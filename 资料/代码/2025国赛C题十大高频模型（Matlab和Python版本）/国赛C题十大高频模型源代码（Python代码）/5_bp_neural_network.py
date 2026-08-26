import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 生成回归数据
np.random.seed(42)
X, y = make_regression(
    n_samples=500, n_features=5, noise=0.1,
    random_state=42
)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# 数据标准化
scaler_X = StandardScaler()
scaler_y = StandardScaler()

X_train_scaled = scaler_X.fit_transform(X_train)
X_test_scaled = scaler_X.transform(X_test)
y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()

# 创建并训练BP神经网络
model = MLPRegressor(
    hidden_layer_sizes=(10, 5),  # 两个隐藏层，分别有10和5个神经元
    activation='relu',           # 激活函数
    solver='adam',               # 优化器
    max_iter=1000,               # 最大迭代次数
    random_state=42,             # 随机种子
    verbose=False
)

model.fit(X_train_scaled, y_train_scaled)

# 预测
y_pred_scaled = model.predict(X_test_scaled)
y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()

# 评估
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# 输出结果
print("BP神经网络结果：")
print(f"均方误差 (MSE): {mse:.4f}")
print(f"决定系数 (R²): {r2:.4f}")
print(f"迭代次数: {model.n_iter_}")

# 绘制预测值与真实值对比
plt.figure(figsize=(8, 6))
plt.scatter(y_test, y_pred, alpha=0.6)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel('真实值')
plt.ylabel('预测值')
plt.title('预测值 vs 真实值')
plt.grid(True, alpha=0.3)
plt.show()

# 绘制损失函数曲线
plt.figure(figsize=(8, 6))
plt.plot(model.loss_curve_)
plt.xlabel('迭代次数')
plt.ylabel('损失值')
plt.title('训练损失曲线')
plt.grid(True, alpha=0.3)
plt.show()
