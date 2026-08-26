import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report

# 生成分类数据
np.random.seed(42)
X, y = make_classification(
    n_samples=500, n_features=10, n_informative=5,
    n_redundant=2, n_classes=3, random_state=42
)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# 数据标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 定义基分类器
clf1 = LogisticRegression(max_iter=1000, random_state=42)
clf2 = SVC(probability=True, random_state=42)
clf3 = DecisionTreeClassifier(max_depth=5, random_state=42)
clf4 = KNeighborsClassifier(n_neighbors=5)

# 创建Soft Voting集成模型
voting_clf = VotingClassifier(
    estimators=[('lr', clf1), ('svc', clf2), ('dt', clf3), ('knn', clf4)],
    voting='soft'  # soft voting使用预测概率的加权平均
)

# 训练所有模型
clf1.fit(X_train_scaled, y_train)
clf2.fit(X_train_scaled, y_train)
clf3.fit(X_train_scaled, y_train)
clf4.fit(X_train_scaled, y_train)
voting_clf.fit(X_train_scaled, y_train)

# 预测
y_pred1 = clf1.predict(X_test_scaled)
y_pred2 = clf2.predict(X_test_scaled)
y_pred3 = clf3.predict(X_test_scaled)
y_pred4 = clf4.predict(X_test_scaled)
y_pred_voting = voting_clf.predict(X_test_scaled)

# 评估准确率
acc1 = accuracy_score(y_test, y_pred1)
acc2 = accuracy_score(y_test, y_pred2)
acc3 = accuracy_score(y_test, y_pred3)
acc4 = accuracy_score(y_test, y_pred4)
acc_voting = accuracy_score(y_test, y_pred_voting)

# 输出结果
print("Soft Voting集成学习结果：")
print(f"逻辑回归准确率: {acc1:.4f}")
print(f"SVM准确率: {acc2:.4f}")
print(f"决策树准确率: {acc3:.4f}")
print(f"KNN准确率: {acc4:.4f}")
print(f"集成模型准确率: {acc_voting:.4f}")

print("\n集成模型分类报告:")
print(classification_report(y_test, y_pred_voting))

# 绘制各模型准确率对比
models = ['逻辑回归', 'SVM', '决策树', 'KNN', '集成模型']
accuracies = [acc1, acc2, acc3, acc4, acc_voting]

plt.figure(figsize=(10, 6))
plt.bar(models, accuracies, color=['blue', 'green', 'red', 'purple', 'orange'])
plt.ylim(0.7, 1.0)
plt.ylabel('准确率')
plt.title('各模型准确率对比')
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(accuracies):
    plt.text(i, v + 0.01, f'{v:.4f}', ha='center')
plt.show()
