"""Extend the saved run using the original forecasting/LP functions, read-only.

Original model sources remain read-only. The q1/q3 stages implement the user's
authorized boundary assumptions; synthesized forecasts are explicitly labelled.
Reproduction order: forecast, q4, q1, q3.
"""
from pathlib import Path
import argparse, importlib.util, json, sys, hashlib

ROOT = Path(__file__).resolve().parents[2]
Q2 = ROOT / '代码/实验/q2_fresh_20260912'
Q3 = ROOT / '代码/实验/q3_revision_a_20260912'
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


def q1():
    import csv
    import numpy as np
    original = ROOT/'代码/q1_solution.py'
    before = digest(original)
    m = module('boundary_q1_original', original)
    p, load, pv = m.load()
    with (ROOT/'代码/results/q1/完整调度.csv').open(encoding='utf-8-sig', newline='') as f:
        history = list(csv.DictReader(f))
    previous_end = float(history[-1]['期末储电_kWh'])
    # New boundary assumption: repeat the supplied PV forecast for one more day.
    # Repeated load and price are already specified in Question 1 itself.
    fit, (g, c, discharge, spill), energy = m.solve(p, load, pv)
    checks = dict(
        cross_day_energy_error=float(abs(energy[0]-previous_end)),
        daily_cyclic_error=float(abs(energy[-1]-energy[0])),
        balance_error=float(np.max(abs(g+pv*m.DT+discharge-load*m.DT-c-spill))),
        storage_error=float(np.max(abs(np.diff(energy)-m.ETA*c+discharge/m.ETA))),
        storage_bound_violation=float(max(0.,1200-energy.min(),energy.max()-10800)),
        rate_violation=float(max(0.,c.max()-m.CAP,discharge.max()-m.CAP)),
        simultaneous_charge_discharge=float(np.minimum(c,discharge).max()))
    assert max(checks.values()) < 1e-6, checks
    assert np.isfinite(g).all() and (g >= -1e-8).all()
    assert digest(original) == before
    path = WORK/'boundary_prediction.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    result['q1'] = dict(ready=True, interval='next day 00:00-00:10',
        assumption='Repeat the supplied one-day PV forecast for the next daily cycle; user authorized boundary extension.',
        method='Fresh call to the unchanged q1_solution.solve with the extended daily profile.',
        fresh_solver_call=True, source_sha256=before, runtime=sys.executable,
        previous_day_end_kwh=previous_end, day_initial_kwh=float(energy[0]),
        day_terminal_kwh=float(energy[-1]), first_slot_kwh=float(g[0]),
        first_slot_cost=float(g[0]*p[0]), plan_kwh=g.tolist(),
        charge_kwh=c.tolist(), discharge_kwh=discharge.tolist(),
        spill_kwh=spill.tolist(), stored_kwh=energy.tolist(),
        pv_assumed_kw=pv.tolist(), objective=float(fit.fun),
        solver_status=int(fit.status), mip_gap=float(fit.mip_gap), validation=checks)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result['q1'][k] for k in
                     ['ready','first_slot_kwh','day_initial_kwh','objective','validation']},ensure_ascii=False))


def q3():
    import numpy as np
    path = WORK/'boundary_prediction.json'
    result = json.loads(path.read_text(encoding='utf-8'))
    engine = module('boundary_q3_original', Q3/'q3_engine.py')
    y, price, load_pred, forecasts = engine.load_inputs()
    # At 2026-01-01 00:00 the last issued forecast is 2025-12-31 18:00.
    # Its hours 7..24 provide January 1 hours 1..18. Extend only hours 19..24
    # with the preceding seven midnight forecasts' means at those same hours.
    carried = forecasts[-1,3,6:].copy()
    estimated = forecasts[-7:,0,18:].mean(axis=0)
    next_hourly = np.r_[carried, estimated]
    assert next_hourly.shape == (24,) and np.isfinite(next_hourly).all()
    assert (next_hourly >= 0).all()
    # The original routines accept exactly 365 dates. Slide that input window
    # forward by one day. Unknown next-day actual observations remain NaN;
    # the midnight forecast uses only the preceding day's final PV observation.
    next_issues = np.full((1,4,24), np.nan)
    next_issues[0,0] = next_hourly
    next_load = np.asarray(result['separate_load_pv_kw'])[0]
    y_window = np.concatenate([y[:,1:],np.full((2,1,144),np.nan)],axis=1)
    load_window = np.concatenate([load_pred[1:],next_load[None,:]],axis=0)
    forecast_window = np.concatenate([forecasts[1:],next_issues],axis=0)
    pred, interpolated = engine.conditional_forecasts(y_window,load_window,forecast_window)
    with np.load(Q3/'results/conditional_forecasts.npz') as z:
        overlap_error = float(np.max(abs(pred[-2,0]-z['pred'][-1,0])))
        historical_pv = z['pv'][:,0]
    assert overlap_error < 1e-8, overlap_error
    target = pred[-1,0]
    # Independently verify the actual date alignment and original calibration.
    target_pv = np.interp(np.arange(1,145)/6.,np.arange(25),np.r_[y[1,-1,-1],next_hourly])
    expected = np.tile(next_load-target_pv,(5,1))
    residual = (y[0]-y[1])-(load_pred-historical_pv)
    for lo in range(0,144,36):
        expected[:,lo:lo+36] += np.quantile(residual[-30:,lo:lo+36],engine.QUANTILES)[:,None]
    expected = np.sort(expected,axis=0)
    alignment_error = float(np.max(abs(target-expected)))
    assert alignment_error < 1e-8 and np.isfinite(target).all()
    assert np.isnan(y_window[:,-1]).all()
    with np.load(Q3/'results/solutions.npz') as z:
        e3 = float(z['arrays'][7,-1,-1,6])
    plan3 = engine.b.plan_lp(price,target[3]/6.,e3,0.)
    model4 = module('boundary_q43_original', Q4/'model.py')
    with np.load(Q4/'results/trajectories.npz') as z:
        e43 = float(z['A43_111'][-1,-1,7])
    price4 = np.asarray(result['q42']['forecast_price'])
    plan43, info43 = model4.plan(price4,target[3]/6.,e43)
    result['q3'] = dict(ready=True,day_initial_kwh=e3,plan_kwh=plan3.tolist(),
        first_slot_kwh=float(plan3[0]),first_slot_cost=float(plan3[0]*price[0]),
        method='Original conditional_forecasts and plan_lp, with authorized PV forecast extension.',
        original_solver_assertions_passed=True)
    result['q43'] = dict(ready=True,day_initial_kwh=e43,plan_kwh=plan43.tolist(),
        first_slot_kwh=float(plan43[0]),first_slot_cost=float(plan43[0]*price4[0]),
        first_slot_cost_basis='forecast price, not observed 2026 price',
        method='Original Q3 conditional_forecasts and original Q4 model.plan, with authorized PV forecast extension.',lp=info43)
    result['q3_q43'] = dict(status='complete_with_authorized_forecast_extension',
        as_of='2026-01-01 00:00',latest_original_issue='2025-12-31 18:00',
        assumption='Carry the latest issued forecast for Jan 1 hours 1..18; extend hours 19..24 using the last seven midnight forecasts at matching hours.',
        carried_hours=18,estimated_hours=6,synthetic_forecast_not_a_new_official_issue=True,
        actual_2026_observations_used=False,next_day_actual_rows_left_unknown=True,
        next_hourly_pv_kw=next_hourly.tolist(),pv_10minute_kw=interpolated[-1,0].tolist(),
        net_quantiles_kw=target.tolist(),last_historical_day_reproduction_error=overlap_error,
        next_day_calibration_alignment_error=alignment_error,runtime=sys.executable,
        original_sources={str(p.relative_to(ROOT)):digest(p) for p in [Q3/'q3_engine.py',Q4/'model.py']})
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(q3_first=plan3[0],q43_first=plan43[0],pv_tail=estimated.tolist(),
                         overlap_error=overlap_error,alignment_error=alignment_error,lp43=info43),ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser()
    parser.add_argument('stage', choices=['forecast','q4','q1','q3'])
    args=parser.parse_args()
    {'forecast':forecast,'q4':q4,'q1':q1,'q3':q3}[args.stage]()
