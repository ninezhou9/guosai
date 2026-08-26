import numpy as np
import matplotlib.pyplot as plt
import simpy

# 设置随机种子
np.random.seed(42)

# 模拟参数
SIMULATION_TIME = 100.0  # 模拟时间
INTER_ARRIVAL_TIME = 2.0  # 平均到达间隔时间
SERVICE_TIME = 1.5  # 平均服务时间
NUM_SERVERS = 2  # 服务器数量

# 存储结果的数据结构
wait_times = []
service_times = []
queue_lengths = []
times = []

# 顾客生成函数
def customer_generator(env, inter_arrival_time, server_resource):
    customer_id = 0
    while True:
        # 生成下一个顾客到达的时间间隔
        arrival_time = np.random.exponential(inter_arrival_time)
        yield env.timeout(arrival_time)
        customer_id += 1
        env.process(customer_service(env, customer_id, server_resource))

# 顾客服务函数
def customer_service(env, customer_id, server_resource):
    arrival_time = env.now
    
    # 记录队列长度
    queue_lengths.append(len(server_resource.queue))
    times.append(env.now)
    
    # 请求服务器资源
    with server_resource.request() as request:
        yield request
        
        # 计算等待时间
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)
        
        # 生成服务时间
        service_time = np.random.exponential(SERVICE_TIME)
        service_times.append(service_time)
        
        # 提供服务
        yield env.timeout(service_time)

# 运行模拟
env = simpy.Environment()
server = simpy.Resource(env, capacity=NUM_SERVERS)
env.process(customer_generator(env, INTER_ARRIVAL_TIME, server))
env.run(until=SIMULATION_TIME)

# 输出结果
print("队列模拟结果：")
print(f"模拟时间: {SIMULATION_TIME}")
print(f"顾客总数: {len(wait_times)}")
print(f"平均等待时间: {np.mean(wait_times):.4f}")
print(f"平均服务时间: {np.mean(service_times):.4f}")
print(f"最大等待时间: {np.max(wait_times):.4f}")
print(f"平均队列长度: {np.mean(queue_lengths):.4f}")

# 绘制队列长度随时间变化
plt.figure(figsize=(10, 6))
plt.step(times, queue_lengths, where='post')
plt.xlabel('时间')
plt.ylabel('队列长度')
plt.title('队列长度随时间变化')
plt.grid(True, alpha=0.3)
plt.show()
