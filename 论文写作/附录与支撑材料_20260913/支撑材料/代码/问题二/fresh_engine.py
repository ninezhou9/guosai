"""本次完整重训所用独立模型函数；不读取历史预测缓存或旧运行结果。"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'.deps'))
from datetime import datetime,timedelta
import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
from numpy.lib.stride_tricks import sliding_window_view
import lightgbm as lgb
N=144;DT=1/6;ETA=.9;CAP=5000/6;EMIN=1200.;EMAX=10800.
QUANTILES=np.array([.2,.5,.65,.8,.9]);SEED=20260911
GRID=np.arange(EMIN,EMAX+1,60.);TOL=2e-5;SAMPLES=7;FIT_CALLS=0

def features(y,d):
    """All rows of day d use exclusively days < d, including training rows."""
    assert d>=1
    t=np.arange(N)/N;wd=(datetime(2025,1,1)+timedelta(days=d)).weekday()
    cols=[t,np.sin(2*np.pi*t),np.cos(2*np.pi*t),np.sin(4*np.pi*t),np.cos(4*np.pi*t)]
    cols += [np.full(N,x) for x in [wd,wd>=5,np.sin(2*np.pi*wd/7),np.cos(2*np.pi*wd/7)]]
    ids=[j for j in range(max(0,d-35),d) if (d-j)%7==0]
    if not ids: ids=list(range(max(0,d-7),d))
    for a in y:
        hist=a[max(0,d-7):d]
        cols.extend([a[d-1],a[max(0,d-7)],a[max(0,d-3):d].mean(axis=0),hist.mean(axis=0),hist.std(axis=0),a[ids].mean(axis=0)])
        cols.extend([np.full(N,a[d-1].mean()),np.full(N,hist.mean())])
    return np.array(cols,dtype=np.float64).T

def one_fit(X,Z,x,days,alpha):
    global FIT_CALLS
    FIT_CALLS += 1
    params=dict(objective='quantile',alpha=float(alpha),verbosity=-1,num_threads=2,seed=SEED,
        deterministic=True,force_col_wise=True,num_leaves=15,max_depth=4,learning_rate=.05,
        min_data_in_leaf=48,lambda_l2=5.,feature_fraction=1.,bagging_fraction=1.)
    w=np.repeat(2.**(-(days[-1]-days)/28),N)
    model=lgb.train(params,lgb.Dataset(X,label=Z/1000,weight=w),num_boost_round=120)
    return model.predict(x,num_threads=2)*1000

def forecast_day(y,d,Xall):
    ids=np.arange(max(7,d-56),d)
    X=Xall[ids].reshape(-1,Xall.shape[-1]);x=Xall[d]
    net=y[0]-y[1]
    direct=np.array([one_fit(X,net[ids].ravel(),x,ids,a) for a in QUANTILES])
    separate=np.array([np.maximum(one_fit(X,y[v,ids].ravel(),x,ids,.5),0) for v in range(2)])
    return np.sort(direct,axis=0),separate

def plan_lp(p,net,E0,kappa):
    """Deterministic forecast LP only proposes g; recourse is never executed."""
    H=len(p);dim=5*H+1;g=0;c=H;q=2*H;w=3*H;e=4*H
    obj=np.zeros(dim);obj[:H]=p;obj[-1]=-kappa
    bounds=[(0,None)]*dim
    A=lil_matrix((2*H,dim));rhs=np.r_[net,np.zeros(H)]
    for t in range(H):
        A[t,[g+t,c+t,q+t,w+t]]=[1,-1,1,-1]
        A[H+t,[e+t+1,e+t,c+t,q+t]]=[1,-1,-ETA,1/ETA]
        bounds[c+t]=bounds[q+t]=(0,CAP)
    for t in range(H+1):bounds[e+t]=(EMIN,EMAX)
    bounds[e]=(E0,E0)
    res=linprog(obj,A_eq=A.tocsr(),b_eq=rhs,bounds=bounds,method='highs')
    assert res.success,res.message
    assert abs(A@res.x-rhs).max()<TOL
    return np.maximum(res.x[:H],0)

def grid_value(v,r,p,grid):
    """Exact minimization of the linearly interpolated continuation on a grid.
    Actual actions respect direction; surplus charging is weakly dominant.
    """
    if r<=0:
        end=np.minimum(grid+ETA*min(-r,CAP),EMAX)
        return np.interp(end,grid,v)
    distance=min(r/ETA,CAP/ETA)
    lo=np.maximum(EMIN,grid-distance)
    width=min(len(grid),int(np.floor(distance/(grid[1]-grid[0])+1e-10))+1)
    width=min(width,len(grid))
    x=v+5*p*ETA*grid
    # Window consists of current grid point and preceding width-1 points.
    pad=np.pad(x,(width-1,0),constant_values=np.inf)
    knot_min=sliding_window_view(pad,width).min(axis=1)
    boundary=np.interp(lo,grid,v)+5*p*ETA*lo
    return 5*p*(r-ETA*grid)+np.minimum(knot_min,boundary)

def action(E,r,p,future,grid=GRID):
    if r<=0:
        c=max(0,min(-r,CAP,(EMAX-E)/ETA));return c,0.,0.,max(0,-r-c),E+ETA*c
    lo=max(EMIN,E-min(r,CAP)/ETA)
    knots=grid[(grid>=lo-1e-9)&(grid<=E+1e-9)]
    knots=np.unique(np.r_[lo,E,knots]);knots=np.clip(knots,lo,E)
    costs=5*p*np.maximum(r-ETA*(E-knots),0)+np.interp(knots,grid,future)
    nxt=float(knots[np.argmin(costs)])
    q=max(0,ETA*(E-nxt));e=max(0,r-q)
    return 0.,q,e,0.,nxt

def execute(actual,p,g,E0,m,V,grid=GRID,greedy=False):
    rows=[];E=float(E0)
    for t in range(N):
        net=float(actual[t])*DT;r=net-g[t]
        if greedy:
            if r<=0:
                c=max(0,min(-r,CAP,(EMAX-E)/ETA));q=e=0.;w=max(0,-r-c)
            else:
                q=max(0,min(r,CAP,(E-EMIN)*ETA));c=w=0.;e=max(0,r-q)
            nxt=E+ETA*c-q/ETA
        else:
            s=int(np.digitize((actual[t]-m['center'][t])/m['scale'][t],[-.84,.84]))
            future=V[t+1,s] if t==N-1 else m['P'][t,s]@V[t+1]
            c,q,e,w,nxt=action(E,r,p[t],future,grid)
        rows.append([g[t],c,q,e,w,E,nxt]);E=nxt
    arr=np.asarray(rows);validate(arr,actual,p)
    return arr

def validate(arr,actual,p):
    a=np.asarray(arr);g,c,q,e,w,before,after=a.T
    errs={'balance':float(abs(g+e+q-c-w-actual*DT).max()),
        'state':float(abs(after-before-ETA*c+q/ETA).max()),
        'continuity':float(abs(before[1:]-after[:-1]).max()) if len(a)>1 else 0.,
        'simultaneous':float(np.minimum(c,q).max()),
        'soc':float(max(0,EMIN-before.min(),EMIN-after.min(),before.max()-EMAX,after.max()-EMAX)),
        'power':float(max(0,c.max()-CAP,q.max()-CAP)),
        'nonnegative':float(max(0,-a[:,:5].min())),
        'emergency_charging':float(np.minimum(c,e).max())}
    assert np.isfinite(a).all() and max(errs.values())<TOL,errs
    return errs

def metrics(a,p):
    daily=np.sum(a[:,:,0]*p+5*a[:,:,3]*p,axis=1)
    return {'normal_cost':float(np.sum(a[:,:,0]*p)),'emergency_cost':float(5*np.sum(a[:,:,3]*p)),
        'total_cost':float(daily.sum()),'planned_kWh':float(a[:,:,0].sum()),'emergency_kWh':float(a[:,:,3].sum()),
        'spill_kWh':float(a[:,:,4].sum()),'charge_kWh':float(a[:,:,1].sum()),'discharge_kWh':float(a[:,:,2].sum()),
        'emergency_days':int(np.sum(np.any(a[:,:,3]>TOL,axis=1))),
        'emergency_intervals':int(np.sum(a[:,:,3]>TOL)),'E_start':float(a[0,0,5]),'E_end':float(a[-1,-1,-1]),
        'max_daily_cost':float(daily.max()),'top_5pct_daily_mean':float(np.sort(daily)[-int(np.ceil(.05*len(daily))):].mean())}

def base_markov(y,pred,d):
    """Only preceding dates enter this probability model."""
    ids=np.arange(max(14,d-30),d);assert len(ids)>0
    real=(y[0]-y[1])[ids]
    scale_hist=np.maximum((pred[ids,3]-pred[ids,0])/1.683,100.)
    z=(real-pred[ids,1])/scale_hist
    states=np.digitize(z,[-.84,.84])
    scale=np.maximum((pred[d,3]-pred[d,0])/1.683,100.)
    means=np.empty((N,3));P=np.empty((N-1,3,3))
    count=np.ones((3,3))
    np.add.at(count,(states[:,:-1].ravel(),states[:,1:].ravel()),1)
    global_P=count/count.sum(axis=1,keepdims=True)
    fallback=np.array([-1.4,0.,1.4])
    for t in range(N):
        a=max(0,t-3);b=min(N,t+4);zs=z[:,a:b];ss=states[:,a:b]
        for s in range(3):
            vals=zs[ss==s]
            means[t,s]=(vals.sum()+2*fallback[s])/(len(vals)+2)
        if t<N-1:
            a=max(0,t-3);b=min(N-1,t+4)
            cnt=3*global_P.copy()
            np.add.at(cnt,(states[:,a:b].ravel(),states[:,a+1:b+1].ravel()),1)
            P[t]=cnt/cnt.sum(axis=1,keepdims=True)
    initial=np.bincount(states[:,0],minlength=3)+np.array([.6,1.8,.6])
    initial=initial/initial.sum()
    net=(pred[d,1,:,None]+scale[:,None]*means)*DT
    assert np.isfinite(net).all() and np.allclose(P.sum(axis=2),1)
    return dict(net=net,P=P,initial=initial,scale=scale,center=pred[d,1])

def atomize(values,limit=SAMPLES):
    """Retain both empirical extremes; compress interior into weighted bins.
    Mean preserved, unlike arbitrary normal draws; remaining compression explicit.
    """
    a=np.sort(np.asarray(values,float))
    if len(a)<=limit:return a,np.full(len(a),1/len(a))
    groups=[a[:1],*np.array_split(a[1:-1],limit-2),a[-1:]]
    return np.array([x.mean() for x in groups]),np.array([len(x)/len(a) for x in groups])

def markov(y,pred,d,limit=SAMPLES):
    m=base_markov(y,pred,d)
    ids=np.arange(max(14,d-30),d)
    z=((y[0]-y[1])[ids]-pred[ids,1])/np.maximum((pred[ids,3]-pred[ids,0])/1.683,100.)
    states=np.digitize(z,[-.84,.84])
    samples=np.zeros((N,3,limit));weights=np.zeros_like(samples)
    for t in range(N):
        sl=slice(max(0,t-3),min(N,t+4));zs=z[:,sl];ss=states[:,sl]
        for s in range(3):
            vals=zs[ss==s]
            if len(vals)==0:vals=np.array([[-1.4,0,1.4][s]])
            atoms,w=atomize(vals,limit)
            samples[t,s,:len(w)]=(pred[d,1,t]+m['scale'][t]*atoms)*DT
            weights[t,s,:len(w)]=w
    m['samples']=samples;m['weights']=weights
    # Expected candidate now uses the same empirical conditional means as Bellman.
    m['net']=(samples*weights).sum(axis=2)
    assert np.allclose(weights.sum(axis=2),1)
    return m

def bellman(p,g,m,kappa,grid=GRID):
    H=len(p);V=np.empty((H+1,3,len(grid)));V[H]=-kappa*grid
    for t in range(H-1,-1,-1):
        for s in range(3):
            future=V[t+1,s] if t==H-1 else m['P'][t,s]@V[t+1]
            if 'samples' not in m:
                V[t,s]=grid_value(future,m['net'][t,s]-g[t],p[t],grid)
            else:
                V[t,s]=0.
                for value,w in zip(m['samples'][t,s],m['weights'][t,s]):
                    if w>0:V[t,s]+=w*grid_value(future,value-g[t],p[t],grid)
    assert np.isfinite(V).all() and np.diff(V,axis=2).max()<TOL
    return V


