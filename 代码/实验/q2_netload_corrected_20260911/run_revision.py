"""Audit corrections. Read prior causal forecasts; all new output stays here."""
from pathlib import Path
import sys, json, time, argparse, platform
sys.dont_write_bytecode=True
import numpy as np
import base_engine as b

BASE=Path(__file__).resolve().parent
OLD=BASE.parent/'q2_netload_probabilistic_20260911'
OUT=BASE/'results';OUT.mkdir(exist_ok=True)
b.BASE=BASE;b.OUT=OUT
BASE_MARKOV=b.markov
BASE_CHOOSE=b.choose_plan
SAMPLES=7
NAMES=['main','median_only','greedy_same_plan','delayed_same_plan']

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def atomize(values,limit=SAMPLES):
    """Retain both empirical extremes; compress interior into weighted bins.
    Mean preserved, unlike arbitrary normal draws; remaining compression explicit.
    """
    a=np.sort(np.asarray(values,float))
    if len(a)<=limit:return a,np.full(len(a),1/len(a))
    groups=[a[:1],*np.array_split(a[1:-1],limit-2),a[-1:]]
    return np.array([x.mean() for x in groups]),np.array([len(x)/len(a) for x in groups])

def markov(y,pred,d,limit=SAMPLES):
    m=BASE_MARKOV(y,pred,d)
    ids=np.arange(max(14,d-30),d)
    z=((y[0]-y[1])[ids]-pred[ids,1])/np.maximum((pred[ids,3]-pred[ids,0])/1.683,100.)
    states=np.digitize(z,[-.84,.84])
    samples=np.zeros((b.N,3,limit));weights=np.zeros_like(samples)
    for t in range(b.N):
        sl=slice(max(0,t-3),min(b.N,t+4));zs=z[:,sl];ss=states[:,sl]
        for s in range(3):
            vals=zs[ss==s]
            if len(vals)==0:vals=np.array([[-1.4,0,1.4][s]])
            atoms,w=atomize(vals,limit)
            samples[t,s,:len(w)]=(pred[d,1,t]+m['scale'][t]*atoms)*b.DT
            weights[t,s,:len(w)]=w
    m['samples']=samples;m['weights']=weights
    # Expected candidate now uses the same empirical conditional means as Bellman.
    m['net']=(samples*weights).sum(axis=2)
    assert np.allclose(weights.sum(axis=2),1)
    return m

def bellman(p,g,m,kappa,grid=b.GRID):
    H=len(p);V=np.empty((H+1,3,len(grid)));V[H]=-kappa*grid
    for t in range(H-1,-1,-1):
        for s in range(3):
            future=V[t+1,s] if t==H-1 else m['P'][t,s]@V[t+1]
            if 'samples' not in m:
                V[t,s]=b.grid_value(future,m['net'][t,s]-g[t],p[t],grid)
            else:
                V[t,s]=0.
                for value,w in zip(m['samples'][t,s],m['weights'][t,s]):
                    if w>0:V[t,s]+=w*b.grid_value(future,value-g[t],p[t],grid)
    assert np.isfinite(V).all() and np.diff(V,axis=2).max()<b.TOL
    return V

b.markov=markov;b.bellman=bellman

def choose(p,pred_day,m,E,k,median=False,grid=b.GRID):
    return BASE_CHOOSE(p,pred_day,m,E,k,median_only=median,grid=grid)

def delayed_execute(actual,p,g,E0,m,V,grid=b.GRID):
    """Previous interval classification determines reserve BEFORE seeing current r.
    Local protection clips commands to measured surplus/deficit; no emergency charge.
    This tests delayed EMS information, not lack of local physical sensing.
    """
    rows=[];commands=[];E=float(E0)
    for t in range(b.N):
        if t==0:belief=m['initial']
        else:
            last_s=int(np.digitize((actual[t-1]-m['center'][t-1])/m['scale'][t-1],[-.84,.84]))
            belief=m['P'][t-1,last_s]
        future=belief@V[t+1] if t==b.N-1 else (belief@m['P'][t])@V[t+1]
        lo=max(b.EMIN,E-b.CAP/b.ETA)
        knots=np.unique(np.r_[lo,E,grid[(grid>=lo)&(grid<=E)]])
        reserve=float(knots[np.argmin(5*p[t]*b.ETA*knots+np.interp(knots,grid,future))])
        discharge_limit=min(b.CAP,max(0,b.ETA*(E-reserve)))
        commands.append([reserve,discharge_limit])
        r=actual[t]*b.DT-g[t]
        if r>0:c=w=0.;q=min(r,discharge_limit);e=max(0,r-q)
        else:q=e=0.;c=max(0,min(-r,b.CAP,(b.EMAX-E)/b.ETA));w=max(0,-r-c)
        nxt=E+b.ETA*c-q/b.ETA
        rows.append([g[t],c,q,e,w,E,nxt]);E=nxt
    a=np.array(rows);b.validate(a,actual,p)
    return a,np.array(commands)

def annual_warmup(y,p):
    """Same executable prior-day rule all of January, independent of selected k."""
    a=list(b.warm(y));E=a[-1][-1,-1];net=y[0]-y[1]
    for d in range(21,31):
        g=np.maximum(net[d-1]*b.DT,0)
        day=b.execute(net[d],p,g,E,None,None,greedy=True);a.append(day);E=day[-1,-1]
    result=np.array(a);b.validate(result.reshape(-1,7),net[:31].ravel(),np.tile(p,31))
    np.save(OUT/'january_common_warmup.npy',result)
    return result

def select_k(y,p,pred,warm):
    ref=float(.9*p.mean())
    kappas=ref*np.array([0.,.25,.5,.75,1.,1.25])
    folder=OUT/'january_validation';folder.mkdir(exist_ok=True)
    candidates=[];all_runs=[];E0=float(warm[20,-1,-1])
    for k in kappas:
        path=folder/f'{k:.9f}.npy'
        if path.exists():days=np.load(path)
        else:
            days=[];E=E0
            for d in range(21,31):
                m=markov(y,pred,d);g,V,_,_=choose(p,pred[d],m,E,k)
                a=b.execute((y[0]-y[1])[d],p,g,E,m,V);days.append(a);E=a[-1,-1]
            days=np.asarray(days);np.save(path,days)
        b.validate(days.reshape(-1,7),(y[0]-y[1])[21:31].ravel(),np.tile(p,10))
        actual=b.cost(days,p);end=float(days[-1,-1,-1]);score=actual+ref*(E0-end)
        row={'kappa':float(k),'cost':actual,'inventory_adjusted_validation_score':score,'E_start':E0,'E_end':end,
             'emergency_kWh':float(days[:,:,3].sum())}
        candidates.append(row);all_runs.append(days);b.log('validation',row)
    best=min(candidates,key=lambda r:(r['inventory_adjusted_validation_score'],r['kappa']))
    diffs=[[float(abs(x-z).max()) for z in all_runs] for x in all_runs]
    selection={'candidates':candidates,'selected':best,'inventory_price_common':ref,'frozen_at':'Feb1 00:00',
        'validation':'Jan22-31, terminal inventory adjusted with same exogenous reference price',
        'max_trajectory_differences':diffs,'distinct_trajectories':len({b.sha(folder/f'{k:.9f}.npy') for k in kappas}),
        'actual_E_feb1':float(warm[-1,-1,-1]),'actual_state_source':'same causal Jan1-31 warmup, not chosen retrospective validation path'}
    b.dump(OUT/'controller_selection.json',selection)
    return best['kappa']

def run(y,p,pred):
    warm=annual_warmup(y,p);k=select_k(y,p,pred,warm)
    state={s:float(warm[-1,-1,-1]) for s in NAMES};runs={s:[] for s in NAMES}
    folder=OUT/'days';folder.mkdir(exist_ok=True)
    for d in range(31,365):
        path=folder/f'{b.date(d)}.npz';meta=folder/f'{b.date(d)}.json'
        if path.exists() and meta.exists():
            z=np.load(path)
            daily={s:z[s] for s in NAMES}
        else:
            kt=0. if d==364 else k
            m=markov(y,pred,d);g,V,label,cands=choose(p,pred[d],m,state['main'],kt)
            a=b.execute((y[0]-y[1])[d],p,g,state['main'],m,V)
            gm,Vm,_,_=choose(p,pred[d],m,state['median_only'],kt,True)
            am=b.execute((y[0]-y[1])[d],p,gm,state['median_only'],m,Vm)
            ag=b.execute((y[0]-y[1])[d],p,g,state['greedy_same_plan'],m,V,greedy=True)
            ad,cmd=delayed_execute((y[0]-y[1])[d],p,g,state['delayed_same_plan'],m,V)
            daily=dict(main=a,median_only=am,greedy_same_plan=ag,delayed_same_plan=ad)
            np.savez_compressed(path,**daily,delayed_commands=cmd)
            b.dump(meta,{'date':b.date(d),'terminal_kappa':kt,'chosen_candidate':label,'candidates':cands})
        for s,a in daily.items():
            assert abs(a[0,5]-state[s])<b.TOL
            b.validate(a,(y[0]-y[1])[d],p);runs[s].append(a);state[s]=float(a[-1,-1])
        if (d-31)%15==0 or d==364:b.log('backtest',b.date(d),{s:round(b.cost(np.array(runs[s]),p),2) for s in NAMES})
    for s in NAMES:runs[s]=np.array(runs[s]);np.save(OUT/f'{s}.npy',runs[s])
    return runs,k

def validate(y,p,pred,runs,k):
    checks=b.validate_results(y,p,pred,runs,k)
    # Critical regression: mean-before-shortfall must not return zero.
    m={'net':np.full((1,3),50.),'samples':np.tile(np.array([0.,100.]),(1,3,1)),
       'weights':np.full((1,3,2),.5),'P':np.empty((0,3,3))}
    v=bellman(np.array([1.]),np.array([50.]),m,0.)
    assert abs(v[0,0,0]-125)<1e-8
    checks['within_class_risk_counterexample']={'expected_cost':125.,'actual_Bellman_cost':float(v[0,0,0]),'single_mean_cost':0.}
    d=31;model=markov(y,pred,d);g=runs['main'][0,:,0];E=runs['delayed_same_plan'][0,0,5]
    V=bellman(p,g,model,k)
    act=(y[0]-y[1])[d];mut=act.copy();mut[72:]+=30000
    a,cmd=delayed_execute(act,p,g,E,model,V);aa,cc=delayed_execute(mut,p,g,E,model,V)
    assert np.array_equal(cmd[:73],cc[:73]) and np.array_equal(a[:72],aa[:72])
    checks['delayed_information']={'commands_through_current_step_unchanged_when_current_and_future_actuals_change':True,
        'previous_settled_actions_unchanged':True,'local_protection':'actual power clips charging/discharging commands; not a no-sensor model'}
    sensitivity=[]
    for ds in ['2025-03-20','2025-06-21','2025-09-23','2025-12-21']:
        d=(b.datetime.fromisoformat(ds)-b.datetime(2025,1,1)).days
        orig=runs['main'][d-31];model=markov(y,pred,d,limit=15)
        V=bellman(p,orig[:,0],model,k)
        a=b.execute((y[0]-y[1])[d],p,orig[:,0],orig[0,5],model,V)
        sensitivity.append({'date':ds,'fixed_plan_and_initial_state':True,'cost_7_atoms':b.cost(orig,p),'cost_15_atoms':b.cost(a,p),
                            'E_end_7':float(orig[-1,-1]),'E_end_15':float(a[-1,-1])})
    checks['atom_compression_sensitivity']=sensitivity
    terminal=read(OUT/'days/2025-12-31.json');assert terminal['terminal_kappa']==0.
    assert np.allclose(runs['main'][:,:,0],runs['greedy_same_plan'][:,:,0])
    assert np.allclose(runs['main'][:,:,0],runs['delayed_same_plan'][:,:,0])
    checks['year_boundary']={'Dec31_terminal_kappa':0.,'common_initial_E':float(runs['main'][0,0,5]),
        'main_E_end':float(runs['main'][-1,-1,-1]),'billing_excludes_terminal_value':True}
    selection=read(OUT/'controller_selection.json')
    assert selection['distinct_trajectories']>1
    checks['parameter_identifiability']={'distinct_validation_trajectories':selection['distinct_trajectories'],
        'limited_January_validation_not_statistical_proof':True}
    b.dump(OUT/'validation.json',checks)
    return checks

def report(summary,checks,manifest):
    metrics=summary['new'];prior=read(OLD/'results/summary.json')['new']['main'];sel=read(OUT/'controller_selection.json')
    labels={'main':'修正版主方案','median_only':'中位数购电对照','greedy_same_plan':'同计划简单控制','delayed_same_plan':'同计划延迟观测控制'}
    lines=['# 第二问修正后回测（待审核）','',
        '2025年2月1日—12月31日，共334天、48096个十分钟时段。所有结果由修正代码实际计算；原始数据、旧代码与上一版输出只读。','',
        '| 方案 | 计划费用（元） | 紧急费用（元） | 总费用（元） | 紧急电量（kWh） | 期初电量 | 期末电量 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,m in list(metrics.items())+[('prior',prior)]:
        lines.append(f"| {labels.get(name,'修正前')} | {m['normal_cost']:,.2f} | {m['emergency_cost']:,.2f} | {m['total_cost']:,.2f} | {m['emergency_kWh']:,.2f} | {m['E_start']:.3f} | {m['E_end']:.3f} |")
    change=metrics['main']['total_cost']-prior['total_cost']
    lines+=['',f'修正版比上一版原始账单变化 {change:+,.2f} 元（{100*change/prior["total_cost"]:+.4f}%）。这同时包含风险模型、参数、预热库存与年末口径变化，不是单个模块的纯收益。','',
        '## 四项修正','',
        '1. 每个误差类别保留最多7个加权样本：保留两端极值，内部按经验样本分组；对每个样本分别计算缺口和动作，再按权重求和。剩余分组压缩仍是近似，不宣称风险已完整刻画。',
        '2. 本次采用截至12月31日的固定评价期：只有最后一天终端价值设为0，其余日期使用1月选定的κ；不强迫年末电池必须耗尽。',
        '3. 主方案明确假设十分钟内功率恒定且即时可测。延迟对照在当前时段净负荷进入前，用上一时段类别决定放电储备；本地保护按实际供需限幅，不能称为设备完全没有即时传感器。它是固定主方案购电计划的敏感性实验，不是独立重新优化的延迟信息最优方案。',
        '4. κ扩大到6个候选，用1月22—31日费用加统一库存消耗价值比较；2月初电量来自独立、统一的1月1—31日因果预热，不追溯替换实际预热轨迹。','',
        '## 1月参数验证','',
        '| κ | 实际账单 | 库存调整验证目标 | 期末库存 |','|---|---:|---:|---:|']
    for r in sel['candidates']:lines.append(f"| {r['kappa']:.9f} | {r['cost']:.2f} | {r['inventory_adjusted_validation_score']:.2f} | {r['E_end']:.3f} |")
    lines += ['',f"选定 κ={sel['selected']['kappa']:.9f}；共 {sel['distinct_trajectories']} 个不同验证轨迹。统一库存参考价格={sel['inventory_price_common']:.9f} 元/kWh。这是有限参数网格内的历史选择，不是最优κ的统计证明。",'',
        '## 库存与比较','',
        '修正前期初、期末库存不同，前表同时列示。另用同一固定库存价格检查库存影响量级，调整值并非题目实际账单：','']
    ref=sel['inventory_price_common'];adjusted={}
    for name,m in list(metrics.items())+[('prior',prior)]:
        adjusted[name]=m['total_cost']+ref*(m['E_start']-m['E_end'])
        lines.append(f"- {labels.get(name,'修正前')}：库存调整费用 {adjusted[name]:,.2f} 元。")
    lines+=['','## 验证范围','',
        f"- 四策略全部物理检查通过；最大残差 {max(max(e.values()) for e in checks['physical'].values()):.3e} kWh。",
        '- 状态内部样本反例：需求0/100各半、计划50、电池最低库存时，修正版计算125元期望紧急费用，原均值替代为0元。',
        '- 日前特征和计划的未来数据扰动测试通过；即时控制只声明不读取后续时段。延迟控制额外验证：修改当前及后续实际量，当前储备命令不变，实际限幅结算允许改变。',
        '- 四个指定日期固定计划与期初库存，检查60→30 kWh价值网格及7→15个状态内样本；这是局部精度敏感性，不是全年收敛证明。','',
        '| 日期 | 7样本实际费用 | 15样本实际费用 |','|---|---:|---:|']
    for r in checks['atom_compression_sensitivity']:lines.append(f"| {r['date']} | {r['cost_7_atoms']:.2f} | {r['cost_15_atoms']:.2f} |")
    lines+=['','## 可视化','',
        '下图按日汇总四种控制方案的累计交易费用。','',
        f"![累计费用]({(BASE/'figures/修正版累计费用.png').as_posix()})",'',
        '图1：修正版及对照的累计实际费用。各方案采购或控制信息条件不同，差异解释以前文对照定义为准。','',
        '## 复现与交付','',
        '预测未改变，复用上一版真实逐日因果预测缓存，并校验原代码及输入文件哈希；复制件保存在本目录。上版预测生成代码保存在base_engine.py，本版只替换风险、调度、参数选择与验证模块。','',
        '```powershell',
        "& 'C:/Program Files/Python313/python.exe' -X utf8 '代码/实验/q2_netload_corrected_20260911/run_revision.py' --stage all",
        '```','',
        f"主程序记录运行时间 {manifest['seconds']:.2f} 秒。完整Excel为独立审核表，保留结束标签，没有覆盖官方模板。主结果、延迟对照、参数选择、精度检查、命令和SHA-256见results。",'',
        f"保护文件检查：{manifest['preservation']['checked_files']} 个；变化或缺失：{manifest['preservation']['changed_or_missing']}。",'',
        '已按项目math-modeling-unified的局部计算路线及此前读取的建模、编程、验证、Excel、可视化规则修正。结果待用户审核，未冻结，未写入论文。没有全局最优声明；三类误差的第一阶转移、有限采购候选、样本网格及观测机制仍是明确的近似假设。']
    (BASE/'修正结果报告.md').write_text('\n'.join(lines),encoding='utf-8')
    b.dump(OUT/'comparison_to_prior.json',{'prior':prior,'corrected':metrics,'cost_change_yuan':change,
        'cost_change_percent':100*change/prior['total_cost'],'inventory_adjusted':adjusted})

def plots(runs,p):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':10,'axes.unicode_minus':False})
    folder=BASE/'figures';folder.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(7,4))
    for (name,a),label,color,ls in zip(runs.items(),['修正版主方案','中位数购电','同计划简单控制','同计划延迟观测'],
            ['#0072B2','#D55E00','#009E73','#CC79A7'],['-','--',':','-.']):
        daily=np.sum(a[:,:,0]*p+5*a[:,:,3]*p,axis=1)
        ax.plot(np.arange(1,335),daily.cumsum()/10000,label=label,color=color,linestyle=ls)
    ax.set(xlabel='自2月1日起的天数',ylabel='累计实际购电费用（万元）');ax.legend();fig.tight_layout()
    for ext in ['png','svg']:fig.savefig(folder/f'修正版累计费用.{ext}',dpi=300)
    plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['all','smoke','export'],default='all');args=parser.parse_args()
    started=time.time();y,p=b.load()
    origin=read(OLD/'results/cache_signature.json')
    assert b.sha(BASE/'base_engine.py')==origin['code_sha256']
    for path,h in origin['inputs'].items():assert b.sha(b.ROOT/path)==h
    source=OLD/'results/forecasts.npz';forecast_path=OUT/'forecasts.npz'
    if not forecast_path.exists():forecast_path.write_bytes(source.read_bytes())
    assert b.sha(forecast_path)==b.sha(source)
    for name in ['forecast_selection.json']:
        (OUT/name).write_bytes((OLD/'results'/name).read_bytes())
    pred=np.load(forecast_path)['pred']
    sig={'revision_sha256':b.sha(__file__),'base_engine_sha256':b.sha(BASE/'base_engine.py'),
         'forecast_sha256':b.sha(forecast_path),'inputs':origin['inputs'],'samples':SAMPLES,
         'numpy':np.__version__,'scipy':b.scipy.__version__,'lightgbm':b.lgb.__version__}
    sp=OUT/'cache_signature.json'
    if sp.exists():assert read(sp)==sig,'Code changed; use fresh cache namespace.'
    else:b.dump(sp,sig)
    if args.stage=='smoke':
        m=markov(y,pred,31);g,V,_,_=choose(p,pred[31],m,6000.,.35)
        a=b.execute((y[0]-y[1])[31],p,g,6000.,m,V)
        ad,cmd=delayed_execute((y[0]-y[1])[31],p,g,6000.,m,V)
        b.dump(OUT/'smoke.json',{'main_cost':b.cost(a,p),'delayed_cost':b.cost(ad,p),'seconds':time.time()-started})
        b.log('SMOKE PASSED',time.time()-started);return
    if args.stage=='export':
        runs={s:np.load(OUT/f'{s}.npy') for s in NAMES};k=read(OUT/'controller_selection.json')['selected']['kappa']
    else:runs,k=run(y,p,pred)
    checks=validate(y,p,pred,runs,k)
    # Original table exporter supports arbitrary policies; replace its three-line plot.
    b.make_plots=lambda *args:None
    summary=b.export(y,p,pred,runs,k,checks)
    summary['limitations']=['finite purchase candidate set','3-state first-order Markov transition',
        'up to 7 weighted atoms per state, preserves sample extremes but compresses interior',
        '60 kWh value grid with continuous actual storage','main: instant piecewise-constant observation',
        'delayed: one-step strategic observation delay with local sensor-based protection',
        'fixed annual endpoint, Dec31 terminal value zero','same dataset used in earlier design, not new blind evaluation']
    summary['terminal_kappa_Dec31']=0.;b.dump(OUT/'summary.json',summary)
    # Fix only this new workbook's explanatory text.
    xlsx=OUT/'result2_独立实验审核版.xlsx';wb=b.openpyxl.load_workbook(xlsx)
    ws=wb['口径说明'];ws['B5']='三类误差＋类内最多7个样本、60kWh价值网格、五个购电候选'
    ws.append(['年度边界','仅12月31日终端价值为零，日常κ由1月库存调整费用选择'])
    ws.append(['观测','主方案即时分段恒定；延迟对照仅储备命令滞后一时段，设备本地限幅仍测量当前功率'])
    ws.append(['预热','所有对照从相同1月因果预热结果开始，无每日重置'])
    wb.save(xlsx);wb.close()
    plots(runs,p)
    preservation=b.check_preservation();assert not preservation['changed_or_missing']
    manifest={**sig,'runtime':sys.executable,'python':platform.python_version(),'seed':b.SEED,'kappa':k,
        'seconds':time.time()-started,'status':'completed_pending_user_review','preservation':preservation,
        'command':[sys.executable,'-X','utf8',str(Path(__file__).relative_to(b.ROOT)),'--stage',args.stage]}
    report(summary,checks,manifest)
    manifest['outputs']={str(f.relative_to(BASE)):b.sha(f) for f in OUT.glob('*') if f.is_file() and f.name!='reproduction_manifest.json'}
    manifest['report_sha256']=b.sha(BASE/'修正结果报告.md')
    b.dump(OUT/'reproduction_manifest.json',manifest)
    b.log('COMPLETE',summary['new'],preservation)

if __name__=='__main__':main()
