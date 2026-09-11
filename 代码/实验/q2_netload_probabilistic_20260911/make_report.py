"""Read actual experiment outputs and produce a traceable Chinese report."""
from pathlib import Path
import json, csv, hashlib
import numpy as np

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'results'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    s=read(OUT/'summary.json');v=read(OUT/'validation.json');f=read(OUT/'forecast_selection.json')
    k=read(OUT/'controller_selection.json');protect=read(OUT/'original_file_preservation.json')
    manifest=read(OUT/'reproduction_manifest.json');new=s['new'];old=s['old_summary_readonly']
    lines=['# 第二问独立实验结果（待审核）','',
        '统计范围：2025 年 2 月 1 日—12 月 31 日，334 天、48096 个十分钟时段。以下数字全部来自本目录真实输出；未引用新上传论文的数值作为实验结果。','',
        '## 实际费用与紧急购电','',
        '| 方案 | 计划费用（元） | 紧急费用（元） | 总费用（元） | 紧急购电量（kWh） |',
        '|---|---:|---:|---:|---:|']
    labels={'main':'概率候选购电＋随机控制','median_only':'仅中位数购电＋随机控制','greedy_same_plan':'相同计划＋贪心控制'}
    for name,r in new.items():lines.append(f"| {labels[name]} | {r['normal_cost']:,.2f} | {r['emergency_cost']:,.2f} | {r['total_cost']:,.2f} | {r['emergency_kWh']:,.2f} |")
    for name in ['neutral','risk']:
        r=old[name];lines.append(f"| 旧{'风险中性' if name=='neutral' else 'CVaR'}方案（只读旧输出） | {r['normal_cost_yuan']:,.2f} | {r['emergency_cost_yuan']:,.2f} | {r['total_cost_yuan']:,.2f} | {r['emergency_kWh']:,.2f} |")
    lines+=['','旧方案与新方案同时改变了预测、候选购电与实际控制，年度差额不能全部归因于某一个模块。两项消融帮助判断本实验中概率计划与控制的贡献；贪心对照使用完全相同的全天购电计划，但储电量按自身执行连续衔接。','']
    comparisons={}
    for name in ['neutral','risk']:
        r=old[name];m=new['main'];dc=r['total_cost_yuan']-m['total_cost'];de=r['emergency_kWh']-m['emergency_kWh']
        comparisons[name]={'cost_reduction_yuan':dc,'cost_reduction_percent':100*dc/r['total_cost_yuan'],
            'emergency_reduction_kWh':de,'emergency_reduction_percent':100*de/r['emergency_kWh']}
        lines.append(f"- 相对旧{name}：总费用变化 {(m['total_cost']/r['total_cost_yuan']-1)*100:+.4f}%，紧急购电量变化 {(m['emergency_kWh']/r['emergency_kWh']-1)*100:+.4f}%。")
    for name in ['median_only','greedy_same_plan']:
        r=new[name];lines.append(f"- 主方案相对{labels[name]}：总费用变化 {(new['main']['total_cost']/r['total_cost']-1)*100:+.4f}%。")
    lines+=['','## 库存及可比性','', '| 方案 | 2月1日日初电量（kWh） | 12月31日日末电量（kWh） |','|---|---:|---:|']
    for name,r in new.items():lines.append(f"| {labels[name]} | {r['E_start']:,.6f} | {r['E_end']:,.6f} |")
    for name in ['neutral','risk']:
        r=old[name];lines.append(f"| 旧{name} | {r['start_soc_kWh']:,.6f} | {r['end_soc_kWh']:,.6f} |")
    lines+=['','原始费用不做库存改写。为检查库存差异的量级，额外以同一个 κ 对库存消耗计价：C_adj=C+κ(E_start−E_end)。这只是敏感性口径，并非题目实际账单。','']
    adjusted={name:r['total_cost']+s['kappa']*(r['E_start']-r['E_end']) for name,r in new.items()}
    for name in ['neutral','risk']:
        r=old[name];adjusted['old_'+name]=r['total_cost_yuan']+s['kappa']*(r['start_soc_kWh']-r['end_soc_kWh'])
    for name,value in adjusted.items():lines.append(f'- {name}：库存调整费用 {value:,.2f} 元。')
    lines+=['','## 预测与参数选择','',f"1 月 15—21 日净负荷 MAE：直接预测 {f['direct_MAE']:.6f} kW，分别预测后相减 {f['separate_MAE']:.6f} kW；1 月 22 日冻结为 `{f['family']}`。此前历史预测和残差不回写。",'',
        f"2—12 月净负荷中位数预测 MAE={s['forecast']['net_MAE_kW']:.6f} kW，RMSE={s['forecast']['net_RMSE_kW']:.6f} kW。",'',
        '| 分位数 | 实际不超过该预测的比例 | 平均 pinball 损失（kW） |','|---|---:|---:|']
    for r in s['forecast']['quantiles']:lines.append(f"| {r['quantile']:.2f} | {r['observed_fraction_below']:.4%} | {r['pinball_kW']:.6f} |")
    lines+=['','分位数有无校准偏差应以上述覆盖率为准，不能因为使用了校准算法就声明覆盖率达标。','', '| κ | 1月22—31日实际费用（元） | 紧急电量（kWh） |','|---|---:|---:|']
    for r in k['candidates']:lines.append(f"| {r['kappa']:.9f} | {r['cost']:,.2f} | {r['emergency_kWh']:,.2f} |")
    lines+=['',f"冻结参数 κ={s['kappa']:.9f}，不在全年回测后修改。κ 只进入规划终端价值，未计入实际交易费用。",'']
    counts={}
    for file in sorted((OUT/'days').glob('*.json')):
        label=read(file)['chosen_candidate'];counts[label]=counts.get(label,0)+1
    lines+=['实际选中计划候选的天数：'+json.dumps(counts,ensure_ascii=False)+'。','',
        '## 四个指定日期','', '| 日期 | 计划费用（元） | 紧急费用（元） | 总费用（元） | 紧急电量（kWh） |','|---|---:|---:|---:|---:|']
    specified=[]
    with (OUT/'daily_metrics.csv').open(encoding='utf-8-sig',newline='') as fh:
        for r in csv.DictReader(fh):
            if r['策略']=='main' and r['日期'] in ['2025-03-20','2025-06-21','2025-09-23','2025-12-21']:
                specified.append(r);lines.append('| '+r['日期']+' | '+' | '.join(f'{float(r[x]):,.2f}' for x in ['计划费用_元','紧急费用_元','总费用_元','紧急电量_kWh'])+' |')
    lines+=['','## 验证','',f"- 全部三策略、各 48096 时段物理核验通过；最大约束残差 {max(max(r.values()) for r in v['physical'].values()):.3e} kWh。",
        '- 因果性回归测试：改变当日后半天实际数据，前 72 步动作逐值不变；改变当日及未来日期的实际数据，日前特征、历史概率模型和购电计划不变。',
        f"- Bellman 网格算子 {v['algorithm']['grid_operator_cases']} 个动作核验，最大差异 {v['algorithm']['max_error']:.3e}；检查选择当前动作前先对未知下一状态取期望。",
        f"- Excel 重读 {v['xlsx_readback']['rows']} 行，计划费用、紧急费用及紧急购电量与原始数组一致。",'',
        '| 网格精度抽查日期 | 60kWh网格费用（元） | 30kWh网格费用（元） | 最大单步储电量差（kWh） |','|---|---:|---:|---:|']
    for r in v['grid_refinement']:lines.append(f"| {r['date']} | {r['cost_grid60']:,.4f} | {r['cost_grid30']:,.4f} | {r['max_step_E_difference']:.6f} |")
    lines+=['','网格精度检查固定该日购电计划和期初电量，仅比较控制精度，不能把四天抽查写成全年网格收敛证明。','',
        f"原文件保护复核数量：{protect['checked_files']}。变化或缺失：{json.dumps(protect['changed_or_missing'],ensure_ascii=False)}。",
        '保护清单不含 git 内部、Skill 元数据、旧依赖和 Python 缓存；新实验目录不属于原文件。','',
        '## 图与数据','',
        '下图比较三策略累计账单，所有曲线由完整逐时结果求和生成。','',
        f"![三策略累计费用]({(BASE/'figures/累计费用对照.png').as_posix()})",'',
        '图1：三策略累计实际购电费用。年度总费用差异见前表；曲线用于观察差异积累过程。','',
        '下图展示指定日期 3 月 20 日概率预测与真实净负荷。区间越宽表示预测分布越不确定，不表示必然能覆盖真实值。','',
        f"![3月20日概率预测]({(BASE/'figures/3月20日概率预测.png').as_posix()})",'',
        '图2：3月20日净负荷及 q20—q80 预测区间。全年覆盖率见前表，不能从单日图判断全年概率质量。','',
        '## 方法边界与完成状态','',
        '- 这次使用有限候选计划选择和三状态 Markov 动态规划；没有声称求出完整随机混合整数模型的全局最优。',
        '- 第一阶离散误差状态、代表值及价值网格属于近似。实际储电量不取整；当前误差类别用于条件更新下一步分布。',
        '- 实际紧急购电只补负荷，不用于主动充电；因此与允许紧急充电的控制模型存在策略范围差别。',
        '- 沿用用户确认的结束时间标签。审核工作簿不覆盖、不冒充官方开始标签模板。',
        '- 全年回测严格按历史信息执行，但方案设计已参考此前对本数据集的观察，不是从未接触的全新盲测。',
        '- 本轮只执行代码试算，不写入或覆盖论文；结果待用户审核，尚未冻结。','',
        '实际读取 Skill：统一入口、逐步审核、交付合同、编程手、CUMCM/C题规则、质量门禁、Excel工具、可视化规范。','',
        '实际关键命令：','',
        '```powershell',
        "& 'C:/Program Files/Python313/python.exe' '代码/实验/q2_netload_probabilistic_20260911/run_experiment.py' --stage smoke",
        "$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'",
        "& 'C:/Program Files/Python313/python.exe' '代码/实验/q2_netload_probabilistic_20260911/run_experiment.py' --stage all",
        "& 'C:/Program Files/Python313/python.exe' -X utf8 '代码/实验/q2_netload_probabilistic_20260911/make_report.py'",
        '```','',
        f"主程序记录状态 `{manifest['status']}`，本次记录运行时间 {manifest['seconds']:.2f} 秒；shell 退出码见对应运行记录。首次默认 GBK 读取中文缓存失败已通过 UTF-8 运行模式解决。",'']
    (BASE/'实验结果报告.md').write_text('\n'.join(lines),encoding='utf-8')
    write(OUT/'comparison.json',{'old_comparison':comparisons,'inventory_adjusted_costs':adjusted,'candidate_days':counts,'specified_days':specified})
    write(OUT/'report_manifest.json',{'report_script_sha256':sha(__file__),'inputs':{name:sha(OUT/name) for name in ['summary.json','validation.json','controller_selection.json','forecast_selection.json']},
        'report_sha256':sha(BASE/'实验结果报告.md'),'comparison_sha256':sha(OUT/'comparison.json'),
        'command':'Python313/python.exe -X utf8 make_report.py','status':'generated from actual output'})
    print(json.dumps({'main':new['main'],'comparisons':comparisons,'preservation':protect},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
