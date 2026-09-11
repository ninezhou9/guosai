"""Q2 causal backtest: SARIMA -> paired errors -> two-stage CVaR -> MPC.
Run with Python313; project-only statsmodels dependencies in .deps.
"""
from pathlib import Path
import sys, json, csv, hashlib, time, warnings, argparse, platform, inspect
from datetime import datetime, timedelta
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'代码/.deps'))
import numpy as np
import scipy
from scipy.optimize import linprog
from scipy.sparse import lil_matrix,csr_matrix
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels
import q1_solution as q1
openpyxl=q1.openpyxl
OUT=ROOT/'代码/results/q2'; OUT.mkdir(parents=True,exist_ok=True)
N=144; DT=1/6; ETA=.9; CAP=5000/6; TOL=2e-5

def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def date(d):return (datetime(2025,1,1)+timedelta(days=int(d))).strftime('%Y-%m-%d')
def csvout(name,header,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def load():
    wb=openpyxl.load_workbook(ROOT/'基础数据/附件2.xlsx',read_only=True,data_only=True)
    arrays=[];heads=[];audit={}
    for ws in wb:
        rows=list(ws.values);assert len(rows)==366 and len(rows[0])==145
        heads.append(rows[0][1:])
        for d,row in enumerate(rows[1:]):assert row[0]==datetime(2025,1,1)+timedelta(days=d)
        a=np.array([r[1:] for r in rows[1:]],float)
        assert a.shape==(365,144) and np.isfinite(a).all() and (a>=0).all()
        arrays.append(a);audit[ws.title]={'shape':list(a.shape),'missing':int(np.isnan(a).sum()),'min':float(a.min()),'max':float(a.max())}
    assert len(arrays)==2 and heads[0]==heads[1]
    wb.close()
    wb=openpyxl.load_workbook(ROOT/'基础数据/附件1.xlsx',read_only=True,data_only=True)
    rows=list(wb.active.values)
    def minute(v):
        if hasattr(v,'hour'):return v.hour*60+v.minute
        if v=='0:00+1':return 1440
        h,m=map(int,str(v).split(':'));return h*60+m
    assert [minute(r[0]) for r in rows[1:]]==[minute(v) for v in heads[0]]==list(range(10,1441,10))
    p=np.array([r[1] for r in rows[1:]],float);assert (p>0).all();wb.close()
    # q1 reader validates all 144 end-of-interval labels.
    q1.load()
    dump(OUT/'数据审计.json',{'sheets':audit,'date_range':[date(0),date(364)],'time_alignment':'00:10 denotes 00:00-00:10; 24:00 denotes 23:50-24:00','inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'基础数据/附件1.xlsx',ROOT/'基础数据/附件2.xlsx']}})
    return np.array(arrays),p

def forecast(y,d,order):
    # Seasonal differencing is explicitly inverted: forecast difference + yesterday.
    hist=y[max(0,d-28):d].reshape(-1)/1000
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model=SARIMAX(hist,order=(order,0,0),seasonal_order=(0,1,0,144),trend='n',simple_differencing=True,
                      enforce_stationarity=True,enforce_invertibility=True)
        fit=model.fit(disp=False,maxiter=150)
    if not fit.mle_retvals.get('converged',False) or caught:
        with warnings.catch_warnings(record=True) as retry_warnings:
            warnings.simplefilter('always')
            fit=model.fit(disp=False,maxiter=500,method='powell')
        if not fit.mle_retvals.get('converged',False) or retry_warnings:
            raise RuntimeError(f'SARIMA unresolved warning day={d} p={order}: {[str(w.message) for w in retry_warnings]} {fit.mle_retvals}')
        with (OUT/'forecast_retry.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps({'day':date(d),'order':order,'initial_warnings':[str(w.message) for w in caught],'resolved_by':'converged Powell optimization'})+'\n')
    pred=(np.asarray(fit.forecast(144))+hist[-144:])*1000
    assert np.isfinite(pred).all()
    return np.maximum(pred,0),float(fit.aic)

def prepare(y):
    path=OUT/'forecasts.npz'
    if path.exists():
        z=np.load(path);assert str(z['input_hash'])==sha(ROOT/'基础数据/附件2.xlsx')
        return z['pred']
    pred=np.zeros_like(y);pred[:,1:7]=y[:,:6]
    candidates=np.empty((2,3,14,144));records=[];orders=[]
    for v in range(2):
        for order in range(3):
            aics=[]
            for d in range(7,21):
                candidates[v,order,d-7],aic=forecast(y[v],d,order);aics.append(aic)
            err=candidates[v,order,7:]-y[v,14:21]
            records.append({'series':['load','pv'][v],'p':order,'seasonal_order':[0,1,0,144],
                'validation':'2025-01-15..2025-01-21','MAE_kW':float(abs(err).mean()),'RMSE_kW':float(np.sqrt((err**2).mean())),
                'mean_AIC_scaled_series':float(np.mean(aics[7:]))})
        choices=records[-3:];best=min(choices,key=lambda r:(r['RMSE_kW'],r['mean_AIC_scaled_series']))['p'];orders.append(best)
        pred[v,7:21]=candidates[v,best]
        print('forecast selected',v,best,flush=True)
        for d in range(21,365):
            pred[v,d],_=forecast(y[v],d,best)
            if d%30==0:print('forecast',v,date(d),flush=True)
    dump(OUT/'预测模型选择.json',{'candidates':records,'selected_p':orders,'training_window_days':28,'orders_frozen_at':'2025-01-22 00:00','no_future_data':'each fit uses rows strictly before prediction day; hyperparameters frozen before Feb'})
    np.savez_compressed(path,pred=pred,input_hash=sha(ROOT/'基础数据/附件2.xlsx'))
    return pred

def cleanup(c,q,w):
    # Preserve internal SOC exactly and redirect recovered conversion losses to spill.
    a=np.minimum(c,q/(ETA*ETA))
    return c-a,q-ETA*ETA*a,w+(1-ETA*ETA)*a

def plan(p,net,initial,alpha,lam,kappa):
    # net: scenario x 144, kWh. Shared g, scenario c,q,e,w,E, xi,u.
    S,H=net.shape; block=5*H+1; dim=H+S*block+1+S; xi=H+S*block
    obj=np.zeros(dim);obj[:H]=p
    bounds=[(0,None)]*dim
    A=lil_matrix((S*2*H,dim));b=np.empty(S*2*H)
    U=lil_matrix((S,dim));ub=np.zeros(S)
    for s in range(S):
        base=H+s*block;C=base;Q=C+H;X=Q+H;W=X+H;E=W+H
        for i in range(H):
            row=s*2*H+i
            A[row,[i,C+i,Q+i,X+i,W+i]]=[1,-1,1,1,-1];b[row]=net[s,i]
            row+=H;A[row,[E+i+1,E+i,C+i,Q+i]]=[1,-1,-ETA,1/ETA];b[row]=0
            bounds[C+i]=(0,CAP);bounds[Q+i]=(0,CAP)
        for i in range(H+1):bounds[E+i]=(1200,10800)
        bounds[E]=(initial,initial)
        obj[X:X+H]=(1-lam)*5*p/S;obj[E+H]=-(1-lam)*kappa/S
        # Shared normal purchase cost separated from CVaR by translation equivariance.
        U[s,X:X+H]=5*p;U[s,E+H]=-kappa;U[s,xi]=-1;U[s,xi+1+s]=-1
        obj[xi+1+s]=lam/(S*(1-alpha))
    obj[xi]=lam;bounds[xi]=(None,None)
    res=linprog(obj,A_ub=U.tocsr(),b_ub=ub,A_eq=A.tocsr(),b_eq=b,bounds=bounds,method='highs')
    assert res.success,res.message
    max_res=0.;max_sim=0.
    for s in range(S):
        z=res.x[H+s*block:H+(s+1)*block];c,q,e,w=z[:H],z[H:2*H],z[2*H:3*H],z[3*H:4*H];E=z[4*H:]
        c,q,w=cleanup(c,q,w)
        max_res=max(max_res,float(abs(res.x[:H]+e+q-c-w-net[s]).max()),float(abs(np.diff(E)-ETA*c+q/ETA).max()))
        max_sim=max(max_sim,float(np.minimum(c,q).max()))
    assert max_res<TOL and max_sim<TOL
    return res.x[:H],max_res

def control(p,net,g,initial,kappa):
    H=len(p);dim=5*H+1;C=0;Q=H;X=2*H;W=3*H;E=4*H
    obj=np.zeros(dim);obj[X:X+H]=5*p;obj[E+H]=-kappa
    A=lil_matrix((2*H,dim));b=np.zeros(2*H);bounds=[(0,None)]*dim
    for i in range(H):
        A[i,[C+i,Q+i,X+i,W+i]]=[-1,1,1,-1];b[i]=net[i]-g[i]
        A[H+i,[E+i+1,E+i,C+i,Q+i]]=[1,-1,-ETA,1/ETA]
        bounds[C+i]=(0,CAP);bounds[Q+i]=(0,CAP)
    for i in range(H+1):bounds[E+i]=(1200,10800)
    bounds[E]=(initial,initial)
    res=linprog(obj,A_eq=A.tocsr(),b_eq=b,bounds=bounds,method='highs');assert res.success,res.message
    c,q,e,w=res.x[0],res.x[Q],res.x[X],res.x[W]
    c,q,w=cleanup(c,q,w)
    return np.array([c,q,e,w,res.x[E+1]])

def simulate(d,initial,y,p,pred,kappa,alpha,lam):
    # No access to actual day until step t; only y[:,d,:t+1] passed to updater.
    ids=np.arange(max(7,d-30),d)
    scenarios=np.maximum(pred[:,d,None,:]+(y[:,ids,:]-pred[:,ids,:]),0)
    net=(scenarios[0]-scenarios[1])*DT
    g,plan_res=plan(p,net,initial,alpha,lam,kappa)
    states=[initial];rows=[]
    for t in range(N):
        observed=y[:,d,:t+1]
        bias=(observed[:,max(0,t-5):]-pred[:,d,max(0,t-5):t+1]).mean(axis=1)
        future=np.maximum(pred[:,d,t:]+bias[:,None]*np.exp(-np.arange(N-t)[None,:]/6),0)
        future[:,0]=observed[:,-1]  # current interval measurement, no later actuals
        c,q,e,w,nextE=control(p[t:],(future[0]-future[1])*DT,g[t:],states[-1],kappa)
        rows.append([g[t],c,q,e,w,states[-1],nextE]);states.append(nextE)
    arr=np.array(rows)
    validate(arr,y[:,d],p)
    return arr,plan_res

def validate(a,actual,p):
    g,c,q,e,w,before,after=a.T
    errs=[np.max(abs(g+e+(actual[1]-actual[0])*DT+q-c-w)),np.max(abs(after-before-ETA*c+q/ETA)),
          np.max(np.minimum(c,q)),max(0,1200-before.min(),1200-after.min(),before.max()-10800,after.max()-10800),
          max(0,c.max()-CAP,q.max()-CAP),max(0,-a[:,:5].min())]
    if len(a)>1:errs.append(np.max(abs(before[1:]-after[:-1])))
    assert max(errs)<TOL,errs
    return float(max(errs))

def warm(y,p,pred):
    # Jan 1 no prehistory: zero day-ahead schedule, causal greedy balancing.
    # Jan 2-21 use previous-day net schedule; no model chosen using later data.
    arr=[];E=6000.
    for d in range(21):
        g=np.zeros(N) if d==0 else np.maximum((y[0,d-1]-y[1,d-1])*DT,0)
        day=[]
        for t in range(N):
            deficit=(y[0,d,t]-y[1,d,t])*DT-g[t];c=q=e=w=0.
            if deficit>0:q=min(deficit,CAP,(E-1200)*ETA);e=deficit-q
            else:c=min(-deficit,CAP,(10800-E)/ETA);w=-deficit-c
            end=E+ETA*c-q/ETA;day.append([g[t],c,q,e,w,E,end]);E=end
        a=np.array(day);validate(a,y[:,d],p);arr.append(a)
    return np.array(arr)

def backtest(y,p,pred):
    warm_arr=warm(y,p,pred);np.save(OUT/'january_warmup.npy',warm_arr)
    settings=[]
    for k in [float(.9*p.mean()),float(p.mean()/.9)]:
        for alpha,lam in [(.9,0),(.8,.25),(.9,.25),(.9,.5)]:settings.append((k,alpha,lam))
    scores=[];validations=[]
    for j,(k,alpha,lam) in enumerate(settings):
        path=OUT/f'validation_{j}.npy'
        if path.exists():a=np.load(path)
        else:
            E=warm_arr[-1,-1,-1];days=[]
            for d in range(21,31):
                a,_=simulate(d,E,y,p,pred,k,alpha,lam);E=a[-1,-1];days.append(a)
                print('validation',j,date(d),flush=True)
            a=np.array(days);np.save(path,a)
        validations.append(a)
        normal=float((a[:,:,0]*p).sum());emergency=float((a[:,:,3]*5*p).sum())
        scores.append({'index':j,'kappa':k,'alpha':alpha,'lambda':lam,'normal_yuan':normal,'emergency_yuan':emergency,
            'total_yuan':normal+emergency,'end_soc_kWh':float(a[-1,-1,-1]),'emergency_kWh':float(a[:,:,3].sum())})
    risk=min([r for r in scores if r['lambda']>0],key=lambda r:r['total_yuan'])
    neutral=min([r for r in scores if r['lambda']==0],key=lambda r:r['total_yuan'])
    dump(OUT/'风险参数选择.json',{'validation_dates':['2025-01-22','2025-01-31'],'scores':scores,'risk_selected':risk,'neutral_selected':neutral,
        'selection_rule':'minimum January validation actual transaction cost, independent of Feb-Dec','terminal_value_not_counted_in_actual_cost':True})
    outputs={}
    for name,chosen in [('risk',risk),('neutral',neutral)]:
        folder=OUT/name;folder.mkdir(exist_ok=True)
        E=validations[chosen['index']][-1,-1,-1];days=[]
        for d in range(31,365):
            path=folder/f'{date(d)}.npy'
            if path.exists():a=np.load(path)
            else:
                a,res=simulate(d,E,y,p,pred,chosen['kappa'],chosen['alpha'],chosen['lambda']);np.save(path,a)
            assert abs(a[0,5]-E)<TOL
            validate(a,y[:,d],p);E=a[-1,-1];days.append(a)
            print('backtest',name,date(d),'cost',round(float(p@(a[:,0]+5*a[:,3])),2),flush=True)
        outputs[name]=np.array(days)
    return outputs

def export(y,p,pred,outputs):
    import matplotlib
    import matplotlib.pyplot as plt
    selection=json.loads((OUT/'风险参数选择.json').read_text(encoding='utf-8'))
    summary={};daily=[];errors=[];maxerr=0.
    for name,a in outputs.items():
        for j,d in enumerate(range(31,365)):
            maxerr=max(maxerr,validate(a[j],y[:,d],p))
            if j:assert abs(a[j,0,5]-a[j-1,-1,6])<TOL
            normal=float(p@a[j,:,0]);emergency=float(5*p@a[j,:,3])
            daily.append([name,date(d),normal,emergency,normal+emergency,float(a[j,:,0].sum()),float(a[j,:,3].sum()),float(a[j,:,4].sum()),float(a[j,0,5]),float(a[j,-1,6])])
        normal=float((a[:,:,0]*p).sum());emergency=float((a[:,:,3]*5*p).sum())
        day_cost=(p*(a[:,:,0]+5*a[:,:,3])).sum(axis=1)
        tail_mass=.05*len(day_cost);whole=int(tail_mass);ordered=np.sort(day_cost)[::-1]
        tail_cvar=float((ordered[:whole].sum()+(tail_mass-whole)*ordered[whole])/tail_mass)
        annual_balance=float(a[:,:,0].sum()+a[:,:,3].sum()+(y[1,31:]-y[0,31:]).sum()*DT-a[:,:,4].sum()
            -(1-ETA)*a[:,:,1].sum()-(1/ETA-1)*a[:,:,2].sum()-(a[-1,-1,6]-a[0,0,5]))
        assert abs(annual_balance)<TOL
        # w is combined spill; it cannot all be attributed to curtailed PV.
        summary[name]={'normal_cost_yuan':normal,'emergency_cost_yuan':emergency,'total_cost_yuan':normal+emergency,
            'purchase_kWh':float(a[:,:,0].sum()),'emergency_kWh':float(a[:,:,3].sum()),'surplus_spill_kWh':float(a[:,:,4].sum()),
            'start_soc_kWh':float(a[0,0,5]),'end_soc_kWh':float(a[-1,-1,6]),
            'emergency_intervals':int((a[:,:,3]>TOL).sum()),'charge_kWh':float(a[:,:,1].sum()),'discharge_kWh':float(a[:,:,2].sum()),
            'actual_daily_CVaR95_yuan':tail_cvar,'max_daily_cost_yuan':float(day_cost.max()),'annual_energy_balance_residual_kWh':annual_balance}
        rows=[]
        for j,d in enumerate(range(31,365)):
            for t in range(N):
                rows.append([date(d),q1.clock(t*10)+'-'+q1.clock((t+1)*10),*a[j,t],p[t],p[t]*(a[j,t,0]+5*a[j,t,3])])
        csvout(f'{name}_完整调度.csv',['日期','时间段','计划购电_kWh','充电_kWh','放电_kWh','紧急购电_kWh','富余电量_kWh','期初储电_kWh','期末储电_kWh','电价_元每kWh','交易费_元'],rows)
    csvout('每日费用.csv',['方案','日期','计划购电费_元','紧急购电费_元','总费用_元','计划购电_kWh','紧急购电_kWh','富余电量_kWh','日初储电_kWh','日末储电_kWh'],daily)
    for v in range(2):
        err=pred[v,31:]-y[v,31:]
        naive=y[v,30:364]-y[v,31:]
        errors.append({'series':['load','pv'][v],'MAE_kW':float(abs(err).mean()),'RMSE_kW':float(np.sqrt((err**2).mean())),
            'previous_day_baseline_MAE_kW':float(abs(naive).mean()),'previous_day_baseline_RMSE_kW':float(np.sqrt((naive**2).mean()))})
    csvout('信息可用性清单.csv',['预测日期','训练末日','最早误差日','最晚误差日','情景数','超参数选取截止日'],
        [[date(d),date(d-1),date(max(7,d-30)),date(d-1),min(d-7,30),'2025-01-31'] for d in range(31,365)])
    csvout('日前预测.csv',['日期','时间段','预测负载_kW','预测光伏_kW'],
        [[date(d),q1.clock(t*10)+'-'+q1.clock((t+1)*10),float(pred[0,d,t]),float(pred[1,d,t])] for d in range(31,365) for t in range(N)])
    summary['forecast_errors']=errors
    summary['validation']={'max_physical_residual_kWh':maxerr,'date_count':334,'interval_count_per_policy':334*144,'physical_tolerance_kWh':TOL,'cross_day_continuity':'passed'}
    summary['risk_vs_neutral']={key:float((summary['risk'][key]/summary['neutral'][key]-1)*100) for key in ['total_cost_yuan','emergency_kWh','emergency_cost_yuan','actual_daily_CVaR95_yuan'] if summary['neutral'][key]!=0}
    summary['parameters']={name:selection[name+'_selected'] for name in ['risk','neutral']}
    dump(OUT/'summary.json',summary)
    # Result workbook preserves required sheet names; official template absent.
    a=outputs['risk'];wb=openpyxl.Workbook();ws=wb.active;ws.title='计划购电量'
    ws.append(['日期']+[q1.clock((t+1)*10) for t in range(N)])
    for j,d in enumerate(range(31,365)):ws.append([date(d)]+a[j,:,0].tolist())
    ws=wb.create_sheet('充放电量');ws.append(['日期']+[f'{q1.clock(k*240)}-{q1.clock((k+1)*240)} {z}（kWh）' for k in range(6) for z in ['充电','放电']]+['0:00储电量（kWh）','24:00储电量（kWh）'])
    for j,d in enumerate(range(31,365)):
        ws.append([date(d)]+[float(a[j,k*24:(k+1)*24,col].sum()) for k in range(6) for col in [1,2]]+[float(a[j,0,5]),float(a[j,-1,6])])
    ws=wb.create_sheet('紧急购电量');ws.append(['日期','紧急购电时间段','紧急购电量（kWh）'])
    emergency_total=0.
    for j,d in enumerate(range(31,365)):
        t=0
        while t<N:
            if a[j,t,3]<=TOL:t+=1;continue
            start=t
            while t<N and a[j,t,3]>TOL:t+=1
            amount=float(a[j,start:t,3].sum());emergency_total+=amount
            ws.append([date(d),q1.clock(start*10)+'-'+q1.clock(t*10),amount])
    assert abs(emergency_total-a[:,:,3].sum())<1e-3
    ws=wb.create_sheet('四个指定日明细');ws.append(['日期','时间段','计划购电_kWh','充电_kWh','放电_kWh','紧急购电_kWh','富余电量_kWh','期初储电_kWh','期末储电_kWh'])
    selected=[78,171,265,354]
    assert [date(d) for d in selected]==['2025-03-20','2025-06-21','2025-09-23','2025-12-21']
    for d in selected:
        for t in range(N):ws.append([date(d),q1.clock(t*10)+'-'+q1.clock((t+1)*10),*a[d-31,t].tolist()])
    ws=wb.create_sheet('表1');ws.append(['日期']+[f'{h:02}:00-{h:02}:10购电（kWh）' for h in [10,12,14,16,18,20]]+['全天购电_kWh','计划购电费_元','紧急购电费_元','总费用_元'])
    for d in selected:
        day=a[d-31];ws.append([date(d)]+[float(day[h*6,0]) for h in [10,12,14,16,18,20]]+[float(day[:,0].sum()),float(p@day[:,0]),float(5*p@day[:,3]),float(p@(day[:,0]+5*day[:,3]))])
    ws=wb.create_sheet('口径与状态')
    for row in [['状态','待用户审核；按用户指定结束时标；与已提供官方模板标签有差异'],['日前','相同历史日联合误差；最近最多30天；计划购电全天固定'],['预测','SARIMA(p,0,0)(0,1,0)[144]，p仅用1月选取，每天重新拟合'],['终端价值','Phi(E)=-kappa E；只参与规划，不计入实际交易费'],['日内','当前区间功率视作可观测；过去最多6个误差均值，未来按exp(-h/6)衰减；只执行第一步'],['起点','1月1日6000kWh，1月连续预热与验证，2月继承1月31日状态'],['计划近似','两阶段情景补救有完整轨迹信息，仅用于日前规划；最终费用来自因果滚动执行'],['富余','富余电量包含计划购电剩余与光伏剩余，不直接称弃光'],['参数','1月22—31日验证，2—12月仅作样本外评价'],['末日','12月31日仍保留规划终端价值；报告最终电量，不强制末日清空或回到6000']]:ws.append(row)
    from openpyxl.styles import Font,PatternFill
    for ws in wb:
        ws.freeze_panes='B2';ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='24536B')
        ws.column_dimensions['A'].width=16
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value,(int,float)):cell.number_format='0.000000'
    target=OUT/'result2_审核版.xlsx';wb.save(target)
    check=openpyxl.load_workbook(target,data_only=True,read_only=True)
    purchases=np.array([r[1:] for r in list(check['计划购电量'].values)[1:]],float)
    assert purchases.shape==(334,144) and np.max(abs(purchases-a[:,:,0]))<TOL
    assert abs(float((purchases*p).sum())-summary['risk']['normal_cost_yuan'])<.001
    emergencies=sum(float(r[2]) for r in list(check['紧急购电量'].values)[1:]);assert abs(emergencies-summary['risk']['emergency_kWh'])<.001
    check.close()
    figs=ROOT/'代码/figures/q2';figs.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':10,'axes.unicode_minus':False})
    fig,ax=plt.subplots(figsize=(7.2,3.5),layout='constrained')
    for name,label,color in [('risk','风险方案','#E64B35'),('neutral','风险中性','#3C5488')]:
        vals=np.array([r[4] for r in daily if r[0]==name]);ax.plot(np.arange(334)+1,np.cumsum(vals)/1e4,label=label,color=color)
    ax.set_xlabel('回测日序号（2月1日起）');ax.set_ylabel('累计交易费用（万元）');ax.legend();ax.grid(alpha=.2)
    for ext in ['png','svg']:fig.savefig(figs/f'累计费用.{ext}',dpi=300)
    plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(7.2,5),sharex=True,layout='constrained')
    for v,ax in enumerate(axes):
        ax.plot(np.arange(N)/6,y[v,78],color='#3C5488',label='实际值')
        ax.plot(np.arange(N)/6,pred[v,78],color='#E64B35',ls='--',label='日前预测')
        ax.set_ylabel(['负载（kW）','光伏（kW）'][v]);ax.legend();ax.grid(alpha=.2)
    axes[-1].set_xlabel('时刻（h）');axes[-1].set_xticks([0,6,12,18,24])
    for ext in ['png','svg']:fig.savefig(figs/f'3月20日预测对照.{ext}',dpi=300)
    plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(9,6),layout='constrained')
    for ax,d in zip(axes.flat,selected):
        day=a[d-31];ax.plot(np.arange(145)/6,np.r_[day[:,5],day[-1,6]],label=date(d),color='#3C5488')
        for level in [1200,10800]:ax.axhline(level,color='gray',ls='--',lw=.8)
        ax.set_xlabel('时刻（h）');ax.set_ylabel('储电量（kWh）');ax.legend();ax.set_xticks([0,6,12,18,24]);ax.grid(alpha=.2)
    for ext in ['png','svg']:fig.savefig(figs/f'四个指定日储电量.{ext}',dpi=300)
    plt.close(fig)
    report=['# 第二问真实回测结果（待审核）','', '区间：2025-02-01至2025-12-31，共334天、48096个十分钟时段；每种策略独立连续运行。','',
        '|方案|计划购电费（元）|紧急购电费（元）|总交易费（元）|紧急购电量（kWh）|','|---|---:|---:|---:|---:|']
    for name in ['risk','neutral']:
        v=summary[name];report.append(f'|{name}|{v["normal_cost_yuan"]:.6f}|{v["emergency_cost_yuan"]:.6f}|{v["total_cost_yuan"]:.6f}|{v["emergency_kWh"]:.6f}|')
    report+=['','参数及比较（正数表示风险方案增加）：','```json',json.dumps({'parameters':summary['parameters'],'changes_percent':summary['risk_vs_neutral'],'forecast_errors':errors},ensure_ascii=False,indent=2),'```','',
        '## 验证','```json',json.dumps(summary['validation'],ensure_ascii=False,indent=2),'```','Excel重新读取的计划电量、费用及汇总紧急电量与原始结果一致。',
        '','## 解释边界',
        '- 风险方案不保证费用或紧急购电必然优于风险中性；如真实回测更差，应如实呈现，不按测试集挑选有利参数。',
        '- 本次光伏SARIMA仅含短滞后AR与日季节差分，午夜差分递推起点为零，日前光伏预测数值上等同前一日曲线。不能据此宣称光伏预测有额外提升；完整差异核验见光伏预测基线核验.json。',
        '- 两阶段规划允许情景内完整补救，属于规划近似；报告费用仅来自固定日前计划后的逐步执行，未使用未来实测控制储能。',
        '- 当前十分钟区间的功率视为可观测、区间内恒定，是执行离散化假设；若要求区间开始时也不可知当前平均功率，需要更细时间尺度。',
        '- 参数仅在1月验证；全年样本外累计费用用于评价，未反向调整参数。候选网格较小、1月验证仅10天，不宣称全局最优参数或跨季节稳健。',
        '- 富余电量不等于纯光伏弃电；不据此推断光伏消纳率。',
        '- 两方案从1月1日6000kWh连续演化，2月初及年末状态可能不同；参见summary.json，不将电池存量价值算成电费。',
        '- 已提供官方模板，但用户要求沿用结束时标，当前Excel标签与官方存在差异；未写入Word、未冻结。',
        '','## 文件','risk_完整调度.csv、neutral_完整调度.csv、每日费用.csv、预测模型选择.json、风险参数选择.json、复现清单.json。']
    (OUT/'第二问结果审核.md').write_text('\n'.join(report),encoding='utf-8')
    files=[p for p in OUT.iterdir() if p.is_file() and p.name not in ['复现清单.json','run_complete.json','运行日志.txt']]+list(figs.glob('*'))
    dump(OUT/'复现清单.json',{'command':f'& "{sys.executable}" "代码/q2_solution.py"','python':platform.python_version(),'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},
        'random_seed':None,'sampling':'all latest up to30 paired historical residual days, equal weights; deterministic',
        'inputs':{str(f.relative_to(ROOT)):sha(f) for f in [ROOT/'基础数据/附件1.xlsx',ROOT/'基础数据/附件2.xlsx',ROOT/'基础数据/C题.pdf',Path(__file__),ROOT/'代码/q1_solution.py']},
        'outputs':{str(f.relative_to(ROOT)):sha(f) for f in files},'parameters':summary['parameters'],'validation':summary['validation'],
        'status':'真实运行完成，结果待审核；用户指定结束时标，官方标签差异已注明','units':'all dispatch variables kWh; powers kW; price yuan/kWh'})
    print('SUMMARY',json.dumps(summary,ensure_ascii=False),flush=True)

def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run','export'],default='run')
    parser.add_argument('--output-dir',type=Path,default=OUT)
    args=parser.parse_args()
    OUT=args.output_dir.resolve()
    assert OUT.is_relative_to(ROOT),'输出必须位于项目内'
    OUT.mkdir(parents=True,exist_ok=True)
    y,p=load();pred=prepare(y)
    if args.stage=='prepare':return
    signature=hashlib.sha256((''.join(inspect.getsource(f) for f in [load,forecast,prepare,plan,cleanup,control,simulate,warm,backtest])+
        sha(ROOT/'基础数据/附件1.xlsx')+sha(ROOT/'基础数据/附件2.xlsx')+sha(OUT/'forecasts.npz')+scipy.__version__+statsmodels.__version__+
        json.dumps([N,DT,ETA,CAP,TOL])).encode()).hexdigest()
    cache_contract=OUT/'计算缓存合同.json'
    if cache_contract.exists():
        assert json.loads(cache_contract.read_text(encoding='utf-8'))['signature']==signature,'模型或数据已变化；请使用新的结果目录重新计算，禁止复用旧缓存'
    else:dump(cache_contract,{'signature':signature,'scope':'solver functions, selection grid, forecast cache, inputs and scipy version','cache_policy':'fail on change; use a new output directory for changed models'})
    if args.stage=='export':
        outputs={name:np.array([np.load(OUT/name/f'{date(d)}.npy') for d in range(31,365)]) for name in ['risk','neutral']}
    else:
        outputs=backtest(y,p,pred)
    export(y,p,pred,outputs)
    dump(OUT/'run_complete.json',{'status':'backtest and export finished','counts':{k:list(v.shape) for k,v in outputs.items()}})

if __name__=='__main__':main()
