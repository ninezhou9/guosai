import numpy as np
import matplotlib.pyplot as plt

# 设置随机种子
np.random.seed(42)

# 排队系统参数
lambda_rate = 3.0  # 到达率（顾客/单位时间）
mu_rate = 4.0      # 服务率（顾客/单位时间）
max_customers = 20 # 最大顾客数
simulation_time = 50.0  # 模拟时间

# 理论计算
rho = lambda_rate / mu_rate  # 系统利用率
if rho < 1:
    p0 = 1 - rho  # 系统空闲概率
    L = rho / (1 - rho)  # 系统中平均顾客数
    Lq = rho**2 / (1 - rho)  # 队列中平均顾客数
    W = 1 / (mu_rate - lambda_rate)  # 系统中平均等待时间
    Wq = rho / (mu_rate - lambda_rate)  # 队列中平均等待时间
else:
    print("警告：系统不稳定（到达率 >= 服务率）")
    p0 = 0
    L = np.inf
    Lq = np.inf
    W = np.inf
    Wq = np.inf

# 模拟生灭过程
current_time = 0.0
num_customers = 0
event_times = []
num_customers_history = []

while current_time < simulation_time:
    event_times.append(current_time)
    num_customers_history.append(num_customers)
    
    if num_customers == 0:
        # 只有到达事件可能发生
        next_arrival = np.random.exponential(1 / lambda_rate)
        current_time += next_arrival
        num_customers += 1
    else:
        # 到达和离开事件都可能发生
        next_arrival = np.random.exponential(1 / lambda_rate)
        next_departure = np.random.exponential(1 / mu_rate)
        
        if next_arrival < next_departure:
            # 到达事件先发生
            current_time += next_arrival
            if num_customers < max_customers:
                num_customers += 1
        else:
            # 离开事件先发生
            current_time += next_departure
            num_customers -= 1

# 计算模拟结果
avg_customers = np.mean(num_customers_history)
busy_time_ratio = 1 - (num_customers_history.count(0) / len(num_customers_history))

# 输出结果
print("排队论（生灭过程）结果：")
print("理论值：")
print(f"系统利用率: {rho:.4f}")
print(f"系统空闲概率: {p0:.4f}")
print(f"系统中平均顾客数: {L:.4f}")
print(f"队列中平均顾客数: {Lq:.4f}")
print(f"系统中平均等待时间: {W:.4f}")
print(f"队列中平均等待时间: {Wq:.4f}\n")

print("模拟值：")
print(f"平均顾客数: {avg_customers:.4f}")
print(f"系统繁忙率: {busy_time_ratio:.4f}")

# 绘制系统中顾客数随时间变化
plt.figure(figsize=(10, 6))
plt.step(event_times, num_customers_history, where='post')
plt.xlabel('时间')
plt.ylabel('系统中顾客数')
plt.title('生灭过程模拟 - 系统中顾客数随时间变化')
plt.grid(True, alpha=0.3)
plt.show()
