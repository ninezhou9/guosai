# 模型代码与运行入口

| 问题 | 当前主版本 | 入口 |
| --- | --- | --- |
| 第一问 | `q1_solution.py` | `q1_solution.py` |
| 第二问 | `实验/q2_fresh_20260912/` | `run_fresh.py`，说明见该目录README |
| 第三问 | `实验/q3_revision_a_20260912/` | `run_q3.py`，说明见该目录README |
| 第四问 | `实验/q4_independent_codex_20260912/` | `run.py`，说明见该目录README |
| 跨日补算、模板回填 | `结果导出/` | 下述顺序 |
| 附录与支撑材料同步 | `交付整理/sync_materials.py` | `build`、`sync`、`pack` |

根目录的 `q2_solution.py`、`q2_validate.py`、`运行第二问.ps1` 及其他第二问实验是历史实现或对照方案。`figures/`、`matlab/` 和各实验的绘图程序保留原有位置，方便既有脚本继续运行。

四问原始优化与预测方法保留。`结果导出/boundary_rules.py` 集中记录新增的时间对齐和边界规则：第一问按光伏日周期延拓后调用原求解器；第三问与4-3衔接最后一次有效预报，并以此前7天同一时刻的预报均值延拓年末缺失时段。

在已有完整模型结果和缓存的基础上，依次执行：

1. `结果导出/boundary_prediction.py forecast`
2. `结果导出/boundary_prediction.py q4`
3. `结果导出/boundary_prediction.py q1`
4. `结果导出/boundary_prediction.py q3`
5. `结果导出/prepare_templates.py`
6. `结果导出/refill_templates.mjs fill`
7. `结果导出/verify_templates.py`
8. `结果导出/publish_results.py`：发布五份已核验答案。
9. `交付整理/sync_materials.py sync`、`pack`：同步源码、记录并重建整个支撑包。

附录内容需要更新时，先运行 `sync_materials.py build`，检查生成的Word和PDF，再同步。文档实际分页未验证时，不将内容检查等同于排版通过；当前状态见论文交付说明。

计算依赖NumPy、SciPy、LightGBM、openpyxl、Matplotlib；Word编辑及独立PDF排版依赖python-docx、ReportLab、pypdf。Excel回填使用Node和 `@oai/artifact-tool`。本机第二问旧清单中的E盘Anaconda路径已失效，当前补算使用Python313及Codex内置运行时。源码打包不包含运行时、`node_modules`、`.deps`、`__pycache__` 或大型模型缓存。完整重现需原始附件及各问计算生成的缓存，不能只凭支撑包宣称全年重跑通过。
