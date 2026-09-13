"""Independent accounting/physics/Excel verification, no solver or cost function calls."""
from pathlib import Path
from datetime import datetime,timedelta
import csv
import hashlib
import json
import sys
import numpy as np
BASE=Path(__file__).resolve().parent; ROOT=BASE.parents[2]; OUT=BASE/'results'; DATA=ROOT/'基础数据'
sys.path.append(str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages'))
import openpyxl

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def style(cell):
    # openpyxl serializes an untouched blank cell as None and a populated
    # default cell as nine zero style indices. These are visually identical.
    return tuple(cell._style) if cell._style is not None else (0,)*9

def main():
    records={}
    def check(name,ok,detail):
        records[name]=dict(passed=bool(ok),detail=detail)
        print(f'{"PASS" if ok else "FAIL"} {name}: {detail}',flush=True)
    raw=[]
    for name,sheets in [('附件2.xlsx',['小区负载','光伏发电实际功率']),('附件4.xlsx',['Sheet1'])]:
        wb=openpyxl.load_workbook(DATA/name,read_only=True,data_only=True)
        for sn in sheets: raw.append(np.array([r[1:] for r in list(wb[sn].values)[1:]],float))
        wb.close()
    net=(raw[0]-raw[1])/6; prices=raw[2]
    annual=json.loads((OUT/'annual.json').read_text(encoding='utf-8'))['strategies']
    with np.load(OUT/'trajectories.npz') as z: paths={n:z[n] for n in z.files}
    with np.load(OUT/'transactions.npz') as z: tx={n:z[n] for n in z.files}
    with np.load(OUT/'plan_snapshots.npz') as z: snaps={n:z[n] for n in z.files}
    daily={}
    with (OUT/'daily_costs.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            key=(r['strategy'],int(r['day'])); assert key not in daily; daily[key]=r
    warm=np.load(OUT/'warmup.npy')
    check('warmup_chain',warm.shape==(31,144,11) and warm[0,0,6]==6000 and np.array_equal(warm.reshape(-1,11)[1:,6],warm.reshape(-1,11)[:-1,7]),float(warm[-1,-1,7]))
    for name,r in paths.items():
        check(name+'_shape_data',r.shape==(334,144,11) and np.allclose(r[:,:,8],net[31:],atol=1e-10,rtol=0) and np.array_equal(r[:,:,9],prices[31:]),list(r.shape))
        balance=float(np.max(np.abs(r[:,:,1]+r[:,:,4]+r[:,:,3]-net[31:]-r[:,:,2]-r[:,:,5])))
        state=float(np.max(np.abs(r[:,:,7]-r[:,:,6]-.9*r[:,:,2]+r[:,:,3]/.9)))
        check(name+'_physical',max(balance,state)<1e-6,dict(balance=balance,state=state))
        boundary=max(0,1200-r[:,:,6:8].min(),r[:,:,6:8].max()-10800,r[:,:,2:4].max()-5000/6,-r[:,:,:6].min())
        overlap=max(float(np.minimum(r[:,:,2],r[:,:,3]).max()),float(np.minimum(r[:,:,2],r[:,:,4]).max()))
        check(name+'_limits',boundary<1e-6 and overlap<1e-6,dict(boundary=float(boundary),overlap=overlap))
        flat=r.reshape(-1,11)
        check(name+'_continuity',r[0,0,6]==warm[-1,-1,7] and np.array_equal(flat[1:,6],flat[:-1,7]),float(r[0,0,6]))
        transactions=tx[name]; replay=r[:,:,0].copy(); extra=np.zeros(334); last=(-1,-1,-1); valid=True
        dailyextra=np.zeros((334,3))
        for d,k,t,old,new,inc,cancel,pred in transactions:
            d,k,t=int(d),int(k),int(t); i=d-31
            valid &= (d,k,t)>=last and 1<=k<=3 and 36*k<=t<144 and abs(old-replay[i,t])<1e-8
            valid &= abs(inc-max(new-old,0))<1e-10 and abs(cancel-max(old-new,0))<1e-10
            replay[i,t]=new; p=prices[d,t]
            dailyextra[i]+=[1.5*p*inc,p*cancel,.5*p*cancel]; extra[i]+=p*(1.5*inc-.5*cancel); last=(d,k,t)
        check(name+'_transaction_replay',valid and np.max(np.abs(replay-r[:,:,1]))<1e-8,int(len(transactions)))
        ini=(r[:,:,0]*prices[31:]).sum(1); emergency=(r[:,:,4]*prices[31:]*5).sum(1)
        calculated=ini+extra+emergency; exported=np.array([float(daily[name,d]['total_cost']) for d in range(31,365)])
        err=max(float(np.max(np.abs(calculated-exported))),abs(float(calculated.sum())-annual[name]['total_cost']))
        check(name+'_accounting',err<1e-5,dict(total=float(calculated.sum()),max_error=err))
        spliterr=0.
        for i,d in enumerate(range(31,365)):
            for key,v in zip(['initial_cost','increase_cost','refund','penalty','emergency_cost'],[ini[i],*dailyextra[i],emergency[i]]):
                spliterr=max(spliterr,abs(v-float(daily[name,d][key])))
        check(name+'_bill_components',spliterr<1e-5,spliterr)
        # Reconstruct every published snapshot, including inactive update times.
        snapshot_ok=True
        for i,d in enumerate(range(31,365)):
            current=r[i,:,0].copy()
            for k in range(4):
                for ev in transactions[(transactions[:,0]==d)&(transactions[:,1]==k)]: current[int(ev[2])]=ev[4]
                snapshot_ok &= np.array_equal(current,snaps[name][i,k])
        check(name+'_snapshots',snapshot_ok,'four snapshots per day replayed')
        if name in ['A42','B42','A43_000','A43_update_only']:
            check(name+'_frozen',len(transactions)==0 and np.array_equal(r[:,:,0],r[:,:,1]),'ordinary plan fixed')
    # LP outcomes are checked independently from candidate output.
    with (OUT/'candidate_scores.csv').open(encoding='utf-8-sig') as f: candidates=list(csv.DictReader(f))
    check('lp_status',all(int(r['status'])==0 and float(r['residual'])<1e-6 for r in candidates),len(candidates))
    for tag,name in [('2','A42'),('3','A43_111')]:
        wb=openpyxl.load_workbook(OUT/f'result4-{tag}.xlsx',data_only=True)
        tpl=openpyxl.load_workbook(DATA/f'result4-{tag}.xlsx',data_only=True); r=paths[name]
        ok=wb.sheetnames==tpl.sheetnames; err=0.; style_errors=0
        for sn,col in [('计划购电量',0),('调整购电量',1)]:
            if sn not in wb.sheetnames: continue
            ws=wb[sn]; ts=tpl[sn]
            ok &= ws.max_row==335 and ws.max_column==147
            ok &= ws.cell(1,2).value=='00:00-00:10' and ws.cell(1,145).value=='23:50-24:00'
            for i in range(334):
                ok &= ws.cell(i+2,1).value==datetime(2025,2,1)+timedelta(days=i)
                got=np.array([ws.cell(i+2,c).value for c in range(2,146)],float)
                err=max(err,float(np.max(np.abs(got-r[i,:,col]))),abs(ws.cell(i+2,146).value-r[i,:,col].sum()))
                dc=daily[name,i+31]; expected=float(dc['initial_cost'])+(float(dc['adjustment_net']) if col else 0)
                err=max(err,abs(ws.cell(i+2,147).value-expected))
                for c in range(1,148): style_errors+=int(style(ws.cell(i+2,c))!=style(ts.cell(i+2,c)))
                style_errors+=int(ws.row_dimensions[i+2].height!=ts.row_dimensions[i+2].height)
        ws=wb['充放电量']; ts=tpl['充放电量']; ok &= ws.max_row==2005
        for i in range(334):
            for b in range(6):
                row=2+i*6+b; err=max(err,abs(ws.cell(row,3).value-r[i,b*24:(b+1)*24,2].sum()),abs(ws.cell(row,4).value-r[i,b*24:(b+1)*24,3].sum()))
                for c in range(1,7): style_errors+=int(style(ws.cell(row,c))!=style(ts.cell(b+2,c)))
                style_errors+=int(ws.row_dimensions[row].height!=ts.row_dimensions[b+2].height)
            err=max(err,abs(ws.cell(2+i*6,6).value-r[i,0,6]),abs(ws.cell(3+i*6,6).value-r[i,-1,7]))
        ws=wb['紧急购电量']; ts=tpl['紧急购电量']; seen={}; current=None; printed=0.
        for cells in list(ws.values)[1:]:
            if cells[0] is not None: current=cells[0].strftime('%Y-%m-%d'); seen[current]=[]
            seen[current].append(cells[1:]); printed+=float(cells[2])
        row=2
        for block in seen.values():
            for j in range(len(block)):
                pattern=0 if j==0 else 2 if j==len(block)-1 else 1
                for c in range(1,4): style_errors+=int(style(ws.cell(row,c))!=style(ts.cell(pattern+2,c)))
                style_errors+=int(ws.row_dimensions[row].height!=ts.row_dimensions[pattern+2].height)
                row+=1
        ok &= len(seen)==334
        for i in range(334):
            ds=(datetime(2025,2,1)+timedelta(days=i)).strftime('%Y-%m-%d'); reconstructed=np.zeros(144)
            for period,q in seen[ds]:
                if period=='无': ok &= abs(q)<1e-8; continue
                a,b=period.split('-'); aa=sum(x*y for x,y in zip(map(int,a.split(':')),[6,.1])); bb=sum(x*y for x,y in zip(map(int,b.split(':')),[6,.1]))
                aa,bb=int(round(aa)),int(round(bb)); ok &= np.all(r[i,aa:bb,4]>1e-8) and not reconstructed[aa:bb].any()
                reconstructed[aa:bb]=1; err=max(err,abs(q-r[i,aa:bb,4].sum()))
            ok &= np.array_equal(reconstructed>0,r[i,:,4]>1e-8)
        err=max(err,abs(printed-r[:,:,4].sum()))
        for sn in wb.sheetnames:
            for col,dim in tpl[sn].column_dimensions.items(): style_errors+=int(wb[sn].column_dimensions[col].width!=dim.width)
            ok &= str(wb[sn].page_setup)==str(tpl[sn].page_setup)
            ok &= not any(c.data_type=='e' or c.value=='⁝' for row in wb[sn] for c in row)
        check(name+'_excel_values',ok and err<1e-5,dict(max_error=err,emergency_kwh=printed))
        check(name+'_excel_styles',style_errors==0,style_errors)
        wb.close(); tpl.close()
        with (OUT/f'{name}_intervals.csv').open(encoding='utf-8-sig') as f: csvrows=list(csv.DictReader(f))
        keys=[(rr['date'],rr['slot']) for rr in csvrows]
        check(name+'_csv_keys',len(keys)==48096 and len(set(keys))==48096,len(keys))
    sig=json.loads((OUT/'signature.json').read_text(encoding='utf-8'))
    changed=[p for p,h in sig['inputs'].items() if sha(ROOT/p)!=h]
    check('protected_input_hashes',not changed,changed)
    changed=[p for p,h in sig['sources'].items() if sha(BASE/p)!=h]
    check('solver_source_hashes',not changed,changed)
    state=json.loads((OUT/'checkpoint.json').read_text(encoding='utf-8'))
    bad_days=[d for d,h in state['day_hashes'].items() if sha(OUT/'days'/f'{int(d):03d}.npz')!=h]
    check('checkpoint_completeness',state['next_day']==365 and len(state['day_hashes'])==334 and not bad_days,bad_days)
    payload=dict(passed=sum(r['passed'] for r in records.values()),total=len(records),checks=records)
    (OUT/'audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    # Output-only refresh; the auditing calculations above call no solver/cost helper.
    import deliver
    deliver.report(); deliver.manifest()
    print(f'Audit {payload["passed"]}/{payload["total"]}')
    return payload['passed']==payload['total']

if __name__=='__main__': sys.exit(0 if main() else 1)
