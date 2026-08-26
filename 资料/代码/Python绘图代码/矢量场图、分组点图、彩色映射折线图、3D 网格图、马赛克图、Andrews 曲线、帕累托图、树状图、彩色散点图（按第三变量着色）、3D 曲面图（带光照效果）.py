import numpy as np
import matplotlib.pyplot as plt

# 最基础的中文显示设置
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

def plot1():
    """矢量场图（极简版）"""
    plt.figure()
    x = np.linspace(-2, 2, 10)
    y = np.linspace(-2, 2, 10)
    X, Y = np.meshgrid(x, y)
    U = -Y
    V = X
    plt.quiver(X, Y, U, V)
    plt.title('矢量场图')
    plt.tight_layout()

def plot2():
    """分组点图（极简版）"""
    plt.figure()
    for i in range(3):
        x = np.random.normal(i, 0.5, 30)
        y = np.random.normal(i, 0.5, 30)
        plt.scatter(x, y, label=f'组{i+1}')
    plt.title('分组点图')
    plt.legend()
    plt.tight_layout()

def plot3():
    """彩色折线图（极简版）"""
    plt.figure()
    x = np.linspace(0, 10, 200)
    y = np.sin(x)
    plt.scatter(x, y, c=x, cmap='viridis', s=10)
    plt.title('彩色映射折线图')
    plt.tight_layout()

def plot4():
    """3D网格图（极简版）"""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x = np.linspace(-3, 3, 10)
    y = np.linspace(-3, 3, 10)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) + np.cos(Y)
    ax.plot_wireframe(X, Y, Z)
    ax.set_title('3D网格图')
    plt.tight_layout()

def plot5():
    """马赛克图（极简版）"""
    plt.figure()
    data = [[0.4, 0.3, 0.3], [0.2, 0.5, 0.3], [0.5, 0.2, 0.3]]
    colors = ['#ff9999','#66b3ff','#99ff99']
    for i in range(3):
        bottom = 0
        for j in range(3):
            plt.bar(i, data[i][j], bottom=bottom, color=colors[j], width=0.5)
            bottom += data[i][j]
    plt.title('马赛克图')
    plt.tight_layout()

def plot6():
    """Andrews曲线（极简版）"""
    plt.figure()
    t = np.linspace(-np.pi, np.pi, 100)
    for _ in range(10):
        coeffs = np.random.randn(4)
        curve = coeffs[0] + coeffs[1]*np.sin(t) + coeffs[2]*np.cos(t) + coeffs[3]*np.sin(2*t)
        plt.plot(t, curve, alpha=0.5)
    plt.title('Andrews曲线')
    plt.tight_layout()

def plot7():
    """帕累托图（极简版）"""
    plt.figure()
    values = [50, 30, 10, 10]
    plt.bar(range(4), values)
    plt.plot(range(4), np.cumsum(values)/sum(values)*100, 'r-')
    plt.title('帕累托图')
    plt.tight_layout()

def plot8():
    """树状图（极简版）"""
    plt.figure()
    sizes = [40, 30, 20, 10]
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
    plt.bar(0, 100, width=100, color='white', edgecolor='black')
    x = 0
    for s, c in zip(sizes, colors):
        plt.bar(x, 100, width=s, color=c, edgecolor='white')
        x += s
    plt.title('树状图')
    plt.axis('off')
    plt.tight_layout()

def plot9():
    """彩色散点图（极简版）"""
    plt.figure()
    x = np.random.randn(100)
    y = np.random.randn(100)
    c = x + y
    plt.scatter(x, y, c=c)
    plt.title('彩色散点图')
    plt.tight_layout()

def plot10():
    """3D曲面图（极简版）"""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x = np.linspace(-3, 3, 20)
    y = np.linspace(-3, 3, 20)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.7)
    ax.set_title('3D曲面图')
    plt.tight_layout()

# 绘制所有图表
plot1()
plot2()
plot3()
plot4()
plot5()
plot6()
plot7()
plot8()
plot9()
plot10()

plt.show()
    