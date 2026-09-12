"""本次输出的补充核验；未来扰动仅改变负载，避免净负荷相减抵消。"""
from pathlib import Path
import json,csv,hashlib
import numpy as np
import fresh_engine as m
from run_fresh import load

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'results'
data=next(p for p in [ROOT/'基础数据/C题/附件',ROOT/'基础数据'] if (p/'附件2.xlsx').exists())
y,p=load(data)
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
pred=np.load(OUT/'fresh_forecasts.npz')['pred']
checks=[]
for d in [31,90,180,270]:
    altered=y.copy();altered[0,d:]+=30000
    assert np.array_equal(m.features(y,d),m.features(altered,d))
    original=m.markov(y,pred,d);mutated=m.markov(altered,pred,d)
    for key in original:np.testing.assert_array_equal(original[key],mutated[key])
    checks.append({'day_index':d,'future_load_changed_without_pv_cancellation':True,'past_only_features_and_probabilities':True})
with (OUT/'main_intervals.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
assert len(rows)==48096
g=np.array([float(r['g_kwh']) for r in rows]);e=np.array([float(r['emergency_kwh']) for r in rows]);price=np.array([float(r['price']) for r in rows])
bill=float(np.sum(price*g+5*price*e))
assert abs(bill-manifest['summary']['main']['total_cost'])<1e-5
with (OUT/'training_trace.csv').open(encoding='utf-8-sig',newline='') as f:trace=list(csv.DictReader(f))
assert len(trace)==351 and sum(int(x['models_fit']) for x in trace)==2457
assert all(x['training_end']<x['forecast_date'] for x in trace)
for name,digest in manifest['output_hashes'].items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest
result={'status':'passed','causal_checks':checks,'csv_recomputed_bill':bill,'training_days':351,'models_fit':2457,
        'training_cutoff_before_forecast_date':True,'original_run_output_hashes_match':True}
(OUT/'independent_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
