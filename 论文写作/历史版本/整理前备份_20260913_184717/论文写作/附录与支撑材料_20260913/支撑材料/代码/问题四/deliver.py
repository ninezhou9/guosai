"""Standalone tables/official-template export from independent run artifacts."""
import argparse
import csv
import json
import sys
from copy import copy
from pathlib import Path
from datetime import datetime
import numpy as np
import model as m

SPEC=['2025-03-20','2025-06-21','2025-09-23','2025-12-21']
OUT=m.BASE/'results'

def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)

def events(e):
    mask=e>1e-8; starts=np.flatnonzero(mask&~np.r_[False,mask[:-1]])
    ends=np.flatnonzero(mask&~np.r_[mask[1:],False])+1
    return [(int(a),int(b),float(e[a:b].sum())) for a,b in zip(starts,ends)]

def repeat_template_row(ws,target,style,height,values):
    for c,v in enumerate(values,1):
        cell=ws.cell(target,c,v); cell._style=copy(style[c-1])
    ws.row_dimensions[target].height=height

def template(tag,trajectory,daily):
    wb=m.openpyxl.load_workbook(m.DATA/f'result4-{tag}.xlsx')
    for sheet,col in [('计划购电量',0),('调整购电量',1)]:
        if sheet not in wb.sheetnames: continue
        ws=wb[sheet]
        for t in range(144): ws.cell(1,t+2,m.interval(t))
        for i,r in enumerate(trajectory):
            dt=datetime.fromisoformat(m.date(i+31)); d=daily[m.date(i+31)]
            amount=r[:,col]; cost=d['initial_cost']+(d['adjustment_net'] if col==1 else 0)
            vals=[dt,*map(float,amount),float(amount.sum()),cost]
            for j,v in enumerate(vals,1): ws.cell(i+2,j,v)
    ws=wb['充放电量']
    styles=[[copy(ws.cell(r,c)._style) for c in range(1,7)] for r in range(2,8)]
    heights=[ws.row_dimensions[r].height for r in range(2,8)]
    ws.delete_rows(2,ws.max_row-1)
    for i,day in enumerate(trajectory):
        for block in range(6):
            vals=[datetime.fromisoformat(m.date(i+31)) if block==0 else None,
                  m.interval(block*24,(block+1)*24),float(day[block*24:(block+1)*24,2].sum()),
                  float(day[block*24:(block+1)*24,3].sum()),
                  '00:00' if block==0 else '24:00' if block==1 else None,
                  float(day[0,6]) if block==0 else float(day[-1,7]) if block==1 else None]
            repeat_template_row(ws,2+i*6+block,styles[block],heights[block],vals)
    ws=wb['紧急购电量']
    styles=[[copy(ws.cell(r,c)._style) for c in range(1,4)] for r in range(2,5)]
    heights=[ws.row_dimensions[r].height for r in range(2,5)]
    ws.delete_rows(2,ws.max_row-1); row=2
    for i,day in enumerate(trajectory):
        ev=events(day[:,4]); ev=ev or [(None,None,0.)]
        for j,(a,b,q) in enumerate(ev):
            pattern=0 if j==0 else 2 if j==len(ev)-1 else 1
            vals=[datetime.fromisoformat(m.date(i+31)) if j==0 else None,m.interval(a,b) if a is not None else '无',q]
            repeat_template_row(ws,row,styles[pattern],heights[pattern],vals); row+=1
    wb.save(OUT/f'result4-{tag}.xlsx'); wb.close()

def sensitivity():
    with np.load(OUT/'features.npz') as z: f={k:z[k] for k in z.files}
    with np.load(OUT/'trajectories.npz') as z: main=z['A43_111']
    rows=[]
    for ds in SPEC:
        d=(datetime.fromisoformat(ds)-datetime(2025,1,1)).days; energy=float(main[d-31,0,6]); base=None
        for step,atoms in [(60,7),(30,7),(60,15)]:
            r=m.simulate(f,d,energy,grid_step=step,atoms=atoms)
            costs=m.costs(r)
            if base is None: base=costs['total_cost']
            rows.append(dict(date=ds,grid_step=step,atoms=atoms,**costs,delta_cost=costs['total_cost']-base))
            print(ds,step,atoms,round(costs['total_cost'],6),flush=True)
    write_csv(OUT/'sensitivity.csv',rows)

def tables():
    with np.load(OUT/'trajectories.npz') as z: trajectories={n:z[n] for n in ['A42','A43_111']}
    with (OUT/'daily_costs.csv').open(encoding='utf-8-sig') as f:
        daily={}
        for r in csv.DictReader(f): daily.setdefault(r['strategy'],{})[r['date']]={k:float(v) for k,v in r.items() if k not in ['strategy','date']}
    tab1=[];tab2=[];tab3=[]
    for tag,name in [('2','A42'),('3','A43_111')]:
        template(tag,trajectories[name],daily[name])
        for ds in SPEC:
            i=(datetime.fromisoformat(ds)-datetime(2025,2,1)).days; day=trajectories[name][i]
            for hour in [10,12,14,16,18,20]:
                t=hour*6
                tab1.append(dict(strategy=name,date=ds,interval=m.interval(t),initial_kwh=day[t,0],ordinary_kwh=day[t,1],
                    initial_daily_kwh=day[:,0].sum(),ordinary_daily_kwh=day[:,1].sum(),total_cost=daily[name][ds]['total_cost']))
            for block in range(6):
                tab2.append(dict(strategy=name,date=ds,interval=m.interval(block*24,(block+1)*24),
                    charge_kwh=day[block*24:(block+1)*24,2].sum(),discharge_kwh=day[block*24:(block+1)*24,3].sum(),
                    E_start=day[0,6],E_end=day[-1,7]))
            for a,b,q in events(day[:,4]) or [(None,None,0.)]:
                tab3.append(dict(strategy=name,date=ds,interval=m.interval(a,b) if a is not None else '无',emergency_kwh=q))
    for n,rows in [(1,tab1),(2,tab2),(3,tab3)]: write_csv(OUT/f'specified_table{n}.csv',rows)
    # Price prediction diagnostics and information cutoffs are generated from new features.
    with np.load(OUT/'features.npz') as z:
        metrics=[]; trace=[]
        for k in range(4):
            diff=z['ph'][31:,k,36*k:]-z['price'][31:,36*k:]
            metrics.append(dict(issue_hour=6*k,mae=float(np.abs(diff).mean()),rmse=float(np.sqrt((diff**2).mean()))))
            for d in range(31,365): trace.append(dict(date=m.date(d),issue_hour=6*k,first_delivery_slot=36*k,
                last_observed_slot=36*k-1,history_first_day=max(18,d-30),history_last_day=d-1))
        write_csv(OUT/'price_metrics.csv',metrics); write_csv(OUT/'information_cutoffs.csv',trace)

def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.sans-serif':['Microsoft YaHei'],'axes.unicode_minus':False,'font.size':10,'savefig.dpi':300})
    figdir=m.BASE/'figures'; figdir.mkdir(exist_ok=True)
    annual=json.loads((OUT/'annual.json').read_text(encoding='utf-8'))['strategies']
    with (OUT/'daily_costs.csv').open(encoding='utf-8-sig') as f: daily=list(csv.DictReader(f))
    names=['A42','B42','A43_111','B43']; palette=['#0072B2','#56B4E9','#D55E00','#E69F00']
    fig,ax=plt.subplots(figsize=(7.5,4.3),layout='constrained')
    for n,c,ls in zip(names,palette,['-','--','-','--']):
        vals=np.array([float(r['total_cost']) for r in daily if r['strategy']==n])
        ax.plot(np.arange(1,335),np.cumsum(vals)/1e6,color=c,linestyle=ls,label=n)
    ax.set(xlabel='正式期天数',ylabel='累计购电费用 / 百万元'); ax.legend(); ax.grid(alpha=.2)
    fig.savefig(figdir/'cumulative_cost.png'); fig.savefig(figdir/'cumulative_cost.svg'); plt.close(fig)
    masks=[f'A43_{i:03b}' for i in range(8)]
    fig,ax=plt.subplots(figsize=(7.5,4.3),layout='constrained')
    ax.bar([n[-3:] for n in masks],[annual[n]['total_cost']/1e6 for n in masks],color=['#D55E00' if n.endswith('111') else '#0072B2' for n in masks])
    ax.set(xlabel='06/12/18 时更新组合（最低位为06时）',ylabel='总购电费用 / 百万元'); ax.grid(axis='y',alpha=.2)
    fig.savefig(figdir/'mask_costs.png'); fig.savefig(figdir/'mask_costs.svg'); plt.close(fig)
    with np.load(OUT/'trajectories.npz') as z: a=z['A43_111']
    peak=max(a[(datetime.fromisoformat(ds)-datetime(2025,2,1)).days,:,4].max() for ds in SPEC)
    fig,axes=plt.subplots(2,2,figsize=(9,6),layout='constrained')
    for ds,ax in zip(SPEC,axes.ravel()):
        i=(datetime.fromisoformat(ds)-datetime(2025,2,1)).days; day=a[i]
        ax.plot(np.arange(145)/6,np.r_[day[0,6],day[:,7]],color='#0072B2',label=ds)
        ax2=ax.twinx(); plotted=np.where(day[:,4]>1e-8,day[:,4],0)
        ax2.bar((np.arange(144)+.5)/6,plotted,width=1/6,color='#D55E00',alpha=.4)
        ax2.set_ylim(0,max(1,float(peak)*1.1))
        ax.set(xlabel='时刻 / h',ylabel='储电量 / kWh',xlim=(0,24),ylim=(1000,11000)); ax2.set_ylabel('紧急购电 / kWh')
        ax.legend(fontsize=9,loc='upper right'); ax.grid(alpha=.2)
    fig.savefig(figdir/'specified_soc.png'); fig.savefig(figdir/'specified_soc.svg'); plt.close(fig)

def report():
    a=json.loads((OUT/'annual.json').read_text(encoding='utf-8')); checks=json.loads((OUT/'audit.json').read_text(encoding='utf-8')) if (OUT/'audit.json').exists() else None
    unit=json.loads((m.BASE/'tests/unit_checks.json').read_text(encoding='utf-8'))
    s=a['strategies']; main=s['A43_111']; fixed=s['A42']; upd=s['A43_update_only']
    lines=['# 第四问 A：独立实现计算报告','',
        '依据已确认的《第四问A_编程实施方案》独立编写；本轮未重新读取、复制、导入或执行 DS 的第四问代码。',
        '只复用经哈希核验的 Q2/Q3 预测缓存；价格预测、联合误差模型、LP、DP、所有第四问决策和账本均重新计算。新预测模型训练次数为 0。',
        '本目录结果供用户审核，尚未冻结为论文结论。','',
        f'正式评价：{a["days"]} 天，每策略 {a["days"]*144} 个区间；1 月从 6000 kWh 连续暖启动。',
        '原始 00:10 列按已确认约定代表 00:00—00:10，输出模板对应改为开始—结束时段。','',
        '| 策略 | 初始计划费/元 | 调整净费/元 | 紧急费/元 | 总费/元 | 紧急电量/kWh | 期末库存/kWh |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for n,v in s.items():
        lines.append(f'| {n} | {v["initial_cost"]:,.2f} | {v["adjustment_net"]:,.2f} | {v["emergency_cost"]:,.2f} | {v["total_cost"]:,.2f} | {v["emergency_kwh"]:,.2f} | {v["E_end"]:,.2f} |')
    lines+=['',f'4-2 主结果为 {fixed["total_cost"]:,.2f} 元；4-3 主结果为 {main["total_cost"]:,.2f} 元。',
        f'在同样更新预测的条件下，开放调整相对 update_only 减少费用 {upd["total_cost"]-main["total_cost"]:,.2f} 元（{100*(upd["total_cost"]-main["total_cost"])/upd["total_cost"]:.3f}%）。',
        f'八种组合中本次最低为 {min((n for n in s if n.startswith("A43_") and n[-3:].isdigit()),key=lambda n:s[n]["total_cost"])}。主结果事先指定 111，未按全年结果回选。','',
        f'单元与因果检查 {unit["passed"]}/{unit["total"]} 通过。',
        f'独立全年与交付审核：{checks["passed"]}/{checks["total"]} 通过。' if checks else '独立全年与交付审核：待执行。','',
        '费用使用交付区间真实价；调整逐笔计算增购1.5倍、退款1倍与违约0.5倍，紧急购电5倍。调整表全天购电费含初始计划费与调整净费，不含紧急费；不得再加一次计划表费用。',
        '所有 LP 为预测候选生成器，实际电池动作由反馈 DP 执行；无强制日末回到6000条件。','',
        '局限：80分位 LP、60 kWh 网格、7个历史代表及零终端价值均为固定近似；当前窗口不优化未来尚未到达的发布和调整机会。A/B 同时改变价格结构与状态近似，不能把全部差值归因于相关性。各策略库存不同，费用比较应结合期末库存。',
        '四日敏感性明细见 results/sensitivity.csv，只反映四日局部变化，不能据此断言全年精度。','',
        '图1：主策略累计费用（figures/cumulative_cost.png）。图2：八组合总费用（figures/mask_costs.png）。图3：指定日期SOC与紧急购电（figures/specified_soc.png）。',
        '指定日期表1/2/3分别见 results/specified_table1.csv、specified_table2.csv、specified_table3.csv。',
        '静态重计价对照见 results/static_repricing.csv；它保留 Q2/Q3 原有数量，不属于第四问重新优化。','',
        '复现顺序：python -X utf8 test_model.py → python -X utf8 run.py --jobs 9 → python -X utf8 deliver.py --sensitivity → python -X utf8 audit.py。',
        '全新运行要求 results 不存在或为空；中断时使用 --resume，仅接受输入/源码/参数/策略签名一致的完整检查点。']
    warm=np.load(OUT/'warmup.npy')
    lines+=['',f'1 月暖启动实际费用 {np.sum(warm[:,:,9]*(warm[:,:,0]+5*warm[:,:,4])):,.2f} 元，单独记录，不计入上述 2—12 月费用。']
    recovery=m.BASE/'tests/recovery_checks.json'
    if recovery.exists():
        rr=json.loads(recovery.read_text(encoding='utf-8'))
        lines.append(f'运行恢复与输出保护检查 {rr["passed"]}/{rr["total"]} 通过；实际续跑前两天轨迹与连续运行逐数组一致。')
    q3=json.loads((m.Q3/'summary.json').read_text(encoding='utf-8'))
    rank3=sorted([n for n in q3 if n.startswith('mask_')],key=lambda n:q3[n]['total_cost'])
    rank4=sorted([n for n in s if n.startswith('A43_') and n[-3:].isdigit()],key=lambda n:s[n]['total_cost'])
    lines+=['','第三问组合排序：'+', '.join(n[-3:] for n in rank3)+'。',
            '第四问组合排序：'+', '.join(n[-3:] for n in rank4)+'。仅比较排序，两问费用结算价不同。',
            'adjust_only 为扩展诊断：不更新预测时，将原模型的状态先验沿转移矩阵推进到当前窗口，再评价剩余计划；它不是必跑的4-3八组合之一。']
    lines.append('SOC图中紧急购电小于等于1e-8 kWh的浮点噪声仅在绘图时隐藏，四幅图采用相同紧急电量纵轴；原始数量与账本未舍弃。')
    (m.BASE/'独立计算报告.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def manifest():
    outputs={str(p.relative_to(m.BASE)):m.digest(p) for folder in [OUT,m.BASE/'figures',m.BASE/'tests'] for p in folder.glob('*') if p.is_file() and p.name not in ['manifest.json','复现清单.json']}
    outputs['独立计算报告.md']=m.digest(m.BASE/'独立计算报告.md')
    data=dict(inputs=m.provenance(),sources={p.name:m.digest(p) for p in m.BASE.glob('*.py')},outputs=outputs,
              parameters=m.PARAMS,reused_forecasts=True,new_model_fits=0,independent_from_prior_q4=True,
              seed=20260912,seed_purpose='randomized mathematical tests; solver/model compression deterministic',
              run=json.loads((OUT/'run_record.json').read_text(encoding='utf-8')),status='computed_pending_user_review',
              reproduction='python -X utf8 test_model.py; python -X utf8 run.py --jobs 9; python -X utf8 deliver.py --sensitivity; python -X utf8 audit.py')
    for n in ['manifest.json','复现清单.json']: (OUT/n).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--sensitivity',action='store_true'); args=parser.parse_args()
    assert json.loads((OUT/'annual.json').read_text(encoding='utf-8'))['days']==334
    if args.sensitivity: sensitivity()
    tables(); figures(); report(); manifest()
    print('Exported official templates, figures, tables, report and provenance manifest.')

if __name__=='__main__': main()
