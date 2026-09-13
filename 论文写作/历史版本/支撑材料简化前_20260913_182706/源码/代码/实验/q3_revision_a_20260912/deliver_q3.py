"""Export, independently reconcile Q3 transactions and prepare review artifacts."""
from pathlib import Path
import argparse,csv,json,sys
from copy import copy
from datetime import datetime
import numpy as np
import q3_engine as m
from run_q3 import POLICIES,dump


def csvout(path,headers,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)


def interval(t,end=None):
    if end is None:end=t+1
    return f'{t*10//60:02d}:{t*10%60:02d}-{end*10//60:02d}:{end*10%60:02d}'


def reconcile(arrays,initials,ledger,p,days,y,summary):
    errs={}
    for a,name in enumerate(POLICIES):
        A=arrays[a];flat=A.reshape(-1,7);g,c,b,e,w,before,after=flat.T
        net=(y[0]-y[1])[days].ravel()/6
        physical=max(float(abs(g+e+b-net-c-w).max()),float(abs(after-before-.9*c+b/.9).max()),float(abs(before[1:]-after[:-1]).max()))
        assert physical<1e-6
        assert before.min()>=1200-1e-6 and after.min()>=1200-1e-6 and before.max()<=10800+1e-6 and after.max()<=10800+1e-6
        assert max(c.max(),b.max())<=5000/6+1e-6 and np.minimum(c,b).max()<1e-6 and np.minimum(c,e).max()<1e-6
        assert flat[:,:5].min()>-1e-6
        own=ledger[ledger[:,0]==a]
        replay=initials[a].copy();cost=float(np.sum(initials[a]*p))
        for row in own:
            _,d,k,t,old,new,up,down,inc,refund,penalty=row
            i=int(d)-int(days[0]);t=int(t);k=int(k)
            assert t>=36*k and k in [1,2,3] and new>=-1e-7
            assert abs(replay[i,t]-old)<1e-7
            assert abs((new-old)-(up-down))<1e-7 and min(up,down)<1e-8
            assert abs(inc-1.5*p[t]*up)<1e-7 and abs(refund-p[t]*down)<1e-7 and abs(penalty-.5*p[t]*down)<1e-7
            cost+=inc-refund+penalty;replay[i,t]=new
        np.testing.assert_allclose(replay,A[:,:,0],atol=1e-7,rtol=0)
        cost+=float(5*np.sum(A[:,:,3]*p))
        error=abs(cost-summary[name]['total_cost']);assert error<1e-5,(name,error)
        errs[name]=dict(physical_max_kwh=physical,ledger_cost_error_yuan=error,ledger_rows=len(own),schedule_replay=True)
    return errs


def export(out,arrays,initials,ledger,p,days,y,summary):
    main=arrays[7];init=initials[7];own=ledger[ledger[:,0]==7];D=len(days)
    head=['date','slot','interval','initial_kwh','effective_kwh','charge_kwh','discharge_kwh','emergency_kwh','spill_kwh','start_kwh','end_kwh','price','net_kwh']
    rows=[[m.date(d),t+1,interval(t),float(init[i,t]),*main[i,t].tolist(),float(p[t]),float((y[0,d,t]-y[1,d,t])/6)] for i,d in enumerate(days) for t in range(144)]
    csvout(out/'main_intervals.csv',head,rows)
    ledger_head=['policy','date','issue_hour','slot','interval','old_kwh','new_kwh','increase_kwh','cancel_kwh','increase_cost','refund','penalty','net_adjustment_cost']
    ledger_rows=[[POLICIES[int(a)],m.date(d),int(k)*6,int(t)+1,interval(int(t)),old,new,up,down,inc,ref,pen,inc-ref+pen] for a,d,k,t,old,new,up,down,inc,ref,pen in ledger]
    csvout(out/'revision_ledger.csv',ledger_head,ledger_rows)
    # Preserve the four official worksheet objects and formatting, extend sample rows.
    wb=m.openpyxl.load_workbook(m.ROOT/'基础数据/result3.xlsx')
    for title,g in [('计划购电量',init),('调整购电量',main[:,:,0])]:
        ws=wb[title]
        for t in range(144):ws.cell(1,t+2,interval(t))
        for i,d in enumerate(days):
            ws.cell(i+2,1,datetime.fromisoformat(m.date(d)))
            for t,v in enumerate(g[i]):ws.cell(i+2,t+2,float(v))
            ws.cell(i+2,146,float(g[i].sum()))
            cost=float(init[i]@p)
            if title=='调整购电量':
                ll=own[own[:,1]==d];cost+=float((ll[:,8]-ll[:,9]+ll[:,10]).sum())
            ws.cell(i+2,147,cost)
    storage=[];events=[]
    for i,d in enumerate(days):
        for k in range(6):storage.append([m.date(d),f'{k*4:02d}:00-{(k+1)*4:02d}:00',float(main[i,k*24:(k+1)*24,1].sum()),float(main[i,k*24:(k+1)*24,2].sum()),'00:00' if k==0 else ('24:00' if k==1 else None),float(main[i,0,5]) if k==0 else (float(main[i,-1,6]) if k==1 else None)])
        t=0
        while t<144:
            if main[i,t,3]<=1e-8:t+=1;continue
            start=t
            while t<144 and main[i,t,3]>1e-8:t+=1
            events.append([m.date(d),interval(start,t),float(main[i,start:t,3].sum())])
    for name,rr in [('充放电量',storage),('紧急购电量',events)]:
        ws=wb[name]
        for row in ws.iter_rows(min_row=2):
            for cell in row:cell.value=None
        for i,row in enumerate(rr,2):
            for j,value in enumerate(row,1):ws.cell(i,j,value)
    ws=wb.create_sheet('调整逐笔账本');ws.append(ledger_head)
    for row in ledger_rows:
        if row[0]=='mask_111':ws.append(row)
    ws=wb.create_sheet('各次计划快照');ws.append(['日期','发布时间']+[interval(t) for t in range(144)])
    for i,d in enumerate(days):
        current=init[i].copy();ws.append([m.date(d),'00:00',*current.tolist()])
        for k in range(1,4):
            for row in own[(own[:,1]==d)&(own[:,2]==k)]:current[int(row[3])]=row[5]
            ws.append([m.date(d),f'{k*6:02d}:00',*current.tolist()])
    ws=wb.create_sheet('十分钟明细');ws.append(head)
    for row in rows:ws.append(row)
    daily=list(csv.DictReader((out/'daily_summary.csv').open(encoding='utf-8-sig')))
    ws=wb.create_sheet('每日费用');ws.append(list(daily[0]))
    for row in daily:
        if row['policy']=='mask_111':ws.append([v if key in ('policy','date') else float(v) for key,v in row.items()])
    specified=['2025-03-20','2025-06-21','2025-09-23','2025-12-21']
    table1=[];table2=[];table3=[]
    for ds in specified:
        d=(datetime.fromisoformat(ds)-datetime(2025,1,1)).days
        if d not in days:continue
        i=list(days).index(d);r=next(r for r in daily if r['policy']=='mask_111' and r['date']==ds)
        for t in [60,72,84,96,108,120]:table1.append([ds,interval(t),float(init[i,t]),float(main[i,t,0]),float(main[i,t,3])])
        table1.append([ds,'全天',float(init[i].sum()),float(main[i,:,0].sum()),float(main[i,:,3].sum())])
        table2.extend([rr for rr in storage if rr[0]==ds])
        ev=[rr for rr in events if rr[0]==ds];table3.extend(ev or [[ds,'无紧急购电',0.]])
    for name,headers,rr in [('指定日表1',['日期','区间','初始购电kWh','有效普通购电kWh','紧急购电kWh'],table1),('指定日表2',['日期','区间','充电kWh','放电kWh','时刻','库存kWh'],table2),('指定日表3',['日期','连续紧急时段','紧急购电kWh'],table3)]:
        ws=wb.create_sheet(name);ws.append(headers)
        for row in rr:ws.append(row)
        csvout(out/(name+'.csv'),headers,rr)
    ws=wb.create_sheet('说明');ws.append(['项目','口径'])
    for key,value in dict(method='新版Q2负载预测＋条件净误差分位＋调整LP候选＋DP评价和反馈执行',
                          settlement='每次对上一有效计划结算；增购1.5倍；撤销量退原价再缴0.5倍违约费。此为已确认建模解释。',
                          main='每天0、6、12、18时使用预报；候选包含不调整；不是事后最优组合',
                          adjusted_sheet='保存最终有效普通购电量；全天购电费=初始计划费+所有逐笔调整净费用，不含紧急费',
                          total_bill='每日费用表total_cost包含紧急费；不再对最终有效普通购电量重复收费',
                          time='输入标签为区间终点；输出副本首列改为00:00—00:10，末列23:50—24:00；原模板保留',
                          instantaneous_observation='当前十分钟功率可测且分段恒定；发布时计划不读取当期未来实测',
                          pv='小时整点线性插值至10分钟终点；发布点左锚为刚完成区间的观测近似；优化止于当日24:00',
                          state='1月1日6000kWh，完整1月共同预热后2月10800kWh；全年跨日连续',
                          terminals='日前LP与日内DP终端系数均固定0；未声称第三问调参得到最优0',
                          future='未来情景先取期望，下一次预报到来再修订；暂冻结未来交易的滚动近似',
                          source='复用Q2已验证的历史负载预测文件；本次未重新训练；Q3购电和运行轨迹全部新算',
                          status='真实计算结果供用户审核，未冻结为论文正文').items():ws.append([key,value])
    for ws in wb:
        ws.freeze_panes='B2';ws.auto_filter.ref=ws.dimensions
        ws.column_dimensions['A'].width=17
    wb.save(out/'result3.xlsx')
    # Independent re-read of actual XLSX/CSV output.
    wb=m.openpyxl.load_workbook(out/'result3.xlsx',read_only=True,data_only=True)
    rr=list(wb['计划购电量'].values);assert len(rr)==D+1
    np.testing.assert_allclose(np.array([r[1:145] for r in rr[1:]],float),init,rtol=0,atol=1e-8)
    rr=list(wb['调整购电量'].values)
    np.testing.assert_allclose(np.array([r[1:145] for r in rr[1:]],float),main[:,:,0],rtol=0,atol=1e-8)
    ordinary=sum(float(r[-1]) for r in rr[1:]);assert abs(ordinary+summary['mask_111']['emergency_cost']-summary['mask_111']['total_cost'])<1e-5
    rr=list(wb['充放电量'].values);assert len(rr)==D*6+1
    assert abs(sum(float(r[2]) for r in rr[1:])-float(main[:,:,1].sum()))<1e-5
    assert abs(sum(float(r[3]) for r in rr[1:])-float(main[:,:,2].sum()))<1e-5
    rr=list(wb['紧急购电量'].values)
    assert abs(sum(float(r[2] or 0) for r in rr[1:])-summary['mask_111']['emergency_kwh'])<1e-5
    assert wb['十分钟明细'].max_row==D*144+1
    wb.close()
    with (out/'main_intervals.csv').open(encoding='utf-8-sig') as f: rr=list(csv.DictReader(f))
    assert len(rr)==D*144
    emergency=sum(5*float(r['price'])*float(r['emergency_kwh']) for r in rr)
    assert abs(emergency-summary['mask_111']['emergency_cost'])<1e-5
    return dict(xlsx_readback=True,main_csv_readback=True,rows=D*144,merged_emergency_events=len(events),template_original_unchanged=True)


def sensitivity(out,y,p,pred,arrays,days):
    rows=[]
    for ds in ['2025-03-20','2025-06-21','2025-09-23','2025-12-21']:
        d=(datetime.fromisoformat(ds)-datetime(2025,1,1)).days
        if d not in days:continue
        i=list(days).index(d);E=arrays[7,i,0,5]
        for label,grid,atoms in [('nominal',m.GRID,7),('grid_30kwh',np.arange(1200,10801,30.),7),('atoms_15',m.GRID,15)]:
            models=[m.model_day(y,pred,d,k,atoms) for k in range(4)]
            run=m.day_run(y,p,pred,models,d,E,grid=grid)
            if label=='nominal':np.testing.assert_allclose(run['arr'],arrays[7,i],atol=1e-7,rtol=0)
            rows.append(dict(date=ds,setting=label,**m.summary_day(run,p)))
    csvout(out/'sensitivity.csv',list(rows[0]),[list(r.values()) for r in rows])
    return rows


def plots(out,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,'font.size':10})
    labels=['不更新','6时','12时','6＋12时','18时','6＋18时','12＋18时','全部','仅更新预报']
    total=np.array([summary[n]['total_cost'] for n in POLICIES])/1e4
    emer=np.array([summary[n]['emergency_cost'] for n in POLICIES])/1e4
    fig,ax=plt.subplots(figsize=(8,4));x=np.arange(9)
    ax.bar(x,total-emer,color='#4DBBD5',label='普通购电费用（含调整）')
    ax.bar(x,emer,bottom=total-emer,color='#E64B35',label='紧急购电费')
    ax.set_xticks(x,labels,rotation=25,ha='right');ax.set_ylabel('累计费用 / 万元');ax.legend(frameon=False,fontsize=9,loc='upper center',bbox_to_anchor=(.5,1.18),ncol=2)
    ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    fig.savefig(out/'预报组合费用.png',dpi=300);fig.savefig(out/'预报组合费用.svg');plt.close(fig)
    with (out/'daily_summary.csv').open(encoding='utf-8-sig') as f:rr=list(csv.DictReader(f))
    fig,ax=plt.subplots(figsize=(7,3.8))
    for key,label,color,style in [('mask_000','仅0时预报','#3C5488','-'),('mask_111','四次预报并调整','#E64B35','-'),('forecast_only','四次预报，仅调储能','#00A087','--')]:
        vals=[float(r['total_cost']) for r in rr if r['policy']==key]
        ax.plot(np.arange(1,len(vals)+1),np.cumsum(vals)/1e4,label=label,color=color,linestyle=style)
    ax.set_xlabel('2月1日起累计天数');ax.set_ylabel('累计费用 / 万元');ax.legend(frameon=False,fontsize=9)
    ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    fig.savefig(out/'累计费用.png',dpi=300);fig.savefig(out/'累计费用.svg');plt.close(fig)


def report(out,summary,checks,sens):
    main=summary['mask_111'];fixed=summary['mask_000'];fo=summary['forecast_only']
    q2=json.loads((m.Q2/'results/manifest.json').read_text(encoding='utf-8'))['summary']['main']
    names=['仅0时','0、6时','0、12时','0、6、12时','0、18时','0、6、18时','0、12、18时','四次预报并调整','四次预报、购电固定']
    text=['# 第三问路线A：真实回测结果审核','',
          '状态：计算与交付核验完成，等待用户审核结果；本文件是结果审核报告，未替代正式Word论文章节。','',
          '**结算前提：撤销量退还原价后缴50%违约费，增购按1.5倍，每次对上一有效计划逐笔结算。该解释已随路线A确认，属于建模口径，不是额外取得的官方释义。**','',
          '负载预测复用队友新版第二问的已验证前推结果；本次没有重新训练LightGBM。附件3各次PV预报、条件净误差、LP调整候选、DP及所有第三问实际调度重新计算。原题目、模板及所用第二问代码/结果哈希前后保持一致；第二问源码仅Git换行差异经LF归一核验。','',
          f"评价区间为2025年2月1日至12月31日，共{main['days']}天。主方案预先定义为四次使用预报，日内三次均可选择保持计划不变，并非事后选全年最优组合。主方案总费用 **{main['total_cost']:,.2f}元**，紧急购电 **{main['emergency_kwh']:,.2f}kWh**。",'',
          '| 费用项 | 金额/元 |','|---|---:|']
    for label,key in [('0时初始计划费','initial_cost'),('后续增购费（1.5倍）','increase_cost'),('撤销量退款（扣减）','cancellation_refund'),('撤销违约费（0.5倍）','cancellation_penalty'),('紧急购电费（5倍）','emergency_cost'),('合计','total_cost')]:text.append(f"| {label} | {main[key]:,.2f} |")
    text+=['',f"账单恒等式：初始费＋增购费−退款＋违约费＋紧急费。最终普通购电量为{main['effective_kwh']:,.2f}kWh，不能再乘原价重复记费。",'',
           '| 使用预报时刻 | 总费用/元 | 紧急费/元 | 紧急电量/kWh | 期末库存/kWh |','|---|---:|---:|---:|---:|']
    for name,label in zip(POLICIES,names):
        r=summary[name];text.append(f"| {label} | {r['total_cost']:,.2f} | {r['emergency_cost']:,.2f} | {r['emergency_kwh']:,.2f} | {r['end_kwh']:,.2f} |")
    text+=['','为直接回答是否增加其他预报时刻，以下在已使用另外两个日内时刻的基础上，计算增加剩余时刻后的费用变化。负数表示节省，正数表示增加费用。','',
           '| 新增调整时刻 | 原先日内时刻 | 费用变化/元 |','|---|---|---:|']
    for hour,base,label in [(6,'mask_110','12、18时'),(12,'mask_101','6、18时'),(18,'mask_011','6、12时')]:
        text.append(f"| {hour}:00 | {label} | {main['total_cost']-summary[base]['total_cost']:+,.2f} |")
    text+=['','在本次近似控制及结算口径下，12时和18时更新具有正的组合收益；在已使用12、18时的基础上增加6时，全年费用反而上升。此结论限定于本次数据和参数，不能写成6时预报在所有情况下都无用。','']
    delta=fixed['total_cost']-main['total_cost']
    best=min(POLICIES[:8],key=lambda n:summary[n]['total_cost'])
    text+=['',f"与同样利用附件3零点预报、全天固定购电的对照相比，对照费用减去主方案费用为{delta:,.2f}元，主方案相对费用变化为{-100*delta/fixed['total_cost']:+.4f}%。八个组合中样本期总费最低为“{names[POLICIES.index(best)]}”；这一排序是整段回测描述，不能当作事前知道的最优选择。",'',
           f"“更新预报但不改购电计划”的对照总费{fo['total_cost']:,.2f}元。它每天从自身实际日初库存制定计划，用于区分更新信息作用和允许交易的作用；长期差异还包含跨日库存导致的次日计划变化，不能全部归为某一次储能控制。",'',
           f"队友新版第二问总费{q2['total_cost']:,.2f}元。与第三问零点预报固定计划对照相比，差额为{q2['total_cost']-fixed['total_cost']:,.2f}元；该差额同时包含外部PV预报和相应净误差校准变化，不能全归因于日内调整。",'',
           '![各组合费用](预报组合费用.png)','',
           '图中普通购电费用已经合并增购、退款及违约费，紧急费用独立列出。对应数值见summary.json和逐日账单。','',
           '![累计费用](累计费用.png)','',
           '累计曲线只比较已定义的可执行策略；没有事后逐日选取最便宜策略。','',
           '## 指定日期与交付表','',
           '| 日期 | 初始费/元 | 调整净费用/元 | 紧急费/元 | 总费/元 | 日初/日末库存kWh |','|---|---:|---:|---:|---:|---|']
    with (out/'daily_summary.csv').open(encoding='utf-8-sig') as f:daily=list(csv.DictReader(f))
    for ds in ['2025-03-20','2025-06-21','2025-09-23','2025-12-21']:
        r=next(r for r in daily if r['policy']=='mask_111' and r['date']==ds)
        text.append(f"| {ds} | {float(r['initial_cost']):,.2f} | {float(r['adjustment_net']):,.2f} | {float(r['emergency_cost']):,.2f} | {float(r['total_cost']):,.2f} | {float(r['start_kwh']):.2f} / {float(r['end_kwh']):.2f} |")
    text+=['','result3.xlsx保留官方四张工作表并补齐全年数据，增加逐笔账本、四次计划快照、十分钟明细、费用表及指定日表。输入结束时标按用户已确认口径映射为00:00—00:10至23:50—24:00，原模板未改。紧急购电按连续时段合并。','',
           '## 已完成的验证与边界','',
           f"独立逐笔重放账本、物理约束及跨日连续通过，最大物理残差为{max(v['physical_max_kwh'] for v in checks['independent'].values()):.3e}kWh。CSV及Excel保存后回读一致。加速DP与原标量DP全网格对比、125元类内缺口反例、120元撤销再买回账单、发布时刻因果扰动及固定计划退化检查通过。",'',
           '| 日期 | 精度设置 | 总费/元 | 末库存/kWh |','|---|---|---:|---:|']
    for r in sens:text.append(f"| {r['date']} | {r['setting']} | {r['total_cost']:.4f} | {r['end_kwh']:.4f} |")
    deviations=[abs(r['total_cost']-next(x['total_cost'] for x in sens if x['date']==r['date'] and x['setting']=='nominal')) for r in sens]
    text+=['',f"四日精度变动下最大费用差为{max(deviations):,.2f}元；网格细化会改变个别调整候选和轨迹，因此尚不能宣称调度对离散精度不敏感。",'']
    text+=['','精度检查从主方案该日相同日初库存开始，重新优化该日；它只支持四个指定日的局部敏感性，不证明全年网格误差上界。','',
           '仍有明确近似：当前十分钟平均功率即时可测；整点PV线性插值；三状态一阶转移、类内7点压缩、60kWh价值网格；有限分位候选；当前评价暂不预知下一次交易；每日规划止于24:00且终端系数固定0。没有声称全局最优。既有全年数据参与过方法探索，本次也不是新的盲测集。','',
           '## 复现','',
           '在项目根目录，用已安装numpy、scipy、lightgbm及openpyxl的Python运行：','',
           '```powershell','python 代码/实验/q3_revision_a_20260912/run_q3.py --output 代码/实验/q3_revision_a_20260912/results_new',
           'python 代码/实验/q3_revision_a_20260912/deliver_q3.py --output 代码/实验/q3_revision_a_20260912/results_new','```','',
           'run_q3.py拒绝覆盖非空目录；中断后仅在代码、输入和参数完全一致时接受--resume。预测复用来源、输入和输出SHA256、运行命令、环境、耗时和验证记录见manifest.json与复现清单.json。','']
    report_dir=m.ROOT/'论文写作/问题三';report_dir.mkdir(parents=True,exist_ok=True)
    import os
    content='\n'.join(text)
    for image in ['预报组合费用.png','累计费用.png']:
        content=content.replace(']('+image+')',']('+Path(os.path.relpath(out/image,report_dir)).as_posix()+')')
    (report_dir/'第三问_路线A结果审核报告.md').write_text(content,encoding='utf-8')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=m.BASE/'results');args=ap.parse_args();out=args.output.resolve()
    with np.load(out/'solutions.npz') as z:arrays=z['arrays'];initials=z['initials'];ledger=z['ledger'];p=z['price'];days=z['day_indices']
    summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    y,price,load,f=m.load_inputs();np.testing.assert_array_equal(price,p)
    with np.load(out/'conditional_forecasts.npz') as z:pred=z['pred']
    independent=reconcile(arrays,initials,ledger,p,days,y,summary)
    delivery=export(out,arrays,initials,ledger,p,days,y,summary)
    sens=sensitivity(out,y,p,pred,arrays,days)
    plots(out,summary)
    checked=dict(independent=independent,delivery=delivery,sensitivity_days=4,visual_check='pending_manual_view')
    dump(out/'delivery_checks.json',checked);report(out,summary,checked,sens)
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    for path,digest in manifest['signature']['inputs'].items():assert m.sha(path)==digest
    manifest.update(status='numerically_verified_pending_visual_and_user_review',delivery_command=[sys.executable,str(Path(__file__).relative_to(m.ROOT)),*sys.argv[1:]],delivery_source_sha256=m.sha(__file__))
    report_path=m.ROOT/'论文写作/问题三/第三问_路线A结果审核报告.md'
    manifest['review_report']={'path':str(report_path),'sha256':m.sha(report_path)}
    manifest['output_hashes']={f.name:m.sha(f) for f in out.iterdir() if f.is_file() and f.name not in ['manifest.json','复现清单.json','checkpoint.npz','daily_checkpoint.json','scores_checkpoint.json']}
    dump(out/'manifest.json',manifest);dump(out/'复现清单.json',manifest)
    print(json.dumps(checked,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
