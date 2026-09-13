# 代码实现 (Code & Implementation)

## 📌 目录定位
本目录存放竞赛全流程的源码，涵盖数据处理、模型求解、算法实现及结果可视化。

## 🛠️ 环境配置
- 推荐编程语言：Python 3.10+ / Matlab R2022b+
- Python 核心依赖：`numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `gurobipy` / `pulp`, `optuna` 等。

## 📂 建议代码组织规范
```text
代码/
├── q1_solution.py       # 问题一求解脚本
├── q2_solution.py       # 问题二求解脚本
├── q3_solution.py       # 问题三求解脚本
├── utils/               # 公共工具函数（数据读取、指标计算等）
├── visualization/       # 图表绘制与美化脚本
└── requirements.txt     # Python 依赖清单
```

## ⚠️ 编写规范
1. **代码注释**：关键计算步骤、参数设置、损失函数需包含清晰注释。
2. **随机种子**：涉及随机优化、机器学习训练时务必固定随机种子（如 `random_state=42`），确保结果 100% 可复现。
3. **输出图表**：统一输出高清矢量图（.pdf / .svg）或高分辨率点阵图（.png, 300 DPI+）。
