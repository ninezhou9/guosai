"""Executable mathematical tests, written independently of earlier Q4 tests."""
import json
import time
import numpy as np
import model as m

def physical(rows):
    r=rows.reshape(-1,len(m.FIELDS)); g,c,b,e,w,E,En,n=r[:,1],r[:,2],r[:,3],r[:,4],r[:,5],r[:,6],r[:,7],r[:,8]
    return dict(balance=float(np.abs(g+e+b-n-c-w).max()),
        recurrence=float(np.abs(En-E-.9*c+b/.9).max()),
        boundary=float(max(0,m.LOW-E.min(),m.LOW-En.min(),E.max()-m.HIGH,En.max()-m.HIGH)),
        power=float(max(0,c.max()-m.RATE,b.max()-m.RATE)),
        nonnegative=float(max(0,-min(g.min(),c.min(),b.min(),e.min(),w.min()))),
        overlap=float(np.minimum(c,b).max()),emergency_charging=float(np.minimum(c,e).max()))

def synthetic(demand,price,mass,transition=None,prior=None):
    h,s,l=demand.shape
    if transition is None: transition=np.full((h-1,s,s),1/s)
    if prior is None: prior=np.full(s,1/s)
    return m.Scenario(0,transition,prior,demand,price,mass,np.zeros(h),np.zeros(h),np.ones(h),
                      np.zeros(h),np.ones(h),True,(0,0),np.zeros((h,s,l),int))

def main():
    started=time.perf_counter(); reports={}
    def check(label,ok,detail):
        reports[label]=dict(passed=bool(ok),detail=detail)
        print(f'{"PASS" if ok else "FAIL"} {label}: {detail}',flush=True)
        if not ok: raise AssertionError(label)
    provenance=m.provenance(); raw=m.load_data(); f=m.features(raw)
    check('input_contract',raw['net'].shape==(365,144) and raw['price'].min()>0,dict(price_min=float(raw['price'].min()),protected_files=len(provenance)))
    # Hand-derived financial and optimal action cases.
    bill=200+m.transact(np.array([100.]),np.array([80.]),np.array([2.]))+m.transact(np.array([80.]),np.array([100.]),np.array([2.]))
    check('round_trip_settlement',abs(bill-240)<1e-10,bill)
    mdl=synthetic(np.array([[[0.,100.]]]),np.array([[[1.,3.]]]),np.array([[[.5,.5]]]))
    grid=np.arange(m.LOW,m.HIGH+1,60.)
    val=m.bellman(np.array([50.]),mdl,grid)[0,0,0]
    check('joint_price_demand',abs(val-375)<1e-9,float(val))
    low,_=m.action(2000,100,.1,-2*grid,grid); high,_=m.action(2000,100,1.,-2*grid,grid)
    check('observed_price_response',abs(low[2]-100)<1e-8 and abs(high[1]-100)<1e-8,dict(low=low.tolist(),high=high.tolist()))
    # Randomized Bellman comparisons against scalar exhaustive knot enumeration.
    rng=np.random.default_rng(20260912)
    n=rng.uniform(-600,1600,(4,3,4)); p=rng.uniform(0,1.7,n.shape); wt=rng.uniform(.1,1,n.shape); wt/=wt.sum(2,keepdims=True)
    trans=rng.uniform(.01,1,(3,3,3)); trans/=trans.sum(2,keepdims=True)
    random=synthetic(n,p,wt,trans); g=rng.uniform(0,800,4)
    fast=m.bellman(g,random,grid); slow=m.bellman(g,random,grid,scalar=True)
    delta=float(np.abs(fast-slow).max())
    check('bellman_all_knots',delta<1e-7,delta)
    actions=[]
    for e in [1200.,2000.3,10799.9,10800.]:
        for gap in [-1500,-2,0,100,1500]:
            a,_=m.action(e,gap,.7,fast[1,1],grid)
            r=np.array([[0,1000,a[0],a[1],a[2],a[3],e,a[4],1000+gap,.7,0]])
            actions.append(max(physical(r).values()))
    check('continuous_boundary_actions',max(actions)<1e-6,max(actions))
    # Constant-price embedded 9-state chain must exactly agree on reachable states.
    joint_trans=np.zeros((3,9,9)); prior=np.zeros(9); prior[[1,4,7]]=1/3
    for i in range(3): joint_trans[:,3*i+1,[1,4,7]]=trans[:,i,:]
    # Unreachable source states receive an arbitrary valid row, but cannot be reached.
    for i in [0,2,3,5,6,8]: joint_trans[:,i,1]=1
    n9=np.repeat(n,3,axis=1); wt9=np.repeat(wt,3,axis=1)
    jmdl=synthetic(n9,np.full_like(n9,.5),wt9,joint_trans,prior)
    small=synthetic(n,np.full_like(n,.5),wt,trans)
    diff=float(np.abs(m.bellman(g,jmdl,grid)[:,[1,4,7]]-m.bellman(g,small,grid)).max())
    check('constant_price_exact_reduction',diff<1e-7,diff)
    for badlen in [0,3,5]:
        try: m.bellman(np.zeros(badlen),random,grid)
        except AssertionError: pass
        else: raise AssertionError('horizon mismatch was not rejected')
    check('horizon_guard',True,'invalid plan lengths rejected')
    jm=m.scenario(f,31,0,'43'); probs=float(np.max(np.abs(jm.transition.sum(2)-1)))
    check('probabilities',probs<1e-12 and abs(jm.prior.sum()-1)<1e-12 and np.allclose(jm.mass.sum(2),1),dict(max_row_error=probs,fallback=jm.fallback))
    # Check actual representative provenance through retained history IDs.
    pts=np.stack([f['zn43'][18:31,0],f['zp'][18:31,0]],axis=-1).reshape(-1,2)
    valid=jm.mass>0; ids=jm.representatives[valid]
    n_back=(jm.demand*6-jm.center[:,None,None])/jm.scale[:,None,None]
    rawp=np.maximum(0,jm.price_center[:,None,None]+jm.price_scale[:,None,None]*pts[np.maximum(jm.representatives,0),1])
    check('paired_representatives',np.allclose(n_back[valid],pts[ids,0]) and np.allclose(jm.price[valid],rawp[valid]),int(valid.sum()))
    flat=np.array([[0.,1.],[0.,1.],[2.,3.]])
    _,mass,_=m.compress(flat,7)
    check('compression_duplicate_mass',np.allclose(mass,[2/3,1/3]),mass.tolist())
    # Rebuild at data ingress: future prices cannot alter historical/zero-hour information.
    changed=raw['price'].copy(); changed[31:]*=2
    ph,sd,zp=m.price_features(changed)
    check('price_causality',np.allclose(ph[:31],f['ph'][:31],equal_nan=True) and np.allclose(ph[31,0],f['ph'][31,0])
          and np.allclose(sd[:32],f['sd'][:32],equal_nan=True) and np.allclose(zp[:31],f['zp'][:31],equal_nan=True),'future-date ingress perturbation')
    tiny=raw['price']*0+.004; ph0,sd0,zp0=m.price_features(tiny)
    ff=dict(f,ph=ph0,sd=sd0,zp=zp0); const=m.scenario(ff,31,0,'43')
    absent=[0,2,3,5,6,8]
    check('constant_price_support',np.max(np.abs(const.transition[:,:,absent]))<1e-12 and np.allclose(const.price[const.mass>0],.004),'no artificial price states or positive-price floor')
    zero=m.scenario(dict(f,ph=ph0*0,sd=sd0,zp=zp0*0),31,0,'43')
    check('zero_price_allowed',np.max(zero.price)==0,0)
    warm=m.warmup(f)
    check('warmup_physics',max(physical(warm).values())<1e-6 and warm[0,0,6]==6000,dict(end=float(warm[-1,-1,7]),**physical(warm)))
    energy=float(warm[-1,-1,7]); cache={}
    full=m.simulate(f,31,energy,cache=cache)
    check('real_day_physics',max(physical(full['rows']).values())<1e-6,physical(full['rows']))
    fixed=m.simulate(f,31,energy,version_mask=7,adjust_mask=0,cache=cache)
    check('update_without_trading',not len(fixed['events']) and np.array_equal(fixed['rows'][:,0],fixed['rows'][:,1]) and fixed['rows'][-1,-1]==3,'4 issue models, same fixed plan')
    frozen=m.simulate(f,31,energy,src='42',version_mask=0,adjust_mask=0)
    check('q42_forecast_family',np.array_equal(frozen['rows'][:,0],frozen['rows'][:,1]) and not np.allclose(frozen['rows'][:,0],full['rows'][:,0]),'Q2 and Q3 forecasts remain separate')
    # Perturb future price/net values and regenerate all affected price features/scenarios.
    r2={k:v.copy() for k,v in raw.items()}; r2['price'][31,36:]*=1.3; r2['net'][31,36:]+=500
    f2=m.features(r2); altered=m.simulate(f2,31,energy)
    e0=full['events'][full['events'][:,0]==1,:6]; e1=altered['events'][altered['events'][:,0]==1,:6]
    check('transaction_before_observation',np.array_equal(full['snapshots'][1],altered['snapshots'][1]) and np.array_equal(e0,e1),'recomputed features + price/net perturbation from slot36')
    r3={k:v.copy() for k,v in raw.items()}; r3['q43'][31,2:,:,72:]+=1000
    later=m.simulate(m.features(r3),31,energy)
    check('unreleased_forecast_causality',np.allclose(full['rows'][:72],later['rows'][:72]),'12h/18h forecast perturbation does not change earlier execution')
    # Physical state is carried to the next day, rather than being reset.
    nxt=m.simulate(f,32,float(full['rows'][-1,7]))
    check('cross_day_state',nxt['rows'][0,6]==full['rows'][-1,7],float(nxt['rows'][0,6]))
    check('protected_inputs',m.provenance()==provenance,'all recorded hashes unchanged')
    out=m.BASE/'tests'; out.mkdir(exist_ok=True)
    payload=dict(passed=len(reports),total=len(reports),checks=reports,elapsed=time.perf_counter()-started)
    (out/'unit_checks.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'All {len(reports)} tests passed; elapsed={payload["elapsed"]:.2f}s')

if __name__=='__main__': main()
