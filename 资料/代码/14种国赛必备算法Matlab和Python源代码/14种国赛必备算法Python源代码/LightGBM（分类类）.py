import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. 模拟数据（用户购买行为）
np.random.seed(42)
n = 500
data = pd.DataFrame({
    "年龄": np.random.randint(18, 60, n),
    "消费能力": np.random.randint(1, 5, n),
    "浏览时长": np.random.uniform(0.5, 4, n),
    "是否购买": np.where(
        (np.random.randint(1,5,n)>=3) & (np.random.uniform(0.5,4,n)>=2), 
        1, 0
    )
})

# 2. 数据拆分
X = data.drop("是否购买", axis=1)
y = data["是否购买"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 建模与预测
train_data = lgb.Dataset(X_train, label=y_train)
params = {
    "objective": "binary",
    "metric": "accuracy",
    "max_depth": 6,
    "seed": 42
}
model = lgb.train(params, train_data, num_boost_round=100)
y_pred = model.predict(X_test) > 0.5  # 概率转标签

# 4. 结果评估
print(f"LightGBM分类准确率：{accuracy_score(y_test, y_pred):.4f}")
print("\n特征重要性：")
print(pd.Series(model.feature_importance(), index=X.columns).round(4))
