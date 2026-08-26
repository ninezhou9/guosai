import numpy as np
import pandas as pd

# 1. 模拟数据（同TOPSIS的5方案4指标）
data = pd.DataFrame({
    "方案1": [85, 92, 88, 25],
    "方案2": [90, 88, 95, 22],
    "方案3": [78, 90, 92, 28],
    "方案4": [92, 85, 86, 20],
    "方案5": [88, 95, 90, 24]
}, index=["收益", "效率", "质量", "成本"]).T

# 2. 熵权法核心算法
def entropy_weight(data, negative_indices=[3]):
    # 标准化（极差法）
    data_std = (data - data.min()) / (data.max() - data.min() + 1e-10)
    # 负向指标转正向
    for idx in negative_indices:
        data_std.iloc[:, idx] = 1 - data_std.iloc[:, idx]
    # 计算熵值
    n, m = data_std.shape  # n=方案数，m=指标数
    p = data_std / data_std.sum(axis=0)  # 各方案占比
    p = np.where(p == 0, 1e-10, p)  # 避免log(0)
    entropy = - (1 / np.log(n)) * (p * np.log(p)).sum(axis=0)
    # 计算权重（熵值越小，权重越大）
    return (1 - entropy) / (1 - entropy).sum()

# 3. 运行并输出结果
weights = entropy_weight(data)
print("各指标权重（熵权法）：")
print(weights.round(4))
print(f"权重总和：{weights.sum():.4f}")  # 验证权重和为1
