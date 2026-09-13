# 模型代码与运行入口

| 问题 | 当前主版本 | 入口 |
| --- | --- | --- |
| 第一问 | `q1_solution.py` | `q1_solution.py` |
| 第二问 | `实验/q2_fresh_20260912/` | `run_fresh.py`，说明见该目录README |
| 第三问 | `实验/q3_revision_a_20260912/` | `run_q3.py`，说明见该目录README |
| 第四问 | `实验/q4_independent_codex_20260912/` | `run.py`，说明见该目录README |
| 跨日补算、模板回填 | `结果导出/` | 下述顺序 |
| 附录与支撑材料同步 | `交付整理/sync_materials.py` | `build`、`sync`、`pack` |

支撑材料按最终版本清单打包，上表各问目录为项目内正式计算入口；支撑包只保留四问模型程序、依赖清单、五份答案和AI使用说明。支撑包中的运行入口已适配简化目录及删除独立核验程序后的依赖，原模型求解函数、参数和方法不变。时间对齐、绘图和各问详细记录仍保留在项目工作目录。打包清单位于 `交付整理/sync_materials.py` 的 `SOURCE_GROUPS`，同步与打包均核对该清单。

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
9. `交付整理/sync_materials.py sync`、`pack`：在交付整理缓存中同步最终程序和答案，向交付目录发布支撑包。

附录内容需要更新时，先运行 `sync_materials.py build`，核对文档后运行 `sync_materials.py sync --include-documents`，再运行 `sync_materials.py pack`。不带 `--include-documents` 的同步仅更新源码、结果和记录。本次按用户确认省略Word分页检查，保留内容、源码与结构核对，实际分页仍标记为未验证；本次确认不自动适用于后续新版本。

计算依赖NumPy、SciPy、LightGBM、openpyxl、Matplotlib；Word编辑及独立PDF排版依赖python-docx、ReportLab、pypdf。Excel回填使用Node和 `@oai/artifact-tool`。当前补算使用Python313及Codex内置运行时，旧SARIMA模型专用的项目依赖已移除。回填数据与交付状态分别放在 `结果导出/缓存/`、`交付整理/缓存/`，它们不进入支撑包。完整重现需原始附件及各问计算生成的缓存，不能只凭支撑包宣称全年重跑通过。
