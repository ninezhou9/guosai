"""Physical, settlement, interpolation, DP equivalence and information tests."""
import time
import numpy as np
import q3_engine as m


def checks(y,p,load_pred,f,pred):
    # Paid cancellation and repurchase must not disappear when final volume matches.
    old=np.array([100.]);down=np.array([80.]);price=np.array([1.])
    assert m.revision_cost(down,old,price)==-10.
    assert 100+m.revision_cost(down,old,price)+m.revision_cost(old,down,price)==120.
    assert m.revision_cost(old,old,price)==0.
    # Compare all value-grid entries to the existing scalar DP, including surplus.
    rng=np.random.default_rng(20260912);H=9
    samples=rng.uniform(-400,1500,(H,3,7));weights=rng.uniform(.1,1,(H,3,7));weights/=weights.sum(axis=2,keepdims=True)
    P=rng.uniform(.1,1,(H-1,3,3));P/=P.sum(axis=2,keepdims=True)
    model=dict(samples=samples,weights=weights,P=P)
    plans=rng.uniform(0,1200,(4,H));price=rng.uniform(.3,1.5,H)
    values=m.bellman_batch(price,plans,model)
    error=0.
    for g,v in zip(plans,values):
        expected=m.b.bellman(price,g,model,0.)
        error=max(error,float(np.max(np.abs(v-expected))))
    assert error<1e-7,error
    toy=dict(samples=np.tile([0.,100.],(1,3,1)),weights=np.full((1,3,2),.5),P=np.empty((0,3,3)))
    assert abs(m.bellman_batch(np.array([1.]),np.array([50.]),toy)[0,0,0,0]-125)<1e-8
    # Actual forecast point +1 h must land at 07:00 for the 06:00 issue.
    pv=m.pv_interpolate(y,f)
    np.testing.assert_allclose(pv[:,1,41],f[:,1,0])
    np.testing.assert_allclose(pv[:,0,5],f[:,0,0])
    # LP settlement independent recomputation already inside revision_lp.
    g=m.revision_lp(np.ones(2),np.array([50.,50.]),1200.,np.array([100.,100.]))
    assert np.all(g>=0)
    d=31;models=[m.model_day(y,pred,d,k) for k in range(4)]
    warm=m.warmup(y,p);E=warm[-1,-1,6]
    t0=time.perf_counter();run=m.day_run(y,p,pred,models,d,E,return_scores=True)
    seconds=time.perf_counter()-t0
    # Mutation at and after 06:00 cannot affect the 06:00 purchase revision.
    changed=y.copy();changed[:,d,36:]+=np.array([10000.,3000.])[:,None]
    cp,_=m.conditional_forecasts(changed,load_pred,f)
    np.testing.assert_array_equal(cp[:d],pred[:d])
    for k in [0,1]:np.testing.assert_array_equal(cp[d,k],pred[d,k])
    cm=[m.model_day(changed,cp,d,k) for k in range(4)]
    for k in [0,1]:
        for key in models[k]:np.testing.assert_array_equal(models[k][key],cm[k][key])
    cr=m.day_run(changed,p,cp,cm,d,E,return_scores=True)
    np.testing.assert_array_equal(run['initial'],cr['initial'])
    np.testing.assert_array_equal(run['arr'][:36],cr['arr'][:36])
    np.testing.assert_array_equal(run['ledger'][run['ledger'][:,0]==1],cr['ledger'][cr['ledger'][:,0]==1])
    # Later published forecasts cannot change earlier actions or purchase revisions.
    ff=f.copy();ff[d,2:]+=2000
    pp,_=m.conditional_forecasts(y,load_pred,ff)
    mm=[m.model_day(y,pp,d,k) for k in range(4)]
    rr=m.day_run(y,p,pp,mm,d,E)
    np.testing.assert_array_equal(run['arr'][:72],rr['arr'][:72])
    np.testing.assert_array_equal(run['ledger'][run['ledger'][:,0]==1],rr['ledger'][rr['ledger'][:,0]==1])
    # Existing no-update policy must reduce exactly to fixed-plan feedback execution.
    no=m.day_run(y,p,pred,models,d,E,mask=0)
    vv=m.b.bellman(p,no['initial'],models[0],0.)
    aa=m.b.execute((y[0]-y[1])[d],p,no['initial'],E,models[0],vv)
    np.testing.assert_allclose(no['arr'],aa,atol=1e-7,rtol=0)
    return dict(scalar_bellman_max_error=error,expected_shortfall_counterexample=125.,
                successive_transaction_cost=120.,hourly_alignment=True,
                current_and_future_actual_no_plan_leak=True,later_issue_no_early_leak=True,
                fixed_plan_equivalence=True,smoke_day=m.summary_day(run,p),full_update_day_seconds=seconds)


if __name__=='__main__':
    import json
    y,p,load,f=m.load_inputs();pred,pv=m.conditional_forecasts(y,load,f)
    print(json.dumps(checks(y,p,load,f,pred),ensure_ascii=False,indent=2))
