import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# 1. 模拟数据（销量与特征的关系）
np.random.seed(42)
data = pd.DataFrame({
    "广告投入": np.random.uniform(10, 100, 200),
    "促销力度": np.random.randint(1, 6, 200),
    "客流量": np.random.uniform(500, 2000, 200),
    "销量": 5 + 0.3*np.random.uniform(10,100,200) + 2*np.random.randint(1,6,200) + 0.01*np.random.uniform(500,2000,200) + np.random.normal(0, 2, 200)
})

# 2. 数据拆分
X = data[["广告投入", "促销力度", "客流量"]]
y = data["销量"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. XGBoost建模
model = XGBRegressor(
    learning_rate=0.05,
    max_depth=5,
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)

# 4. 预测与评估
y_pred = model.predict(X_test)
print(f"XGBoost预测R²得分：{r2_score(y_test, y_pred):.4f}")
print("\n特征重要性：")
print(pd.Series(model.feature_importances_, index=X.columns).round(4))
