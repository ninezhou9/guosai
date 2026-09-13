"""Publish verified result files, preserving unrelated support-package contents."""
from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,sys,zipfile

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'代码/结果导出/缓存'
PACKAGE=ROOT/'论文写作/附录与支撑材料_20260913'
DELIVERY=ROOT/'代码/交付整理/缓存/支撑材料/结果'
RECORDS=ROOT/'代码/交付整理/缓存/核验/原模板回填'
NAMES=['result1.xlsx','result2.xlsx','result3.xlsx','result4-2.xlsx','result4-3.xlsx']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report=json.loads((WORK/'verification.json').read_text(encoding='utf-8'))
    boundary=json.loads((WORK/'boundary_prediction.json').read_text(encoding='utf-8'))
    assert report['status']=='complete_with_authorized_boundary_assumptions'
    expected={r['file']:r['sha256'] for r in report['verified']}
    assert set(expected)==set(NAMES) and not report['waiting']
    for name in NAMES:assert sha(WORK/'filled'/name)==expected[name]
    archive=PACKAGE/'支撑材料.zip'
    archive_hash=sha(archive)
    backup=WORK/('更新交付前备份_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    targets=[archive]+[DELIVERY/n for n in NAMES]
    # Check every resolved target before any copy or replacement.
    assert all(p.resolve().is_relative_to(ROOT.resolve()) for p in targets+[backup])
    assert not backup.exists()
    backup.mkdir(parents=True)
    before={str(p):sha(p) for p in targets if p.exists()}
    for p in targets:
        if p.exists():
            saved=backup/p.relative_to(ROOT)
            saved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,saved)
            assert sha(saved)==before[str(p)]
    replacements={'结果/'+n:WORK/'filled'/n for n in NAMES}
    staging=WORK/'支撑材料_结果更新暂存.zip'
    untouched={}
    with zipfile.ZipFile(archive) as old,zipfile.ZipFile(staging,'w') as new:
        old_names=old.namelist()
        assert len(old_names)==len(set(old_names))
        assert all(k in old_names for k in replacements)
        new.comment=old.comment
        for info in old.infolist():
            if info.filename in replacements:
                data=replacements[info.filename].read_bytes()
            else:
                data=old.read(info.filename)
                untouched[info.filename]=hashlib.sha256(data).hexdigest()
            new.writestr(info,data)
    with zipfile.ZipFile(staging) as new:
        assert new.namelist()==old_names
        assert new.testzip() is None
        for name,value in untouched.items():assert hashlib.sha256(new.read(name)).hexdigest()==value
        for name in NAMES:assert hashlib.sha256(new.read('结果/'+name)).hexdigest()==expected[name]
    # Do not overwrite another editor's changes made while preparing the ZIP.
    assert sha(archive)==archive_hash
    for p in targets:
        if str(p) in before:assert sha(p)==before[str(p)],('Changed concurrently',p)
    for name in NAMES:
        for folder in [DELIVERY]:
            target=folder/name
            if not target.exists() or sha(target)!=expected[name]:shutil.copy2(WORK/'filled'/name,target)
            assert sha(target)==expected[name]
    staging.replace(archive)
    RECORDS.mkdir(parents=True,exist_ok=True)
    (RECORDS/'核验记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (RECORDS/'年末预测记录.json').write_text(json.dumps(boundary,ensure_ascii=False,indent=2),encoding='utf-8')
    count=sum(r['cells_compared'] for r in report['verified'])
    note=f'''原模板重填与跨日延拓说明

五份结果均已完成并核对：result1.xlsx、result2.xlsx、result3.xlsx、result4-2.xlsx、result4-3.xlsx。
已同步支撑材料中的五份结果，以及支撑材料.zip中的同名五个条目。压缩包的其他条目保持不变。

一、时间对应
按用户指定，输入标签为十分钟区间的结束时刻：0:10对应00:00—00:10，0:20对应00:10—00:20。
原模板的时间文字不变：第一段00:10—00:20取原模型第二段；末段取次日00:00—00:10的计划。原模板工作表、日期和表头均保留；调整购电表的两列全天合计适当加宽，以完整显示数字。

二、新增且获用户允许的跨日假设
第一问：电价和负载按题设每日重复；新增假设为给定的一天光伏预测曲线再延续一个日周期。实际调用原q1_solution.solve重新求解次日计划，期初储电量接上当天末值{boundary['q1']['previous_day_end_kwh']:.4f} kWh，次日首段为{boundary['q1']['first_slot_kwh']:.10f} kWh。此值与当天首段相同，源于重复预测曲线及相同储能边界；它是延拓假设下的计算结果，不能称为独立取得的次日气象预报。
第二问及4-2：沿用先前原预测函数、原校准及原优化函数补算2026年1月1日，首段为{boundary['first_slot_kwh']:.10f} kWh。未改变原预测或优化方法。
第三问及4-3：在2026年1月1日零点沿用2025年12月31日18点发布的预报，覆盖次日1—18点；缺少的19—24点采用此前7天零点发布的同一时刻预报的均值延拓。这六个夜间均值由数据计算得到，恰好均为0。随后调用原光伏插值、历史残差校准和优化函数，次日首段为{boundary['q3']['first_slot_kwh']:.10f} kWh。构造的延拓预报不是附件中真实发布的新预报，没有使用或补造2026年实际观测。
第三问和4-3的调整购电表末段取次日首段计划；该首段早于次日首次日内调整，故与次日初始计划相同。

三、合计与信息时点
购电表的全天购电量、费用按模板展示的00:10—次日00:10窗口重算。充放电和紧急购电仍按各自模板指定的自然日时段统计。原论文全年费用对应自然日窗口，不能与平移十分钟后的表内合计直接混用，本次未修改论文数字。
各行末段接入的是次日零点模型产生的计划，不表述为前一天零点已知的决策。第一问使用无具体日期的日周期延拓。
4-2和4-3的2026年1月1日首段费用采用原七日均值方法得到的预测电价{boundary['q42']['forecast_price'][0]:.10f}元/kWh，不是缺失的2026年实际成交电价。

四、验证与复现
{count}个填入单元格全部读回核对，最大绝对误差为0；时间标签、日期顺序及工作表名与原模板一致。原模型源码和输入文件哈希未变。已查看代表性首末区间与新填工作表的渲染；第一问跨日衔接残差为0，第三问历史重现和补算日期校准误差为0。
只补算所需跨日计划，没有重跑原全年实际调度。新增假设只用于边界，不将预测值冒充实际观测。
计算入口：代码/结果导出/boundary_prediction.py，执行顺序forecast、q4、q1、q3；之后运行prepare_templates.py、refill_templates.mjs fill、verify_templates.py、publish_results.py。
计算运行时为本机Python313；Excel读写与渲染使用Codex内置Python和Node运行时。原第二问清单记录的E盘Anaconda现已不存在，补算未修改全局环境。
实际运行及数值明细见年末预测记录.json与核验记录.json。此说明和补算记录位于本目录，支撑材料.zip本次仅替换五份答案。
'''
    (RECORDS/'请先阅读_重填状态.txt').write_text(note,encoding='utf-8')
    publication=dict(status='complete',output_hashes=expected,backup_directory=str(backup),
        archive_sha256=sha(archive),archive_result_entries_changed=5,
        archive_other_entries_preserved=len(untouched),archive_entry_count=len(old_names),
        original_archive_sha256=archive_hash,total_verified_cells=count)
    (RECORDS/'交付同步记录.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(publication,ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
