import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 生成三维数据
np.random.seed(42)
mean = [0, 0, 0]
cov = [[1, 0.8, 0.3], [0.8, 1, 0.2], [0.3, 0.2, 1]]
data = np.random.multivariate_normal(mean, cov, 100)

# 数据标准化
scaler = StandardScaler()
scaled_data = scaler.fit_transform(data)

# 应用PCA降维到2维
pca = PCA(n_components=2)
pca_result = pca.fit_transform(scaled_data)

# 输出解释方差比
print("主成分分析（PCA）结果：")
print(f"解释方差比: {pca.explained_variance_ratio_}")
print(f"累计解释方差比: {sum(pca.explained_variance_ratio_):.4f}")

# 绘制结果
plt.figure(figsize=(8, 6))
plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.7)
plt.xlabel('主成分1')
plt.ylabel('主成分2')
plt.title('PCA降维结果')
plt.grid(True)
plt.show()
