import numpy as np
import pandas as pd

# 1. 模拟数据（5个方案，4个指标：前3个正向，第4个负向）
data = pd.DataFrame({
    "方案1": [85, 92, 88, 25],
    "方案2": [90, 88, 95, 22],
    "方案3": [78, 90, 92, 28],
    "方案4": [92, 85, 86, 20],
    "方案5": [88, 95, 90, 24]
}, index=["收益", "效率", "质量", "成本"]).T  # 行：方案，列：指标

# 2. TOPSIS核心算法
def topsis(data, negative_indices=[3]):
    # 标准化（极差法）
    data_std = (data - data.min()) / (data.max() - data.min() + 1e-10)
    # 负向指标转正向（成本类指标）
    for idx in negative_indices:
        data_std.iloc[:, idx] = 1 - data_std.iloc[:, idx]
    # 计算理想解和距离
    ideal_pos = data_std.max()  # 最优方案
    ideal_neg = data_std.min()  # 最劣方案
    dist_pos = np.sqrt(((data_std - ideal_pos) **2).sum(axis=1))  # 到最优距离
    dist_neg = np.sqrt(((data_std - ideal_neg)** 2).sum(axis=1))  # 到最劣距离
    # 计算贴近度（0~1，越接近1越优）
    return dist_neg / (dist_pos + dist_neg)

# 3. 运行并输出结果
result = topsis(data)
print("TOPSIS方案排名（贴近度越高越优）：")
print(result.sort_values(ascending=False).round(4))
