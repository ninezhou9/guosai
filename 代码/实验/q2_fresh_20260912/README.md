# 第二问：原始附件完整重跑

总费用 **13,774,501.34元**，本次新训练2457个LightGBM模型，无旧预测/旧结果输入。

[具体解法与结果](解法与结果.md) · [结果Excel](results/result2.xlsx) · [完整逐时明细](results/main_intervals.csv) · [运行与校验记录](results/manifest.json)

核心路线：固定80分位预测、日前无终端项LP、日内Markov与类内加权样本Bellman、连续SOC。

复现须新建空输出目录：

```powershell
python -m pip install -r 代码/实验/q2_fresh_20260912/requirements.txt
python 代码/实验/q2_fresh_20260912/run_fresh.py --output 代码/实验/q2_fresh_20260912/results_new
```
