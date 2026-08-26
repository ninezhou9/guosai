import numpy as np
import pandas as pd
from prophet import Prophet

# 1. 模拟数据（带周季节性的客流量）
np.random.seed(42)
dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")
n = len(dates)
trend = np.linspace(1000, 1100, n)  # 年趋势
weekly_season = np.where(dates.weekday >= 5, 200, 50)  # 周末高峰
y = trend + weekly_season + np.random.normal(0, 30, n)
data = pd.DataFrame({"ds": dates, "y": y})

# 2. 建模与预测
model = Prophet(weekly_seasonality=True, yearly_seasonality=True)
model.fit(data)

# 3. 预测未来30天
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# 4. 输出结果
print("未来7天客流量预测：")
print(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(7).round(0))
