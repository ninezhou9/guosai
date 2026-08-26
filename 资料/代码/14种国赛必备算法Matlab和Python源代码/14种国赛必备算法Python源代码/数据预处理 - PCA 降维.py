import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 1. 生成高维数据（5个特征，含相关性）
np.random.seed(42)
n = 200
feature1 = np.random.normal(0, 1, n)
feature2 = 0.8*feature1 + np.random.normal(0, 0.5, n)  # 与feature1相关
feature3 = 0.7*feature1 + 0.2*feature2 + np.random.normal(0, 0.4, n)
feature4 = np.random.normal(1, 1, n)  # 独立特征
feature5 = 0.6*feature4 + np.random.normal(0, 0.6, n)
data = pd.DataFrame({
    "f1": feature1, "f2": feature2, "f3": feature3, "f4": feature4, "f5": feature5
})

# 2. PCA降维步骤
# 标准化
scaler = StandardScaler()
data_std = scaler.fit_transform(data)

# 拟合PCA
pca = PCA()
pca_result = pca.fit_transform(data_std)

# 3. 结果分析
explained_var = pca.explained_variance_ratio_
cum_var = np.cumsum(explained_var)
print("主成分解释方差比：")
for i in range(len(explained_var)):
    print(f"主成分{i+1}：{explained_var[i]:.4f}（累计：{cum_var[i]:.4f}）")

# 确定保留主成分数（累计方差≥85%）
n_components = np.argmax(cum_var >= 0.85) + 1
print(f"\n需保留的主成分数：{n_components}")

# 降维后的数据形状
data_pca = pca_result[:, :n_components]
print(f"降维后数据形状：{data_pca.shape}（原形状：{data.shape}）")
