"""Meaningful causality regression: future actuals must not affect earlier decisions."""
import numpy as np
import q2_solution as q

Y,p=q.load()
pred=np.load(q.OUT/'forecasts.npz')['pred']
d=31
A,_=q.simulate(d,6000,Y,p,pred,float(p.mean()),.9,.25)
changed=Y.copy()
changed[:,d,72:]=changed[:,d,72:]*7+1000
changed[:,d+1:]=changed[:,d+1:]*3
B,_=q.simulate(d,6000,changed,p,pred,float(p.mean()),.9,.25)
assert np.max(abs(A[:72]-B[:72]))<q.TOL
assert np.max(abs(A[:,0]-B[:,0]))<q.TOL
f1,_=q.forecast(Y[0],d,1)
f2,_=q.forecast(changed[0],d,1)
assert np.max(abs(f1-f2))<1e-9
q.dump(q.OUT/'无未来泄漏测试.json',{
    'method':'change actuals after noon and all later days; earlier controls and all day-ahead purchases must be unchanged',
    'day':q.date(d),'max_dispatch_difference':float(abs(A[:72]-B[:72]).max()),
    'max_plan_difference':float(abs(A[:,0]-B[:,0]).max()),
    'max_forecast_difference':float(abs(f1-f2).max()),'status':'passed'})
print('CAUSALITY_TEST_PASSED')
