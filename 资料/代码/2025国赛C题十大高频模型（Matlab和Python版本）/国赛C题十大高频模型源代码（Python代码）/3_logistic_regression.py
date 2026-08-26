import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix

# 生成二分类数据
np.random.seed(42)
X, y = make_classification(
    n_samples=200, n_features=5, n_informative=3,
    n_redundant=1, random_state=42
)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# 训练Logistic回归模型
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train, y_train)

# 预测
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

# 评估
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

# 输出结果
print("Logistic回归模型结果：")
print(f"准确率: {accuracy:.4f}")
print("混淆矩阵:")
print(conf_matrix)
print("\n系数:")
for i, coef in enumerate(model.coef_[0]):
    print(f"特征 {i+1}: {coef:.4f}")
print(f"截距: {model.intercept_[0]:.4f}")

# 绘制预测概率直方图
plt.figure(figsize=(8, 6))
plt.hist(y_prob[y_test == 0], bins=10, alpha=0.5, label='负类')
plt.hist(y_prob[y_test == 1], bins=10, alpha=0.5, label='正类')
plt.xlabel('预测概率')
plt.ylabel('频率')
plt.title('预测概率分布')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
