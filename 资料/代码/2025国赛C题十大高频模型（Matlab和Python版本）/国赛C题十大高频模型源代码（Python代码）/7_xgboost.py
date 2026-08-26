import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

# 生成二分类数据
np.random.seed(42)
X, y = make_classification(
    n_samples=1000, n_features=15, n_informative=8,
    n_redundant=3, random_state=42
)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# 数据标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 创建并训练XGBoost模型
model = xgb.XGBClassifier(
    objective='binary:logistic',  # 二分类问题
    n_estimators=100,             # 树的数量
    max_depth=3,                  # 树的最大深度
    learning_rate=0.1,            # 学习率
    random_state=42
)

model.fit(X_train_scaled, y_train)

# 预测
y_pred = model.predict(X_test_scaled)
y_prob = model.predict_proba(X_test_scaled)[:, 1]

# 评估
accuracy = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)

# 输出结果
print("XGBoost模型结果：")
print(f"准确率: {accuracy:.4f}")
print(f"AUC: {auc:.4f}")
print("\n分类报告:")
print(classification_report(y_test, y_pred))

# 特征重要性
plt.figure(figsize=(10, 6))
xgb.plot_importance(model, importance_type='weight', title='特征重要性')
plt.tight_layout()
plt.show()
