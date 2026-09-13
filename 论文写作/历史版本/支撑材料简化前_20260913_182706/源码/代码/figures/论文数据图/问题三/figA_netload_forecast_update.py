"""Plot existing Q3 forecasts; no fitting, smoothing, or simulated observations.

Run: python -X utf8 figA_netload_forecast_update.py --kind raw
Optional: --kind calibrated --date 2025-03-20
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.text import Text
import numpy as np
import pandas as pd

COLORS = dict(actual='#104E8B', forecast_00='#7DAEEB', forecast_06='#5BC0C9',
              forecast_12='#E5B5B5', forecast_18='#D85C5C')
STEM = 'figA_netload_forecast_update'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=['raw', 'calibrated'], default='raw')
    parser.add_argument('--date', default='2025-03-20',
                        help='Default: first of the four dates specified in the problem; not selected by accuracy.')
    args = parser.parse_args()
    out = Path(__file__).resolve().parent
    root = next(p for p in out.parents if (p/'基础数据').is_dir())
    source = root/'代码/实验/q3_revision_a_20260912/results'
    cache_path = source/'conditional_forecasts.npz'
    actual_path = source/'main_intervals.csv'
    manifest_path = source/'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    inputs = {str(p): sha(p) for p in [cache_path, actual_path, manifest_path]}
    for p in [cache_path, actual_path]:
        assert inputs[str(p)] == manifest['output_hashes'][p.name], f'Source hash mismatch: {p}'
    data = pd.read_csv(actual_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'slot']).reset_index(drop=True)
    dates = pd.date_range('2025-02-01', '2025-12-31')
    assert len(data) == 334*144
    assert np.array_equal(data['date'].to_numpy().reshape(334, 144)[:, 0], dates.to_numpy())
    assert np.array_equal(data['slot'].to_numpy().reshape(334, 144), np.tile(np.arange(1,145), (334,1)))
    actual = data['net_kwh'].to_numpy().reshape(334,144)*6
    with np.load(cache_path) as f:
        load = f['load'].copy()
        pv = f['pv'].copy()
        raw = load[:, None, :]-pv
        forecast = raw if args.kind == 'raw' else f['pred'][:, :, 1, :].copy()
    assert forecast.shape == (365,4,144)
    forecast = forecast[31:]
    for k in range(4):
        assert np.isfinite(forecast[:,k,36*k:]).all()
        assert np.isnan(forecast[:,k,:36*k]).all()
    date = pd.Timestamp(args.date)
    assert date in dates
    d = (date-dates[0]).days
    daily, paired = [], []
    for k in range(4):
        sl = slice(k*36, 144)
        error = forecast[d,k,sl]-actual[d,sl]
        all_error = forecast[:,k,sl]-actual[:,sl]
        daily.append(dict(issue=f'{6*k}:00', window=f'{6*k}:00–24:00', n=int(error.size),
                          mae_kw=float(np.abs(error).mean()), rmse_kw=float(np.sqrt(np.mean(error**2))),
                          pooled_mae_kw=float(np.abs(all_error).mean())))
        if k:
            old = float(np.abs(forecast[:,k-1,sl]-actual[:,sl]).mean())
            new = float(np.abs(all_error).mean())
            paired.append(dict(issue=f'{6*k}:00', target_window=f'{6*k}:00–24:00',
                               previous_version_mae_kw=old, updated_mae_kw=new,
                               reduction_percent=100*(old-new)/old,
                               representative_day_previous_mae_kw=float(np.abs(forecast[d,k-1,sl]-actual[d,sl]).mean()),
                               representative_day_updated_mae_kw=daily[-1]['mae_kw']))

    available = {f.name for f in font_manager.fontManager.ttflist}
    chinese = next((n for n in ['Microsoft YaHei','SimHei','Noto Sans CJK SC'] if n in available), None)
    assert chinese, 'A Chinese font is required.'
    plt.rcParams.update({'font.family':'sans-serif', 'font.sans-serif':[chinese,'Arial'],
                         'axes.unicode_minus':False, 'font.size':10,
                         'axes.labelsize':11, 'xtick.labelsize':10, 'ytick.labelsize':10,
                         'svg.fonttype':'path', 'pdf.fonttype':42, 'axes.linewidth':0.75})
    fig = plt.figure(figsize=(8.4,4.4), facecolor='white')
    ax = fig.add_axes([0.10,0.16,0.61,0.79])
    x = (np.arange(144)+0.5)/6  # interval midpoints; never shift completed values into future slots
    styles = [(0,(6,3)), (0,(6,2,1.5,2)), (0,(3.5,2.2)), (0,(2,1.5))]
    labels = ['0:00 预测','6:00 更新预测','12:00 更新预测','18:00 更新预测']
    forecast_lines = []
    for k, key in enumerate(['forecast_00','forecast_06','forecast_12','forecast_18']):
        line, = ax.plot(x[36*k:], forecast[d,k,36*k:], color=COLORS[key],
                        lw=1.65 if k!=3 else 1.85, ls=styles[k], label=labels[k], zorder=3+k)
        forecast_lines.append(line)
    actual_line, = ax.plot(x,actual[d],color=COLORS['actual'],lw=2.4,label='实际净负荷',zorder=8)
    for h in [6,12,18]:
        ax.axvline(h,color='#AEB8C2',lw=0.85,ls=(0,(3,4)),zorder=1)
    ax.set_xlim(0,24)
    ax.set_xticks([0,6,12,18,24], ['0:00','6:00','12:00','18:00','24:00'])
    ax.set_xlabel('时间')
    ax.set_ylabel('净负荷 / kW')
    ax.grid(axis='y',color='#E9EDF1',lw=0.65,zorder=0)
    ax.spines[['top','right']].set_visible(False)
    for edge in ['left','bottom']:
        ax.spines[edge].set_color('#6E7883')
    ax.tick_params(length=3,color='#6E7883')
    ax.margins(y=0.10)
    fig.text(0.755,0.934,args.date,fontsize=10.5,color='#334155')
    fig.legend(handles=[actual_line]+forecast_lines,loc='upper left',
               bbox_to_anchor=(0.745,0.899),frameon=False,handlelength=3.2,
               handletextpad=0.8,labelspacing=0.75,fontsize=9.5)
    table = ax.table(cellText=[[v['issue'],f"{v['mae_kw']:.2f}"] for v in daily],
                     colLabels=['预报时刻','MAE / kW'],cellLoc='center',colLoc='center',
                     bbox=[1.07,0.22,0.37,0.34],colWidths=[0.44,0.56])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#E1E7ED')
        cell.set_linewidth(0.55)
        cell.set_facecolor('#F1F5F9' if r==0 else 'white')
        cell.get_text().set_color('#334155')
    footnote = fig.text(0.755,0.29,'MAE：代表日发布后至24:00\n各行评价时段长度不同',fontsize=8.2,
                        color='#64748B',linespacing=1.65,va='top')
    kind_label = '负荷预测 − 光伏预测' if args.kind=='raw' else '历史误差校准后的中位数'
    fig.text(0.755,0.177,kind_label,fontsize=8.2,color='#64748B')
    for text in fig.findobj(match=Text):
        text.set_fontfamily(chinese if any(ord(c)>127 for c in text.get_text()) else 'Arial')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    assert not table.get_window_extent(renderer).overlaps(footnote.get_window_extent(renderer))
    for ext in ['png','svg','pdf']:
        fig.savefig(out/f'{STEM}.{ext}',dpi=300,facecolor='white',metadata={'Creator':'Matplotlib'} if ext!='png' else None)
    plt.close(fig)
    records = pd.DataFrame({'interval_start':np.arange(144)/6, 'interval_end':(np.arange(144)+1)/6,
                            'plot_hour_midpoint':x,'actual_netload_kw':actual[d]})
    for k in range(4):
        records[f'forecast_{6*k:02d}_kw'] = forecast[d,k]
    records.to_csv(out/f'{STEM}_data.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(daily).to_csv(out/f'{STEM}_mae.csv',index=False,encoding='utf-8-sig')
    meta = dict(date=args.date,kind=args.kind,selection='First date specified in problem; fixed, not chosen by forecast performance.',
                actual_field='main_intervals.csv: net_kwh * 6 = actual load - actual PV, kW',
                forecast_field='conditional_forecasts.npz: load[d, :] - pv[d, k, :]' if args.kind=='raw'
                else 'conditional_forecasts.npz: pred[d, k, 1, :] (q=0.50; includes historical residual correction)',
                raw_forecast_field='load[d, :] - pv[d, k, :]',date_index=(date-pd.Timestamp('2025-01-01')).days,
                issue_index={'0:00':0,'6:00':1,'12:00':2,'18:00':3},plot_time='10-minute interval midpoint',
                dpi=300,colors=COLORS,mae=daily,same_target_window_update_checks=paired,
                caveats=['Later forecasts begin only after release; no backfilling or curve offsets.',
                         'MAE across issue times covers different remaining horizons; not a pure information-value comparison.',
                         'Identical late-day forecasts remain overlapping; not artificially separated.',
                         'Forecast accuracy alone does not prove every purchase-plan revision is economical.'],
                input_sha256=inputs,python=platform.python_version(),matplotlib=matplotlib.__version__,
                source_sha256=sha(Path(__file__)))
    for path, digest in inputs.items():
        assert sha(Path(path)) == digest, f'Input changed: {path}'
    (out/f'{STEM}_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'date':args.date,'kind':args.kind,'metrics':daily,'paired_checks':paired,
                      'output':str(out),'input_hashes_verified':True},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
