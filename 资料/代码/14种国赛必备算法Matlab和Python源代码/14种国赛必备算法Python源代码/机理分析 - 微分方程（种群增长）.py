import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# 1. 定义Logistic增长微分方程
def logistic_model(N, t, r, K):
    """
    dN/dt = r*N*(1 - N/K)
    N: 种群数量
    r: 增长率
    K: 环境容纳量
    """
    return r * N * (1 - N / K)

# 2. 求解微分方程
t = np.linspace(0, 20, 100)  # 时间范围0~20年
N0 = 100                     # 初始种群数量
r = 0.5                      # 增长率
K = 1000                     # 环境最大容量

# 数值求解
N = odeint(logistic_model, N0, t, args=(r, K))

# 3. 输出结果
print("种群增长预测（前10年）：")
for i in range(10):
    print(f"第{t[i]:.0f}年：{N[i][0]:.0f}")
print(f"\n长期稳定种群数量：{N[-1][0]:.0f}（接近K={K}）")

# 4. 可视化（可选）
plt.plot(t, N)
plt.xlabel("时间（年）")
plt.ylabel("种群数量")
plt.title("Logistic种群增长模型")
plt.grid(alpha=0.3)
plt.show()
