"""Sequential days, parallel independent strategy groups, atomic day checkpoints."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import argparse
import csv
import json
import time
import platform
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import numpy as np
import scipy
import model as m
from test_model import physical

STRATEGIES={'A42':('42',True,0,0),'B42':('42',False,0,0),'B43':('43',False,7,7),
            **{f'A43_{mask:03b}':('43',True,mask,mask) for mask in range(8)},
            'A43_update_only':('43',True,7,0),'A43_adjust_only':('43',True,0,7)}
GROUPS=[['A42'],['B42'],['B43'],['A43_000','A43_001'],['A43_010','A43_011'],
        ['A43_100','A43_101'],['A43_110'],['A43_111','A43_update_only'],['A43_adjust_only']]

def signature():
    return dict(inputs=m.provenance(),sources={n:m.digest(m.BASE/n) for n in ['model.py','run.py']},
                params=m.PARAMS,strategies={k:list(v) for k,v in STRATEGIES.items()},period=[31,365])

def dump(path,obj):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(temp,path)

def init_worker(cache):
    global FEATURES
    with np.load(cache) as z: FEATURES={k:z[k] for k in z.files}

def worker(task):
    day,names,energies=task; cache={}; out={}
    for name in names:
        src,joint,vm,am=STRATEGIES[name]
        result=m.simulate(FEATURES,day,energies[name],src,joint,vm,am,cache=cache)
        residual=physical(result['rows'])
        assert max(residual.values())<1e-6,(name,day,residual)
        result['daily']=dict(strategy=name,day=day,date=m.date(day),**m.costs(result))
        result['physical']=residual
        out[name]=result
    diag=[]
    for (src,joint,k,atoms),mdl in cache.items():
        diag.append(dict(day=day,source=src,joint=joint,issue=k,atoms=atoms,
                         fallback_state=mdl.fallback[0],fallback_all=mdl.fallback[1]))
    return out,diag

def pack_day(path,results,diagnostics):
    data={}; info={}
    for name,r in results.items():
        for field in ['rows','events','snapshots','changed']: data[name+'__'+field]=r[field]
        info[name]={k:r[k] for k in ['daily','physical','scores','initial_lp']}
    data['metadata']=np.array(json.dumps(dict(strategies=info,diagnostics=diagnostics)))
    temp=path.with_suffix('.tmp')
    with temp.open('wb') as f: np.savez_compressed(f,**data)
    os.replace(temp,path)

def csv_write(path,rows):
    rows=list(rows)
    if not rows: return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def collect(out,end):
    daily=[]; scores=[]; diag={}; trajectories={n:[] for n in STRATEGIES}; all_ev={n:[] for n in STRATEGIES}
    snapshots={n:[] for n in STRATEGIES}; maxphys={n:{} for n in STRATEGIES}
    for d in range(31,end):
        with np.load(out/'days'/f'{d:03d}.npz') as z:
            meta=json.loads(str(z['metadata']))
            for r in meta['diagnostics']: diag[(d,r['source'],r['joint'],r['issue'])]=r
            for name in STRATEGIES:
                data=meta['strategies'][name]; daily.append(data['daily'])
                scores.append(dict(strategy=name,day=d,issue=0,candidate='initial',score=None,**data['initial_lp']))
                scores.extend(dict(strategy=name,day=d,**r) for r in data['scores'])
                for k,v in data['physical'].items(): maxphys[name][k]=max(v,maxphys[name].get(k,0))
                trajectories[name].append(z[name+'__rows']); snapshots[name].append(z[name+'__snapshots'])
                ev=z[name+'__events']
                all_ev[name].append(np.column_stack([np.full(len(ev),d),ev]))
    arrays={n:np.array(v) for n,v in trajectories.items()}
    np.savez_compressed(out/'trajectories.npz',**arrays)
    np.savez_compressed(out/'plan_snapshots.npz',**{n:np.array(v) for n,v in snapshots.items()})
    np.savez_compressed(out/'transactions.npz',**{n:np.concatenate(v) for n,v in all_ev.items()})
    csv_write(out/'daily_costs.csv',daily); csv_write(out/'candidate_scores.csv',scores)
    csv_write(out/'scenario_diagnostics.csv',diag.values())
    annual={}
    for name in STRATEGIES:
        rows=[r for r in daily if r['strategy']==name]
        annual[name]={k:sum(r[k] for r in rows) for k in rows[0] if k not in ['strategy','day','date','E_start','E_end']}
        annual[name].update(E_start=rows[0]['E_start'],E_end=rows[-1]['E_end'],emergency_days=sum(r['emergency_kwh']>1e-8 for r in rows))
        r=arrays[name]
        assert np.array_equal(r[1:,0,6],r[:-1,-1,7])
    dump(out/'annual.json',dict(days=end-31,strategies=annual,physical=maxphys,columns=m.FIELDS))
    for name in ['A42','A43_111']:
        a=arrays[name]; rows=[]; ledger=[]
        for dd,rday in enumerate(a):
            for t,row in enumerate(rday):
                rows.append(dict(date=m.date(dd+31),slot=t,interval=m.interval(t),**dict(zip(m.FIELDS,map(float,row))),net_kw=float(row[8]*6)))
        for d,k,t,old,new,inc,cancel,forecast in np.concatenate(all_ev[name]):
            price=arrays[name][int(d)-31,int(t),9]
            ledger.append(dict(date=m.date(d),issue_hour=int(k)*6,slot=int(t),old=old,new=new,increase=inc,cancel=cancel,
                               forecast_price=forecast,actual_price=price,increase_cost=1.5*price*inc,refund=price*cancel,
                               penalty=.5*price*cancel,adjustment_net=price*(1.5*inc-.5*cancel)))
        csv_write(out/f'{name}_intervals.csv',rows); csv_write(out/f'{name}_ledger.csv',ledger)
    return annual

def static_repricing(out,price):
    results=[]
    for src in ['2','3']:
        folder=m.Q2 if src=='2' else m.Q3
        with (folder/'main_intervals.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
        p=price[31:].ravel(); assert len(rows)==334*144
        g=np.array([float(r['g_kwh' if src=='2' else 'initial_kwh']) for r in rows])
        em=np.array([float(r['emergency_kwh']) for r in rows]); adj=0.
        for i,r in enumerate(rows):
            assert r['date']==m.date(31+i//144) and int(r['slot'])==i%144+1
            ordinary=float(r['g_kwh' if src=='2' else 'effective_kwh'])
            balance=ordinary+float(r['emergency_kwh'])+float(r['discharge_kwh'])-float(r['net_kwh'])-float(r['charge_kwh'])-float(r['waste_kwh' if src=='2' else 'spill_kwh'])
            assert abs(balance)<1e-6
        if src=='3':
            with (folder/'revision_ledger.csv').open(encoding='utf-8-sig') as f:
                for r in csv.DictReader(f):
                    if r['policy']!='mask_111': continue
                    d=(datetime.fromisoformat(r['date'])-datetime(2025,1,1)).days
                    adj+=price[d,int(r['slot'])-1]*(1.5*float(r['increase_kwh'])-.5*float(r['cancel_kwh']))
        results.append(dict(strategy='static_Q'+src,initial_cost=float(p@g),adjustment_net=adj,
                            emergency_cost=float(5*p@em),total_cost=float(p@g+adj+5*p@em),
                            E_end=float(rows[-1]['end_kwh'])))
    csv_write(out/'static_repricing.csv',results)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--resume',action='store_true')
    parser.add_argument('--days',type=int,default=334); parser.add_argument('--jobs',type=int,default=9)
    parser.add_argument('--output',default='results'); args=parser.parse_args()
    assert 1<=args.days<=334 and 1<=args.jobs<=16
    out=(m.BASE/args.output).resolve(); assert out.is_relative_to(m.BASE)
    start=time.perf_counter(); sign=signature(); begin=31
    if args.resume:
        assert json.loads((out/'signature.json').read_text(encoding='utf-8'))==sign,'signature mismatch'
        state=json.loads((out/'checkpoint.json').read_text(encoding='utf-8')); begin=state['next_day']; energies=state['energies']
        assert 31<=begin<=365 and set(energies)==set(STRATEGIES)
        assert all(m.LOW-1e-6<=v<=m.HIGH+1e-6 for v in energies.values())
        for d in range(31,begin):
            path=out/'days'/f'{d:03d}.npz'; assert m.digest(path)==state['day_hashes'][str(d)]
        if begin>31:
            with np.load(out/'days'/f'{begin-1:03d}.npz') as z:
                assert all(energies[n]==float(z[n+'__rows'][-1,7]) for n in STRATEGIES)
        # A complete day written just before a checkpoint interruption may exist; never overwrite silently.
        assert not (out/'days'/f'{begin:03d}.npz').exists(),'orphan day: inspect before recovery'
        init_worker(out/'features.npz')
    else:
        if out.exists() and any(out.iterdir()): raise RuntimeError('output not empty: choose a new directory or --resume')
        out.mkdir(parents=True,exist_ok=True); (out/'days').mkdir()
        f=m.features(m.load_data()); np.savez_compressed(out/'features.npz',**f)
        warm=m.warmup(f); np.save(out/'warmup.npy',warm)
        energies={n:float(warm[-1,-1,7]) for n in STRATEGIES}
        state=dict(next_day=31,energies=energies,day_hashes={})
        dump(out/'signature.json',sign); dump(out/'checkpoint.json',state)
        init_worker(out/'features.npz')
    end=31+args.days; assert begin<=end
    started=datetime.now().isoformat()
    print(f'Independent run: {len(STRATEGIES)} strategies, days {begin}..{end-1}, workers={args.jobs}',flush=True)
    with ProcessPoolExecutor(max_workers=args.jobs,initializer=init_worker,initargs=(out/'features.npz',)) as pool:
        for d in range(begin,end):
            futures=[pool.submit(worker,(d,g,energies)) for g in GROUPS]; results={}; diag=[]
            for future in futures:
                r,extra=future.result(); results.update(r); diag.extend(extra)
            pack_day(out/'days'/f'{d:03d}.npz',results,diag)
            energies={n:float(r['rows'][-1,7]) for n,r in results.items()}
            state.update(next_day=d+1,energies=energies); state['day_hashes'][str(d)]=m.digest(out/'days'/f'{d:03d}.npz')
            dump(out/'checkpoint.json',state)
            if (d-begin)%10==0 or d==end-1:
                elapsed=time.perf_counter()-start
                print(f'{m.date(d)} {d-30}/{args.days} elapsed={elapsed:.1f}s',flush=True)
    annual=collect(out,end)
    if end==365: static_repricing(out,FEATURES['price'])
    dump(out/'run_record.json',dict(started=started,ended=datetime.now().isoformat(),elapsed=time.perf_counter()-start,
        command=os.sys.argv,exit_code=0,python=os.sys.version,numpy=np.__version__,scipy=scipy.__version__,
        platform=platform.platform(),resumed=args.resume,days_computed=end-begin,random_seed=None,model_fits=0))
    assert m.provenance()==sign['inputs'],'protected inputs changed'
    for n,r in annual.items(): print(f'{n}: {r["total_cost"]:,.2f} yuan; emergency={r["emergency_kwh"]:,.2f} kWh',flush=True)

if __name__=='__main__': main()
