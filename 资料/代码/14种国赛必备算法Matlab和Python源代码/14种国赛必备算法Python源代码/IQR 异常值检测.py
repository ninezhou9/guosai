import numpy as np
import pandas as pd

# 1. 模拟数据（含异常值的销量数据）
np.random.seed(42)
normal_data = np.random.normal(500, 50, 95)  # 正常数据
outliers = np.array([1200, 80, 1100, 50, 1300])  # 异常值
sales = np.concatenate([normal_data, outliers])
data = pd.DataFrame({"销量": sales})

# 2. IQR异常值检测
def iqr_detect(data, column="销量"):
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = data[(data[column] < lower) | (data[column] > upper)]
    return outliers, lower, upper

# 3. 运行检测
outliers, lower, upper = iqr_detect(data)

# 4. 输出结果
print(f"异常值数量：{len(outliers)}")
print("\n异常值详情：")
print(outliers.round(2))
print(f"\n正常范围：[{lower:.2f}, {upper:.2f}]")
