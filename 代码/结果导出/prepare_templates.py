"""Prepare original-template cell payloads from the unchanged saved model runs.

The time interpretation is fixed: input label 00:10 ends 00:00-00:10.
Template times are retained verbatim. Purchase tables therefore shift forward
one interval and use the next calendar day's first model result at their end.
"""
from pathlib import Path
from datetime import datetime, timedelta
import argparse, csv, hashlib, json, sys
import numpy as np
from openpyxl import load_workbook
from openpyxl.utils.datetime import to_excel

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'tmp/result_template_refill_20260913'
Q2=ROOT/'代码/实验/q2_fresh_20260912/results'
Q3=ROOT/'代码/实验/q3_revision_a_20260912/results'
Q4=ROOT/'代码/实验/q4_independent_codex_20260912/results'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(t, end):
    def label(k):
        return '0:00+1' if k==144 else f'{k//6}:{k%6*10:02d}'
    return f'{label(t)}-{label(end)}'


def events(day):
    result=[];t=0
    while t<144:
        if day[t]<=1e-8:
            t+=1;continue
        start=t
        while t<144 and day[t]>1e-8:t+=1
        result.append([interval(start,t),float(day[start:t].sum())])
    return result or [['无',0.]]


def prepare():
    boundary=json.loads((WORK/'boundary_prediction.json').read_text(encoding='utf-8'))
    days=[datetime(2025,2,1)+timedelta(days=i) for i in range(334)]
    base=ROOT/'代码/results/q1'
    with (base/'完整调度.csv').open(encoding='utf-8-sig',newline='') as f:
        q1=list(csv.DictReader(f))
    g1=np.array([float(r['购电_kWh']) for r in q1])
    q1store=[]
    for k in range(6):
        block=q1[k*24:(k+1)*24]
        q1store.append([sum(float(r['充电_kWh']) for r in block),sum(float(r['放电_kWh']) for r in block)])
    # Use the freshly solved next-day plan under the authorized PV extension.
    # Never silently wrap the saved first slot into the next-day position.
    next_q1=boundary.get('q1',{})
    q1_ready=next_q1.get('ready',False)
    q1_tail=next_q1['first_slot_kwh'] if q1_ready else None
    specs=[dict(file='result1.xlsx',ready=q1_ready,kind='single',
                missing_input=None if q1_ready else 'Q1 next-day model plan under an authorized forecast extension',
                plans={'计划购电量':[[float(v)] for v in g1[1:]]+[[q1_tail]]},
                storage=q1store,start=float(q1[0]['期初储电_kWh']),end=float(q1[-1]['期末储电_kWh']))]
    p=np.asarray(boundary['q2_price'])
    main2=np.load(Q2/'main.npy')
    with np.load(Q3/'solutions.npz') as z:
        main3=z['arrays'][7];init3=z['initials'][7];ledger3=z['ledger'];idx=z['day_indices']
    assert np.array_equal(idx,np.arange(31,365))
    with np.load(Q4/'trajectories.npz') as z:
        main42=z['A42'];main43=z['A43_111']
    adj3=init3*p
    for a,d,k,t,old,new,up,down,inc,refund,penalty in ledger3:
        if int(a)==7:adj3[int(d)-31,int(t)]+=inc-refund+penalty
    # Q4 final ordinary cost includes the original incremental revision ledger.
    adj43=main43[:,:,0]*main43[:,:,9]
    with (Q4/'A43_111_ledger.csv').open(encoding='utf-8-sig',newline='') as f:
        ledger43=list(csv.DictReader(f))
    if ledger43:
        print('Q4_LEDGER_FIELDS',list(ledger43[0]))
    data=[('result2.xlsx',main2,{'计划购电量':(main2[:,:,0],main2[:,:,0]*p)},1,2,3,5,6,'q2'),
          ('result3.xlsx',main3,{'计划购电量':(init3,init3*p),'调整购电量':(main3[:,:,0],adj3)},1,2,3,5,6,'q3'),
          ('result4-2.xlsx',main42,{'计划购电量':(main42[:,:,0],main42[:,:,0]*main42[:,:,9])},2,3,4,6,7,'q42')]
    # Each delivery slot's initial cost and original recorded net adjustments.
    for row in ledger43:
        d=(datetime.fromisoformat(row['date'])-days[0]).days
        t=int(row['slot'])
        adj43[d,t]+=float(row['adjustment_net'])
    annual=json.loads((Q4/'annual.json').read_text(encoding='utf-8'))['strategies']['A43_111']
    assert abs(adj43.sum()-annual['initial_cost']-annual['adjustment_net'])<1e-5
    data.append(('result4-3.xlsx',main43,{'计划购电量':(main43[:,:,0],main43[:,:,0]*main43[:,:,9]),'调整购电量':(main43[:,:,1],adj43)},2,3,4,6,7,'q43'))
    for name,a,plans,cidx,didx,eidx,bidx,aidx,tag in data:
        ready=tag in ['q2','q42'] or boundary.get(tag,{}).get('ready',False)
        if tag=='q2':extra_g=boundary['first_slot_kwh'];extra_cost=boundary['first_slot_cost']
        elif tag=='q42':extra_g=boundary['q42']['first_slot_kwh'];extra_cost=boundary['q42']['first_slot_cost_forecast']
        elif ready:extra_g=boundary[tag]['first_slot_kwh'];extra_cost=boundary[tag]['first_slot_cost']
        else:extra_g=extra_cost=None
        matrices={}
        for sheet,(g,cost) in plans.items():
            rows=[]
            for i in range(334):
                tail=float(g[i+1,0]) if i<333 else extra_g
                tailcost=float(cost[i+1,0]) if i<333 else extra_cost
                vals=g[i,1:].tolist()+[tail]
                total=None if tail is None else float(g[i,1:].sum()+tail)
                totalcost=None if tailcost is None else float(cost[i,1:].sum()+tailcost)
                rows.append(vals+[total,totalcost])
            matrices[sheet]=rows
        storage=[];emergency=[];daygroups=[]
        for i,date in enumerate(days):
            serial=to_excel(date)
            for k in range(6):
                storage.append([serial if k==0 else None,
                                f'{k*4}:00-{(k+1)*4}:00',
                                float(a[i,k*24:(k+1)*24,cidx].sum()),
                                float(a[i,k*24:(k+1)*24,didx].sum()),
                                0 if k==0 else ('24:00' if k==1 else None),
                                float(a[i,0,bidx]) if k==0 else (float(a[i,-1,aidx]) if k==1 else None)])
            es=events(a[i,:,eidx]);daygroups.append(len(es))
            for j,(label,amount) in enumerate(es):emergency.append([serial if j==0 else None,label,amount])
        assert abs(sum(x[2] for x in emergency)-a[:,:,eidx].sum())<1e-6
        specs.append(dict(file=name,ready=ready,kind='annual',plans=matrices,storage=storage,
                          emergency=emergency,daygroups=daygroups,
                          missing_input=None if ready else '2026-01-01 00:00 issued 24-hour PV forecast'))
    sources=[ROOT/'基础数据'/s['file'] for s in specs]
    sources += [ROOT/'基础数据/附件1.xlsx',ROOT/'基础数据/附件2.xlsx',ROOT/'基础数据/附件3.xlsx',
                ROOT/'基础数据/附件4.xlsx',base/'完整调度.csv',Q2/'main.npy',Q3/'solutions.npz',Q4/'trajectories.npz',Q4/'A43_111_ledger.csv']
    sources += [ROOT/'代码/q1_solution.py',Q2.parent/'fresh_engine.py',Q2.parent/'run_fresh.py',
                Q3.parent/'q3_engine.py',Q3.parent/'deliver_q3.py',Q4.parent/'model.py',Q4.parent/'deliver.py']
    payload=dict(root=str(ROOT),input_end_labels=True,template_labels_unchanged=True,
                 missing_q3_external_forecast=any(not x['ready'] for x in specs if x['file'] in ['result3.xlsx','result4-3.xlsx']),
                 missing_inputs={x['file']:x['missing_input'] for x in specs if not x['ready']},workbooks=specs,
                 source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources})
    (WORK/'payload.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps({'ready':[s['file'] for s in specs if s['ready']],
                      'waiting':[s['file'] for s in specs if not s['ready']]},ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    prepare()
