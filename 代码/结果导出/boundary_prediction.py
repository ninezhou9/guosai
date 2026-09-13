"""Extend the saved run using the original forecasting/LP functions, read-only.

This does not manufacture the externally issued PV forecast required by Q3.
Run forecast with the original Q2 runtime and q4 with the original Q4 runtime.
"""
from pathlib import Path
import argparse, importlib.util, json, sys, hashlib

ROOT = Path(__file__).resolve().parents[2]
Q2 = ROOT / '代码/实验/q2_fresh_20260912'
Q4 = ROOT / '代码/实验/q4_independent_codex_20260912'
WORK = ROOT / 'tmp/result_template_refill_20260913'
sys.path.append(str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages'))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forecast():
    import numpy as np
    core = module('boundary_q2_original', Q2/'fresh_engine.py')
    sys.path.insert(0, str(Q2))
    runner = module('boundary_q2_loader', Q2/'run_fresh.py')
    y, p = runner.load(ROOT/'基础数据')
    day = y.shape[1]
    assert day == 365
    X = np.zeros((day+1, 144, 25))
    for d in range(max(7, day-56), day+1):
        X[d] = core.features(y, d)
    direct, separate = core.forecast_day(y, day, X)
    selection = json.loads((Q2/'results/forecast_selection.json').read_text(encoding='utf-8'))
    base = direct.copy()
    if selection['family'] == 'separate_center':
        base += separate[0]-separate[1]-direct[1]
    with np.load(Q2/'results/fresh_forecasts.npz') as z:
        historical_base = z['base']
    pred = base.copy()
    ids = np.arange(max(14, day-30), day)
    net = y[0]-y[1]
    for block in range(4):
        sl = slice(block*36, (block+1)*36)
        for k, q in enumerate(core.QUANTILES):
            pred[k, sl] += np.quantile(net[ids, sl]-historical_base[ids, k, sl], float(q))
    pred = np.sort(pred, axis=0)
    saved = np.load(Q2/'results/main.npy')
    E0 = float(saved[-1,-1,-1])
    plan = core.plan_lp(p, pred[3]/6, E0, 0.)
    assert core.FIT_CALLS == 7
    assert np.isfinite(plan).all() and (plan >= 0).all()
    # The extra date has no actual observation rows. Only historical input is passed.
    assert y.shape == (2,365,144)
    result = dict(date='2026-01-01', interval='00:00-00:10',
                  method='original Q2 forecast_day, calibration and plan_lp',
                  training_dates=['2025-11-06','2025-12-31'], models_fitted=core.FIT_CALLS,
                  runtime=sys.executable, family=selection['family'],
                  historical_observations_only=True, day_initial_kwh=E0,
                  q2_plan_kwh=plan.tolist(), q2_price=p.tolist(),
                  net_quantiles_kw=pred.tolist(), separate_load_pv_kw=separate.tolist(),
                  first_slot_kwh=float(plan[0]), first_slot_cost=float(plan[0]*p[0]),
                  original_sources={str(path.relative_to(ROOT)):digest(path) for path in
                                    [Q2/'fresh_engine.py',Q2/'run_fresh.py']})
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK/'boundary_prediction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['date','interval','models_fitted','first_slot_kwh','first_slot_cost']},ensure_ascii=False))


def q4():
    import numpy as np
    m = module('boundary_q4_original', Q4/'model.py')
    path = WORK/'boundary_prediction.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    with np.load(Q4/'results/features.npz') as z:
        actual_price = z['price']
    with np.load(Q4/'results/trajectories.npz') as z:
        E0 = float(z['A42'][-1,-1,7])
    # Exact continuation of model.price_features, line 87, for d=365.
    price = actual_price[max(0,365-7):365].mean(axis=0)
    net = np.asarray(result['net_quantiles_kw'])[3]/6
    plan, info = m.plan(price, net, E0)
    assert np.isfinite(plan).all() and (plan >= 0).all()
    result['q42'] = dict(day_initial_kwh=E0, plan_kwh=plan.tolist(),
                        forecast_price=price.tolist(), first_slot_kwh=float(plan[0]),
                        first_slot_cost_forecast=float(plan[0]*price[0]), lp=info,
                        method='original model.plan and original seven-day price mean',
                        runtime=sys.executable, source_sha256=digest(Q4/'model.py'))
    result['q3_q43'] = dict(status='requires_external_forecast',
                           missing='2026-01-01 00:00 issued 24-hour PV forecast',
                           no_substitute_forecast_method_used=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result['q42'],ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser()
    parser.add_argument('stage', choices=['forecast','q4'])
    args=parser.parse_args()
    (forecast if args.stage=='forecast' else q4)()
