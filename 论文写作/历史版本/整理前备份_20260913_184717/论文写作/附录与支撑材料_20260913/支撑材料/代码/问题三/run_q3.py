"""Run the approved Q3 A model, preserving all earlier Q1/Q2 files."""
from pathlib import Path
import argparse
import json
import sys
import time
import csv
from datetime import datetime
import numpy as np
import q3_engine as m
from check_engine import checks

POLICIES=['mask_000','mask_001','mask_010','mask_011','mask_100','mask_101','mask_110','mask_111','forecast_only']


def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=m.BASE/'results')
    ap.add_argument('--end-day',type=int,default=365,help='Exclusive day index, 365 means the full year')
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args();out=args.output.resolve()
    assert out.is_relative_to(m.ROOT) and 32<=args.end_day<=365
    if out.exists() and any(out.iterdir()) and not args.resume:raise RuntimeError('Output exists; use a new directory or --resume for the same source')
    out.mkdir(parents=True,exist_ok=True)
    sources={str(m.BASE/n):m.sha(m.BASE/n) for n in ['q3_engine.py','check_engine.py','run_q3.py']}
    protected=[m.ROOT/'基础数据'/n for n in ['C题.pdf','附件1.xlsx','附件2.xlsx','附件3.xlsx','result3.xlsx']]
    protected += [m.Q2/n for n in ['fresh_engine.py','run_fresh.py','results/fresh_forecasts.npz','results/manifest.json','results/result2.xlsx','results/main.npy']]
    input_hashes={str(p):m.sha(p) for p in protected}
    signature=dict(sources=sources,inputs=input_hashes,end_day=args.end_day,policies=POLICIES,
                   settlement='incremental revisions; refund old base price plus 50% penalty; 150% upward price',
                   dp_terminal=0,grid_kwh=60,atoms=7,quantiles=m.QUANTILES.tolist(),
                   load_forecast='read-only hash-verified Q2 fresh_forecasts separate[:,0]',
                   reference_Q2_source_hash_rule='exact bytes or exact CRLF-to-LF normalization')
    start_time=time.perf_counter()
    if args.resume:
        assert json.loads((out/'signature.json').read_text(encoding='utf-8'))==signature,'Resume source/input mismatch'
    else:dump(out/'signature.json',signature)
    print(datetime.now().isoformat(timespec='seconds'),'loading and conditioning forecasts',flush=True)
    y,p,load,f=m.load_inputs();pred,pv=m.conditional_forecasts(y,load,f);warm=m.warmup(y,p)
    if not args.resume:
        result=checks(y,p,load,f,pred);dump(out/'engine_checks.json',result)
        np.savez_compressed(out/'conditional_forecasts.npz',pred=pred,pv=pv,load=load)
        np.save(out/'january_warmup.npy',warm)
    D=args.end_day-31
    arrays=np.zeros((9,D,144,7));initials=np.zeros((9,D,144));E=np.full(9,warm[-1,-1,6]);ledger=[];scores=[];daily=[];first=31
    if args.resume:
        with np.load(out/'checkpoint.npz') as z:
            arrays[:]=z['arrays'];initials[:]=z['initials'];E[:]=z['states'];first=int(z['next_day'])
            ledger=z['ledger'].tolist()
        daily=json.loads((out/'daily_checkpoint.json').read_text(encoding='utf-8'))
        scores=json.loads((out/'scores_checkpoint.json').read_text(encoding='utf-8'))
    for d in range(first,args.end_day):
        models=[m.model_day(y,pred,d,k) for k in range(4)]
        for a,name in enumerate(POLICIES):
            run=m.day_run(y,p,pred,models,d,E[a],mask=min(a,7),update_only=a==8,return_scores=a==7)
            arrays[a,d-31]=run['arr'];initials[a,d-31]=run['initial'];E[a]=run['arr'][-1,6]
            ledger.extend([[a,d,*r] for r in run['ledger'].tolist()])
            scores.extend([[d,*r] for r in run['scores']])
            daily.append(dict(policy=name,date=m.date(d),**m.summary_day(run,p)))
        if (d-31)%15==0 or d==args.end_day-1:
            print(datetime.now().isoformat(timespec='seconds'),m.date(d),'main cumulative',round(sum(r['total_cost'] for r in daily if r['policy']=='mask_111'),2),'elapsed',round(time.perf_counter()-start_time,1),flush=True)
        if (d-30)%30==0 or d==args.end_day-1:
            np.savez(out/'checkpoint.npz',arrays=arrays,initials=initials,states=E,next_day=d+1,ledger=np.asarray(ledger,float).reshape(-1,11))
            dump(out/'daily_checkpoint.json',daily);dump(out/'scores_checkpoint.json',scores)
    physical={name:m.b.validate(arrays[a].reshape(-1,7),(y[0]-y[1])[31:args.end_day].ravel(),np.tile(p,D)) for a,name in enumerate(POLICIES)}
    summary={}
    for a,name in enumerate(POLICIES):
        rr=[r for r in daily if r['policy']==name]
        summ={key:float(sum(r[key] for r in rr)) for key in rr[0] if key not in ['policy','date','start_kwh','end_kwh']}
        summ.update(start_kwh=float(arrays[a,0,0,5]),end_kwh=float(E[a]),emergency_days=int(np.sum(np.any(arrays[a,:,:,3]>TOL,axis=1))),
                    emergency_intervals=int(np.sum(arrays[a,:,:,3]>TOL)),days=D)
        assert abs(summ['initial_kwh']+summ['increase_kwh']-summ['cancel_kwh']-summ['effective_kwh'])<1e-5
        summary[name]=summ
    for path,digest in input_hashes.items():assert m.sha(path)==digest,'Input modified: '+path
    np.savez_compressed(out/'solutions.npz',arrays=arrays,initials=initials,ledger=np.asarray(ledger,float).reshape(-1,11),price=p,day_indices=np.arange(31,args.end_day))
    with (out/'daily_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(daily[0]));writer.writeheader();writer.writerows(daily)
    dump(out/'summary.json',summary)
    with (out/'candidate_scores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['day_index','issue_index','candidate_quantile','revision_net_cost','expected_emergency_cost','planning_score','chosen']);w.writerows(scores)
    metrics={}
    for k in range(4):
        sl=slice(k*36,144);actual=(y[0]-y[1])[31:args.end_day,sl]
        error=actual-pred[31:args.end_day,k,1,sl]
        metrics[str(k*6)]=dict(MAE_kW=float(abs(error).mean()),RMSE_kW=float(np.sqrt((error**2).mean())),
                             q80_coverage=float(np.mean(actual<=pred[31:args.end_day,k,3,sl])))
    dump(out/'forecast_metrics.json',metrics)
    manifest=dict(status='computed_pending_delivery_checks_and_user_review',created=datetime.now().isoformat(),
                  python=sys.version,numpy=np.__version__,scipy=m.b.scipy.__version__,lightgbm=m.b.lgb.__version__,openpyxl=m.openpyxl.__version__,
                  elapsed_seconds=time.perf_counter()-start_time,signature=signature,physical_checks=physical,
                  reused_Q2_forecast_files=1,new_forecast_model_fits=0,new_Q3_dispatch=True,protected_files_unchanged=True,
                  command=[sys.executable,str(Path(__file__).relative_to(m.ROOT)),*sys.argv[1:]],
                  output_hashes={p.name:m.sha(p) for p in out.iterdir() if p.is_file() and p.name not in ['manifest.json','checkpoint.npz','daily_checkpoint.json','scores_checkpoint.json']})
    dump(out/'manifest.json',manifest)
    print('COMPLETE',json.dumps(summary,ensure_ascii=False),flush=True)


TOL=m.TOL
if __name__=='__main__':main()
