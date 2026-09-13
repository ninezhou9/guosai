# 第三问：路线A

用户确认的路线：条件净负荷分位预测 → 零点80分位LP → 三次调整LP候选 → DP预期费用评价 → 十分钟反馈执行。

结算：每次对上一版有效计划，增购按1.5倍；撤销量退还原价并缴0.5倍违约费。该口径属于模型解释。期末价值固定0，连续SOC，不每日回到6000kWh。

- `q3_engine.py`：数据读取、光伏预报对齐、条件分位、误差模型、调整LP与批量DP。
- `check_engine.py`：交易、对齐、标量DP等价、当前/未来信息扰动与固定计划退化检查。
- `run_q3.py`：八个预报使用组合和一个只更新预报对照，全年连续回测。
- `deliver_q3.py`：独立账本重放、物理检查、Excel导出回读、四日精度敏感性、图及结果审核报告。
- `results/result3.xlsx`：实际计算后生成的完整结果；原始模板在基础数据目录，保持只读。
- 正式结果审核报告生成到 `论文写作/问题三/第三问_路线A结果审核报告.md`。

在项目根目录执行（需numpy、scipy、lightgbm、openpyxl、matplotlib）：

```powershell
python 代码/实验/q3_revision_a_20260912/run_q3.py --output 代码/实验/q3_revision_a_20260912/results_new
python 代码/实验/q3_revision_a_20260912/deliver_q3.py --output 代码/实验/q3_revision_a_20260912/results_new
```

中断后可对相同输出目录加 `--resume`，程序要求源码、输入、参数完全一致。新运行拒绝覆盖非空目录。

依赖队友新版 `q2_fresh_20260912/fresh_engine.py` 及其已验证预测结果 `results/fresh_forecasts.npz` 的负载中位数分量；有明确SHA256来源校验。本次不重新训练预测模型，不借用第二问购电/SOC轨迹，第三问净误差分位、各次调度及账单均新算。运行时若openpyxl未安装，仅为当前Python进程追加本机Codex bundled site-packages作为导入回退，不改全局环境。

mask的最低位表示6时，次低位12时，最高位18时，例如 `mask_001` 使用0和6时，`mask_100` 使用0和18时。主方案事先固定为 `mask_111`，不是根据全年最小费用反选。

运行数组列依次为：有效普通购电、充电、放电、紧急购电、弃用、期初库存、期末库存；单位kWh。实际总费用须读取初始计划及逐笔调整账本，不能直接用有效普通购电量乘原价。
