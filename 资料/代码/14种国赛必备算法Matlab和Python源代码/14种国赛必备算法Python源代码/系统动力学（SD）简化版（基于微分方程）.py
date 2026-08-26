import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# 1. SIR模型微分方程（易感者-感染者-康复者）
def sir_model(y, t, beta, gamma):
    S, I, R = y
    N = S + I + R  # 总人数
    dSdt = -beta * S * I / N  # 易感者变化率
    dIdt = beta * S * I / N - gamma * I  # 感染者变化率
    dRdt = gamma * I  # 康复者变化率
    return dSdt, dIdt, dRdt

# 2. 初始条件与参数
initial_conditions = (999, 1, 0)  # S0, I0, R0
t = np.linspace(0, 100, 100)  # 时间范围
beta = 0.3  # 传染率
gamma = 0.1  # 康复率

# 3. 求解微分方程
solution = odeint(sir_model, initial_conditions, t, args=(beta, gamma))
S, I, R = solution.T

# 4. 输出结果
print("SIR模型传染病模拟（前10天）：")
for i in range(10):
    print(f"第{i}天：易感者={int(S[i])}, 感染者={int(I[i])}, 康复者={int(R[i])}")

# 5. 可视化（可选）
plt.plot(t, S, label="易感者")
plt.plot(t, I, label="感染者")
plt.plot(t, R, label="康复者")
plt.xlabel("时间（天）")
plt.ylabel("人数")
plt.legend()
plt.show()
