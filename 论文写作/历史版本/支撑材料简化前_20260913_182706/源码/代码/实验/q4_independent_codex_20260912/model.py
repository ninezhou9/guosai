"""Independent implementation of the approved Q4-A mathematical contract.

No imports from earlier Q4/Q2/Q3 implementations. Only forecast data are reused.
All powers are converted to grid-side kWh at the data boundary.
"""
from pathlib import Path
from dataclasses import dataclass
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import json
import sys
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
DATA = ROOT/'基础数据'
Q2 = BASE.parent/'q2_fresh_20260912/results'
Q3 = BASE.parent/'q3_revision_a_20260912/results'
sys.path.append(str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages'))
import openpyxl

LOW, HIGH, RATE, ETA = 1200.,10800.,5000./6.,.9
PARAMS = dict(dt=1/6, eta=ETA, low=LOW, high=HIGH, rate=RATE,
              grid_step=60, atoms=7, window=30, history_start=18,
              state_cut=.84, scale_floor=.01, terminal=0, tie_tol=1e-8)
FIELDS = ['initial','ordinary','charge','discharge','emergency','spill','before','after','net_kwh','price','issue']

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def date(day):
    return (datetime(2025,1,1)+timedelta(days=int(day))).strftime('%Y-%m-%d')

def interval(t, end=None):
    end = t+1 if end is None else end
    return f'{t//6:02d}:{t%6*10:02d}-{end//6:02d}:{end%6*10:02d}'

def input_paths():
    return [DATA/n for n in ['C题.pdf','附件1.xlsx','附件2.xlsx','附件3.xlsx','附件4.xlsx','result4-2.xlsx','result4-3.xlsx']] + [
        Q2/'fresh_forecasts.npz',Q2/'manifest.json',Q2/'main.npy',
        Q3/'conditional_forecasts.npz',Q3/'manifest.json',Q3/'solutions.npz',Q3/'summary.json',
        Q2/'main_intervals.csv',Q3/'main_intervals.csv',Q3/'revision_ledger.csv']

def provenance():
    m2=json.loads((Q2/'manifest.json').read_text(encoding='utf-8'))
    m3=json.loads((Q3/'manifest.json').read_text(encoding='utf-8'))
    for name,h in m2['raw_inputs'].items():
        assert digest(DATA/name)==h, ('Q2 raw input mismatch',name)
    for folder,manifest,names in [(Q2,m2,['fresh_forecasts.npz','main.npy','main_intervals.csv']),
                                  (Q3,m3,['conditional_forecasts.npz','solutions.npz','main_intervals.csv','revision_ledger.csv'])]:
        for n in names:
            assert digest(folder/n)==manifest['output_hashes'][n], ('upstream output mismatch',n)
    upstream={Path(k).name:v for k,v in m3['signature']['inputs'].items()}
    for n in ['附件2.xlsx','附件3.xlsx']:
        assert digest(DATA/n)==upstream[n], ('Q3 source mismatch',n)
    assert digest(Q2/'fresh_forecasts.npz')==upstream['fresh_forecasts.npz']
    return {str(p.relative_to(ROOT)):digest(p) for p in input_paths()}

def load_data():
    values=[]; labels=None
    for file,sheets in [('附件2.xlsx',['小区负载','光伏发电实际功率']),('附件4.xlsx',['Sheet1'])]:
        wb=openpyxl.load_workbook(DATA/file,read_only=True,data_only=True)
        for sn in sheets:
            rows=list(wb[sn].values)
            assert len(rows)==366 and all(len(r)==145 for r in rows)
            assert [r[0] for r in rows[1:]]==[datetime(2025,1,1)+timedelta(days=d) for d in range(365)]
            if labels is None: labels=rows[0][1:]
            assert rows[0][1:]==labels
            values.append(np.array([r[1:] for r in rows[1:]],float))
        wb.close()
    assert str(labels[0])=='00:10:00' and labels[-1]=='0:00+1'
    assert all(np.isfinite(v).all() for v in values) and (values[2]>0).all()
    with np.load(Q2/'fresh_forecasts.npz') as z: q42=z['pred'].copy()[:,None]
    with np.load(Q3/'conditional_forecasts.npz') as z: q43=z['pred'].copy()
    assert q42.shape==(365,1,5,144) and q43.shape==(365,4,5,144)
    assert np.isfinite(q42[18:]).all()
    for k in range(4): assert np.isfinite(q43[18:,k,:,36*k:]).all()
    return dict(load=values[0],pv=values[1],net=values[0]-values[1],price=values[2],q42=q42,q43=q43)

def price_features(actual):
    """Every cell is produced using only the history available at its issue time."""
    ph=np.full((365,4,144),np.nan); sd=ph.copy()
    for d in range(1,365):
        ph[d,0]=actual[max(0,d-7):d].mean(axis=0)
        for k in range(1,4):
            u=36*k
            bias=(actual[d,u-6:u]-ph[d,0,u-6:u]).mean()
            ph[d,k,u:]=np.maximum(0,ph[d,0,u:]+bias*np.exp(-np.arange(1,145-u)/6))
    residual=actual[:,None,:]-ph
    for d in range(1,365):
        for k in range(4):
            u=36*k
            for t in range(u,144):
                block=residual[max(1,d-30):d,k,max(u,t-3):min(144,t+4)]
                sd[d,k,t]=max(.01,float(np.sqrt(np.mean(block**2)))) if block.size else .01
    return ph,sd,residual/sd

def features(raw):
    ph,sd,zp=price_features(raw['price'])
    result=dict(raw,ph=ph,sd=sd,zp=zp)
    for src in ['42','43']:
        q=raw['q'+src]
        center=q[:,:,1]; scale=np.maximum((q[:,:,3]-q[:,:,0])/1.683,100)
        result['center'+src]=center; result['scale'+src]=scale
        result['zn'+src]=(raw['net'][:,None,:]-center)/scale
    return result

def category(z):
    return np.searchsorted([-.84,.84],z,side='right')

def compress(points,limit):
    """Stable earliest-ID tie order; original point mass is preserved."""
    unique, first, counts=np.unique(points,axis=0,return_index=True,return_counts=True)
    order=np.argsort(first); unique=unique[order]; counts=counts[order]; first=first[order]
    if len(unique)<=limit:
        return unique,counts/counts.sum(),first
    chosen=[]
    for axis in range(points.shape[1]):
        for index in [int(np.argmin(unique[:,axis])),int(np.argmax(unique[:,axis]))]:
            if index not in chosen: chosen.append(index)
    distance=((unique[:,None,:]-unique[chosen][None,:,:])**2).sum(axis=2).min(axis=1)
    while len(chosen)<limit:
        index=int(np.argmax(distance)); chosen.append(index)
        distance=np.minimum(distance,((unique-unique[index])**2).sum(axis=1))
    assignment=((unique[:,None,:]-unique[chosen][None,:,:])**2).sum(axis=2).argmin(axis=1)
    mass=np.bincount(assignment,weights=counts,minlength=len(chosen))
    return unique[chosen],mass/mass.sum(),first[chosen]

@dataclass
class Scenario:
    start:int
    transition:np.ndarray
    prior:np.ndarray
    demand:np.ndarray
    price:np.ndarray
    mass:np.ndarray
    mean_price:np.ndarray
    center:np.ndarray
    scale:np.ndarray
    price_center:np.ndarray
    price_scale:np.ndarray
    joint:bool
    fallback:tuple
    representatives:np.ndarray

def scenario(f,d,k,src,joint=True,atoms=7):
    u=36*k; h=144-u; states=9 if joint else 3
    znet=f['zn'+src][max(18,d-30):d,k,u:]
    zprice=f['zp'][max(18,d-30):d,k,u:]
    cats=category(znet)*3+category(zprice) if joint else category(znet)
    points=np.stack([znet,zprice],axis=-1) if joint else znet[...,None]
    flat=points.reshape(-1,points.shape[-1]); codes=cats.ravel()
    nu=np.bincount(codes,minlength=states)/codes.size
    def counts(a,b):
        return np.bincount((a*states+b).ravel(),minlength=states**2).reshape(states,states)
    allcounts=counts(cats[:,:-1],cats[:,1:])
    allp=(allcounts+nu)/(allcounts.sum(axis=1)[:,None]+1)
    trans=np.empty((h-1,states,states))
    for t in range(h-1):
        lo=max(0,t-3); hi=min(h-1,t+4)
        c=counts(cats[:,lo:hi],cats[:,lo+1:hi+1])
        trans[t]=(c+3*allp)/(c.sum(axis=1)[:,None]+3)
    prior=(np.bincount(cats[:,0],minlength=states)+3*nu)/(len(cats)+3)
    n=np.zeros((h,states,atoms)); p=n.copy(); mass=n.copy(); ids=np.full(n.shape,-1,int)
    fallback_state=fallback_all=0
    for t in range(h):
        lo=max(0,t-3); hi=min(h,t+4)
        local=np.arange(codes.size).reshape(cats.shape)[:,lo:hi].ravel()
        for s in range(states):
            picked=local[codes[local]==s]
            if not len(picked):
                fallback_state+=1; picked=np.flatnonzero(codes==s)
            if not len(picked):
                fallback_all+=1; picked=np.arange(codes.size)
            rep,w,first=compress(flat[picked],atoms); m=len(w)
            n[t,s,:m]=(f['center'+src][d,k,u+t]+f['scale'+src][d,k,u+t]*rep[:,0])/6
            p[t,s,:m]=np.maximum(0,f['ph'][d,k,u+t]+f['sd'][d,k,u+t]*rep[:,1]) if joint else f['ph'][d,k,u+t]
            mass[t,s,:m]=w; ids[t,s,:m]=picked[first]
    prob=prior.copy(); mean=[]
    for t in range(h):
        mean.append(np.sum(prob[:,None]*mass[t]*p[t]))
        if t<h-1: prob=prob@trans[t]
    assert np.allclose(mass.sum(2),1) and np.allclose(trans.sum(2),1)
    return Scenario(u,trans,prior,n,p,mass,np.array(mean),f['center'+src][d,k,u:],
                    f['scale'+src][d,k,u:],f['ph'][d,k,u:],f['sd'][d,k,u:],joint,
                    (fallback_state,fallback_all),ids)

@lru_cache(maxsize=8)
def lp_matrix(h,revision):
    # Interleaved variables per slot: g,c,b,w,E_after[,increase,cancel].
    width=7 if revision else 5
    a=lil_matrix(((3 if revision else 2)*h,h*width))
    bounds=[]
    for t in range(h):
        j=t*width
        a[2*t,j:j+4]=[1,-1,1,-1]
        a[2*t+1,j+1]=-ETA; a[2*t+1,j+2]=1/ETA; a[2*t+1,j+4]=1
        if t: a[2*t+1,j-width+4]=-1
        bounds.extend([(0,None),(0,RATE),(0,RATE),(0,None),(LOW,HIGH)])
        if revision:
            a[2*h+t,j]=1; a[2*h+t,j+5]=-1; a[2*h+t,j+6]=1
            bounds.extend([(0,None),(0,None)])
    return a.tocsr(),bounds,width

def plan(price,net_kwh,energy,old=None):
    h=len(price); revision=old is not None
    a,bounds,width=lp_matrix(h,revision)
    b=np.zeros(a.shape[0]); b[:2*h:2]=net_kwh; b[1]=energy
    c=np.zeros(h*width)
    if revision:
        b[2*h:]=old; c[5::width]=1.5*price; c[6::width]=-.5*price
    else: c[::width]=price
    assert np.isfinite(b).all() and np.isfinite(c).all()
    fit=linprog(c,A_eq=a,b_eq=b,bounds=bounds,method='highs')
    if not fit.success: raise RuntimeError(f'LP status {fit.status}: {fit.message}')
    residual=float(np.abs(a@fit.x-b).max())
    assert residual<1e-6
    return np.maximum(0,fit.x[::width]), dict(status=int(fit.status),residual=residual,objective=float(fit.fun))

def action(energy,gap,price,future,grid):
    """Scalar reference action; continuous energy, endpoints + interior knots."""
    if gap<=0:
        c=min(-gap,RATE,(HIGH-energy)/ETA); en=energy+ETA*c
        return np.array([c,0,0,-gap-c,en]),float(np.interp(en,grid,future))
    lower=max(LOW,energy-min(gap,RATE)/ETA)
    nodes=np.r_[lower,grid[(grid>lower)&(grid<energy)],energy]
    bills=5*price*(gap-ETA*(energy-nodes))+np.interp(nodes,grid,future)
    index=int(np.flatnonzero(bills<=bills.min()+1e-8)[0])
    en=nodes[index]; b=ETA*(energy-en)
    return np.array([0,b,max(0,gap-b),0,en]),float(bills[index])

def interpolate_rows(values,x,grid):
    """values (S,M), x (S,L,M); equally spaced grid."""
    pos=np.clip((x-grid[0])/(grid[1]-grid[0]),0,len(grid)-1)
    ix=np.minimum(pos.astype(int),len(grid)-2); frac=pos-ix
    s=np.arange(len(values))[:,None,None]
    return values[s,ix]*(1-frac)+values[s,ix+1]*frac

def bellman(g,mdl,grid,scalar=False):
    h,s,l=mdl.mass.shape; assert np.asarray(g).shape==(h,)
    w=np.zeros((h+1,s,len(grid)))
    for t in range(h-1,-1,-1):
        future=mdl.transition[t]@w[t+1] if t<h-1 else w[t+1]
        if scalar:
            for state in range(s):
                for j,e in enumerate(grid):
                    w[t,state,j]=sum(mdl.mass[t,state,a]*action(e,mdl.demand[t,state,a]-g[t],
                        mdl.price[t,state,a],future[state],grid)[1] for a in range(l) if mdl.mass[t,state,a]>0)
            continue
        gap=mdl.demand[t]-g[t]; pp=mdl.price[t]; e=grid[None,None,:]
        lower=np.maximum(LOW,e-np.minimum(np.maximum(gap,0),RATE)[:,:,None]/ETA)
        at_lower=interpolate_rows(future,lower,grid)+5*pp[:,:,None]*(gap[:,:,None]-ETA*(e-lower))
        best=5*pp[:,:,None]*gap[:,:,None]+future[:,None,:]
        best=np.minimum(best,at_lower)
        # All internal knots are grid[j-offset]. This shifted reduction avoids M^2 storage.
        reach=np.minimum(np.maximum(gap,0),RATE)/ETA
        for offset in range(1,min(len(grid),int(np.ceil(RATE/ETA/(grid[1]-grid[0])))+1)):
            delta=offset*(grid[1]-grid[0])
            trial=future[:,None,:-offset]+5*pp[:,:,None]*(gap[:,:,None]-ETA*delta)
            valid=reach>=delta
            best[:,:,offset:]=np.minimum(best[:,:,offset:],np.where(valid[:,:,None],trial,np.inf))
        en=np.minimum(HIGH,e+ETA*np.minimum(np.maximum(-gap,0),RATE)[:,:,None])
        surplus=interpolate_rows(future,en,grid)
        costs=np.where((gap<=0)[:,:,None],surplus,best)
        w[t]=np.sum(mdl.mass[t,:,:,None]*costs,axis=1)
    return w

def transact(old,new,p):
    return np.sum(p*(1.5*np.maximum(new-old,0)-.5*np.maximum(old-new,0)))

def simulate(f,day,energy,src='43',joint=True,version_mask=7,adjust_mask=7,grid_step=60,atoms=7,cache=None):
    grid=np.arange(LOW,HIGH+grid_step/2,grid_step)
    models={} if cache is None else cache
    def get(k):
        key=(src,joint,k,atoms)
        if key not in models: models[key]=scenario(f,day,k,src,joint,atoms)
        return models[key]
    original,initial_lp=plan(f['ph'][day,0],f['q'+src][day,0,3]/6,energy)
    current=original.copy(); mdl=get(0); w=bellman(current,mdl,grid)
    rows=np.zeros((144,len(FIELDS))); snapshots=[]; changed=[]; events=[]; scores=[]
    active=0
    for t in range(144):
        if t and t%36==0:
            k=t//36; bit=1<<(k-1)
            if version_mask&bit:
                active=k; mdl=get(k)
            if adjust_mask&bit:
                # In adj-only diagnostics, crop the old model at the current time.
                local=mdl if mdl.start==t else crop(mdl,t)
                old=current[t:].copy(); proposals=[old]; labels=['keep']; infos=[dict(status=0,residual=0,objective=0)]
                for qindex in [1,2,3,4]:
                    proposed,info=plan(f['ph'][day,active,t:],f['q'+src][day,active,qindex,t:]/6,energy,old)
                    if not any(np.max(np.abs(proposed-x))<=1e-8 for x in proposals):
                        proposals.append(proposed); labels.append(str([.2,.5,.65,.8,.9][qindex])); infos.append(info)
                best=np.inf; selected=0; selected_w=None
                for i,p in enumerate(proposals):
                    value=bellman(p,local,grid)
                    score=float(sum(local.prior[s]*np.interp(energy,grid,value[0,s]) for s in range(len(local.prior)))+transact(old,p,local.mean_price))
                    scores.append(dict(issue=k,candidate=labels[i],score=score,**infos[i]))
                    if score<best-1e-8: best=score; selected=i; selected_w=value
                new=proposals[selected]; delta=new-old
                for h in np.flatnonzero(delta!=0):
                    events.append([k,t+int(h),old[h],new[h],max(delta[h],0),max(-delta[h],0),f['ph'][day,active,t+h]])
                current[t:]=new; mdl=local; w=selected_w
            elif version_mask&bit:
                w=bellman(current[t:],mdl,grid)
        if t%36==0:
            snapshots.append(current.copy()); changed.append(bool(t and np.max(np.abs(snapshots[-1]-snapshots[-2]))>1e-8))
        h=t-mdl.start
        # Only here does the controller observe this interval's real price and demand.
        n=f['net'][day,t]/6; p=f['price'][day,t]
        zn=(n*6-mdl.center[h])/mdl.scale[h]; zp=(p-mdl.price_center[h])/mdl.price_scale[h]
        state=int(category(zn)*3+category(zp)) if joint else int(category(zn))
        future=mdl.transition[h,state]@w[h+1] if h<len(mdl.transition) else np.zeros(len(grid))
        control,_=action(energy,n-current[t],p,future,grid)
        c,b,em,spill,en=control
        rows[t]=[original[t],current[t],c,b,em,spill,energy,en,n,p,active]
        energy=en
    events=np.array(events,float).reshape(-1,7)
    return dict(rows=rows,events=events,snapshots=np.array(snapshots),changed=np.array(changed),scores=scores,initial_lp=initial_lp)

def crop(mdl,start):
    """Remaining horizon with prior propagated under the unchanged information model."""
    a=start-mdl.start; prior=mdl.prior.copy()
    for t in range(a): prior=prior@mdl.transition[t]
    return Scenario(start,mdl.transition[a:],prior,mdl.demand[a:],mdl.price[a:],mdl.mass[a:],
        mdl.mean_price[a:],mdl.center[a:],mdl.scale[a:],mdl.price_center[a:],mdl.price_scale[a:],
        mdl.joint,mdl.fallback,mdl.representatives[a:])

def costs(result):
    r=result['rows']; ev=result['events']; p=r[:,9]
    initial=float(p@r[:,0]); emergency=float(5*p@r[:,4])
    inc=refund=penalty=0.
    if len(ev):
        price=p[ev[:,1].astype(int)]
        inc=float(1.5*price@ev[:,4]); refund=float(price@ev[:,5]); penalty=.5*refund
    return dict(initial_cost=initial,increase_cost=inc,refund=refund,penalty=penalty,
        adjustment_net=inc-refund+penalty,emergency_cost=emergency,total_cost=initial+inc-refund+penalty+emergency,
        initial_kwh=float(r[:,0].sum()),effective_kwh=float(r[:,1].sum()),
        increase_kwh=float(ev[:,4].sum()),cancel_kwh=float(ev[:,5].sum()),
        emergency_kwh=float(r[:,4].sum()),charge_kwh=float(r[:,2].sum()),discharge_kwh=float(r[:,3].sum()),
        spill_kwh=float(r[:,5].sum()),E_start=float(r[0,6]),E_end=float(r[-1,7]))

def warmup(f):
    energy=6000.; allrows=[]
    grid=np.array([LOW,HIGH])
    for d in range(31):
        g=np.maximum(f['net'][d-1]/6,0) if d else np.zeros(144)
        for t in range(144):
            n=f['net'][d,t]/6; p=f['price'][d,t]
            ctl,_=action(energy,n-g[t],p,np.zeros(2),grid)
            c,b,em,spill,en=ctl
            allrows.append([g[t],g[t],c,b,em,spill,energy,en,n,p,0]); energy=en
    return np.array(allrows).reshape(31,144,len(FIELDS))
