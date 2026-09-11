"""Post-export checks without changing solver outputs or any previous files."""
from pathlib import Path
import sys, json
sys.dont_write_bytecode=True
import numpy as np
import run_revision as r

def main():
    b=r.b;out=r.OUT
    summary=r.read(out/'summary.json');main=summary['new']['main']
    vals=np.array([-50.,-5.,0.,1.,2.,6.,20.,70.,110.])
    atoms,weights=r.atomize(vals,7)
    assert abs(weights.sum()-1)<1e-12
    assert abs(atoms@weights-vals.mean())<1e-12
    assert atoms.min()==vals.min() and atoms.max()==vals.max()
    manifest=r.read(out/'reproduction_manifest.json')
    mismatches=[name for name,h in manifest['outputs'].items() if b.sha(r.BASE/name)!=h]
    assert not mismatches,mismatches
    assert b.sha(r.BASE/'修正结果报告.md')==manifest['report_sha256']
    wb=b.openpyxl.load_workbook(out/'result2_独立实验审核版.xlsx',read_only=True,data_only=True)
    ws=wb['全年主方案'];assert ws.max_row==48097
    sums=np.zeros(3)
    for row in ws.iter_rows(min_row=2,values_only=True):sums+=np.array([row[-2],row[-1],row[8]],float)
    expected=np.array([main['normal_cost'],main['emergency_cost'],main['emergency_kWh']])
    assert abs(sums-expected).max()<1e-5
    assert '7个样本' in wb['口径说明']['B5'].value
    wb.close()
    previous=r.read(r.OLD/'results/summary.json')['new']['main']
    metrics=summary['new'];greedy=metrics['greedy_same_plan'];delay=metrics['delayed_same_plan']
    results={'status':'passed','atom_weight_mean_and_extremes_preserved':True,'manifest_output_hashes_match':True,
        'final_workbook_rows':48096,'final_workbook_max_numeric_difference':float(abs(sums-expected).max()),
        'main':main,'prior_cost':previous['total_cost'],'cost_change':main['total_cost']-previous['total_cost'],
        'savings_vs_same_plan_greedy':greedy['total_cost']-main['total_cost'],
        'delayed_extra_cost':delay['total_cost']-main['total_cost'],
        'delayed_extra_cost_percent':100*(delay['total_cost']/main['total_cost']-1),
        'command':[sys.executable,'-X','utf8',str(Path(__file__).relative_to(b.ROOT))]}
    b.dump(out/'delivery_check.json',results)
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
