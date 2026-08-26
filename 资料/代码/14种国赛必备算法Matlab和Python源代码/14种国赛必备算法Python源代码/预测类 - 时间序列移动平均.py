import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. 模拟数据（含趋势和季节性的客流量）
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", periods=100)  # 100天数据
trend = np.linspace(100, 200, 100)  # 增长趋势
seasonal = 30 * np.sin(np.linspace(0, 10, 100))  # 周期性波动
data = pd.DataFrame({
    "日期": dates,
    "客流量": trend + seasonal + np.random.normal(0, 10, 100)  # 加噪声
})

# 2. 移动平均预测（窗口=7天）
window = 7
data["预测值"] = data["客流量"].rolling(window=window, min_periods=1).mean()

# 3. 输出结果
print(f"{window}天移动平均预测（最后7天）：")
print(data[["日期", "客流量", "预测值"]].tail(7).round(1))

# 4. 可视化（可选）
plt.figure(figsize=(10, 4))
plt.plot(data["日期"], data["客流量"], label="实际客流量")
plt.plot(data["日期"], data["预测值"], label=f"{window}天移动平均", linestyle="--")
plt.title("客流量时间序列预测")
plt.legend()
plt.show()
