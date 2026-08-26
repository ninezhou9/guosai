import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. 模拟数据（设备状态：正常+温度故障）
np.random.seed(42)
# 正常设备（标签0）
normal = pd.DataFrame({
    "温度": np.random.normal(50, 5, 50),
    "振动": np.random.normal(0.5, 0.1, 50),
    "故障类型": 0
})
# 温度故障（标签1）
fault = pd.DataFrame({
    "温度": np.random.normal(80, 8, 50),
    "振动": np.random.normal(0.5, 0.1, 50),
    "故障类型": 1
})
data = pd.concat([normal, fault], ignore_index=True)

# 2. 数据拆分
X = data[["温度", "振动"]]
y = data["故障类型"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 建模与预测
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# 4. 结果评估
print(f"故障识别准确率：{accuracy_score(y_test, y_pred):.4f}")
print("\n特征重要性（判断故障的关键指标）：")
print(pd.Series(model.feature_importances_, index=X.columns).round(4))
