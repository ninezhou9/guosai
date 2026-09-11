# 第二问：概率净负荷与随机储能控制独立实验

本目录自包含新程序、新结果和新图，原有 `代码/q2_solution.py`、`代码/results/q2`、`代码/figures/q2`、原始附件和论文不参与写入。模型细节见 `模型合同.md`。

## 复现

从项目根目录执行：

```powershell
& '代码/实验/q2_netload_probabilistic_20260911/运行实验.ps1'
```

或运行主程序（Windows 使用 UTF-8 模式，避免中文缓存路径被 GBK 误读）：

```powershell
& 'C:/Program Files/Python313/python.exe' -X utf8 '代码/实验/q2_netload_probabilistic_20260911/run_experiment.py' --stage all
& 'C:/Program Files/Python313/python.exe' -X utf8 '代码/实验/q2_netload_probabilistic_20260911/make_report.py'
```

`--stage smoke` 是真实输入最小纵向测试；`forecast` 仅生成全年预测；`run` 使用预测缓存运行控制回测；`export` 重新核验及导出现有完整结果。默认 `all` 按代码、输入和依赖签名检查逐日缓存，支持断点继续。需要完全从零运行时，复制本目录的两个 `.py`、`.ps1`、模型合同和原文件哈希清单到同层的另一个新实验目录，不复制 `results`、`figures`，再运行；根目录按固定相对层级解析。

## 输出

- `results/summary.json`：主方案、两项消融、概率预测质量、只读引入的旧汇总。
- `results/result2_独立实验审核版.xlsx`：完整主方案 48096 行、三策略每日费用、四个指定日期及口径说明；是独立审核工作簿，不冒称已填官方开始标签模板。
- `results/*_full_strategy.csv`：三策略的完整逐时计划与实际执行。
- `results/forecast_quantiles.csv`、`forecasts.npz`、`forecast_days`：可追溯概率预测。
- `results/january_warmup.npy`、`validation_*.npy`：1 月连续预热与参数选择证据。
- `results/days`：逐日回测缓存与候选计划期望费用。
- `results/validation.json`：物理约束、算法核验、因果性回归检查、网格精度、Excel 重读。
- `results/original_file_preservation.json`：运行前列入保护范围的原文件复核。
- `results/reproduction_manifest.json`：代码、数据、依赖、参数、运行命令、输出哈希。
- `实验结果报告.md`：由 `make_report.py` 从实际输出生成的阅读版报告。

## 环境与执行记录

实际使用已有 Python 3.13、LightGBM 4.7.0、NumPy 2.5.2、SciPy 1.18.1。Excel 复用桌面运行时的 openpyxl。无需新依赖；前期尝试项目内 pip 安装遇到索引不可用，随后直接导入确认原环境已有可用 LightGBM，本实验未更改全局或旧项目依赖。

最小纵向测试退出码 0。首次读取中文缓存时因默认 GBK 解码失败，退出码 1；改为进程级 UTF-8 模式后继续，未修改数学模型或原文件。完整计算及报告生成是否完成，以日志末尾、复现清单和结果报告为准，不能以本说明代替真实完成证据。

## 审核范围

这是有限候选计划、三状态误差过程及储能价值网格的近似方法，不能宣称原随机优化全局最优。真实储电量连续，没有取整。代码不是读取整条实际未来曲线后一次性调度；每步动作只根据当前观测识别误差状态，并对下一步条件概率求期望。

当日误差不确定性用有限状态近似，不能保证预测区间覆盖率，也不能把本数据集上的改进外推到其他年份。实际观测口径、紧急购电不充储能的策略限制、期初期末库存、时间标签差异均在模型合同和结果报告中披露。

本轮按统一 Skill 的局部代码路线执行，实际读取：统一入口、逐步审核工作流、交付物合同、编程手、CUMCM/C 题规则、质量门禁、Excel 工具、可视化规范。用户已授权方法试算；结果尚待用户审核，未冻结，未写入论文。
