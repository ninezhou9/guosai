import numpy as np
import matplotlib.pyplot as plt

# 简化字体设置，避免找不到字体的问题
plt.rcParams["font.family"] = ["sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 环形图
def plot_donut():
    plt.figure(figsize=(6,6))
    labels = ['A', 'B', 'C', 'D']
    sizes = [30, 25, 25, 20]
    colors = ['#ff6666','#66b3ff','#99ff99','#ffcc99']
    
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            wedgeprops=dict(width=0.3, edgecolor='w'))
    plt.gca().add_artist(plt.Circle((0,0),0.7,fc='white'))
    plt.title('环形图')
    plt.axis('equal')
    plt.show()

# 雷达图
def plot_radar():
    plt.figure(figsize=(6,6))
    ax = plt.subplot(111, polar=True)
    labels = ['指标1', '指标2', '指标3', '指标4']
    values1 = [80, 90, 70, 60]
    values2 = [60, 70, 80, 90]
    
    angles = np.linspace(0, 2*np.pi, 4, endpoint=False).tolist()
    values1 += values1[:1]
    values2 += values2[:1]
    angles += angles[:1]
    
    ax.plot(angles, values1, 'b-', linewidth=2, label='数据1')
    ax.fill(angles, values1, 'b', alpha=0.2)
    ax.plot(angles, values2, 'g-', linewidth=2, label='数据2')
    ax.fill(angles, values2, 'g', alpha=0.2)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels([])
    plt.title('雷达图')
    plt.legend()
    plt.show()

# 热图
def plot_heat():
    plt.figure(figsize=(6,5))
    data = np.random.rand(5,5)  # 5x5随机数据
    plt.imshow(data, cmap='coolwarm')
    plt.colorbar(label='值')
    plt.title('热图')
    plt.xticks(range(5), [f'X{i}' for i in range(5)])
    plt.yticks(range(5), [f'Y{i}' for i in range(5)])
    plt.show()

# 相关性热图
def plot_corr_heat():
    plt.figure(figsize=(6,5))
    data = np.random.randn(5, 30)  # 5个变量，30个样本
    corr = np.corrcoef(data)
    plt.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(label='相关系数')
    plt.title('相关性热图')
    plt.xticks(range(5), [f'变量{i}' for i in range(5)])
    plt.yticks(range(5), [f'变量{i}' for i in range(5)])
    plt.show()

# 3D散点图
def plot_3d_scatter():
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='3d')
    x = np.random.rand(50)
    y = np.random.rand(50)
    z = np.random.rand(50)
    ax.scatter(x, y, z, c=z, cmap='viridis')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.title('3D散点图')
    plt.show()

# 3D曲面图
def plot_3d_surface():
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='3d')
    x = np.linspace(-3,3,20)
    y = np.linspace(-3,3,20)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x**2 + y**2))
    ax.plot_surface(x, y, z, cmap='coolwarm', alpha=0.8)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.title('3D曲面图')
    plt.show()

# 等高线图
def plot_contour():
    plt.figure(figsize=(6,5))
    x = np.linspace(-3,3,30)
    y = np.linspace(-3,3,30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x**2 + y**2))
    plt.contourf(x, y, z, 10, cmap='coolwarm')
    plt.colorbar(label='值')
    plt.title('等高线图')
    plt.show()

# 瀑布图（已修复形状不匹配问题）
def plot_waterfall():
    plt.figure(figsize=(6,5))
    labels = ['初始', '增1', '减1', '增2', '最终']
    values = [100, 30, -20, 40, 150]
    # 修复底部数据长度，使其与标签和值的长度匹配
    cumulative = [0, 100, 130, 110, 150]
    
    # 修复颜色列表长度，使其与数据长度匹配
    colors = ['blue'] 
    for v in values[1:-1]:
        colors.append('green' if v > 0 else 'red')
    colors.append('blue')
    
    # 确保所有数组长度一致
    plt.bar(labels, values, bottom=cumulative, 
            color=colors)
    plt.title('瀑布图')
    plt.grid(axis='y', linestyle='--')
    plt.show()

# 面积图
def plot_area():
    plt.figure(figsize=(6,5))
    x = [1,2,3,4,5,6]
    y1 = [10,15,12,18,20,25]
    y2 = [5,8,10,12,15,18]
    
    plt.fill_between(x, y1, alpha=0.4, color='blue', label='数据1')
    plt.fill_between(x, y2, alpha=0.4, color='green', label='数据2')
    plt.plot(x, y1, 'b-')
    plt.plot(x, y2, 'g-')
    plt.title('面积图')
    plt.legend()
    plt.show()

# 时间序列图
def plot_time_series():
    plt.figure(figsize=(6,5))
    x = range(12)  # 用数字代替日期，避免日期处理问题
    y1 = np.cumsum(np.random.randn(12)) + 20
    y2 = np.cumsum(np.random.randn(12)) + 10
    
    plt.plot(x, y1, 'b-', label='序列1')
    plt.plot(x, y2, 'r-', label='序列2')
    plt.xticks(x, [f'{i+1}月' for i in x])
    plt.title('时间序列图')
    plt.legend()
    plt.grid(axis='y', linestyle='--')
    plt.show()

# 绘制所有图表
if __name__ == "__main__":
    plot_donut()
    plot_radar()
    plot_heat()
    plot_corr_heat()
    plot_3d_scatter()
    plot_3d_surface()
    plot_contour()
    plot_waterfall()  # 已修复此函数的错误
    plot_area()
    plot_time_series()
    