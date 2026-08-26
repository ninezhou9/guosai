import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

# 基础设置 - 确保中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 100


def plot_double_y_axis():
    """双Y轴折线图"""
    x = np.linspace(0, 10, 100)
    y1 = np.exp(x/10)
    y2 = np.sin(x) * 10 + 30

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # 第一个Y轴
    ax1.plot(x, y1, 'b-', linewidth=2)
    ax1.set_xlabel('X轴')
    ax1.set_ylabel('系列1', color='b')
    ax1.tick_params('y', colors='b')

    # 第二个Y轴
    ax2 = ax1.twinx()
    ax2.plot(x, y2, 'r--', linewidth=2)
    ax2.set_ylabel('系列2', color='r')
    ax2.tick_params('y', colors='r')

    plt.title('双Y轴折线图')
    plt.tight_layout()
    plt.show()


def plot_filled_line_chart():
    """带填充区域的折线图"""
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.plot(x, y1, 'b-', label='正弦')
    ax.plot(x, y2, 'r-', label='余弦')
    ax.fill_between(x, y1, y2, where=(y1 >= y2), color='blue', alpha=0.2)
    ax.fill_between(x, y1, y2, where=(y1 < y2), color='red', alpha=0.2)
    
    ax.set_title('带填充区域的折线图')
    ax.set_xlabel('X轴')
    ax.set_ylabel('Y轴')
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_grouped_boxplot():
    """分组箱线图"""
    np.random.seed(10)
    data1 = [np.random.normal(0, std, 50) for std in range(1, 4)]
    data2 = [np.random.normal(3, std, 50) for std in range(1, 4)]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    bp1 = ax.boxplot(data1, positions=[1, 2, 3], widths=0.3, 
                    patch_artist=True, boxprops=dict(facecolor="lightblue"))
    bp2 = ax.boxplot(data2, positions=[1.5, 2.5, 3.5], widths=0.3, 
                    patch_artist=True, boxprops=dict(facecolor="lightgreen"))
    
    ax.set_title('分组箱线图')
    ax.set_xlabel('类别')
    ax.set_ylabel('数值')
    ax.set_xticks([1.25, 2.25, 3.25])
    ax.set_xticklabels(['A', 'B', 'C'])
    ax.legend([bp1["boxes"][0], bp2["boxes"][0]], ['组1', '组2'])
    plt.tight_layout()
    plt.show()


def plot_3d_bar_chart():
    """3D柱状图"""
    x = np.arange(5)
    y = np.arange(5)
    x, y = np.meshgrid(x, y)
    
    x = x.flatten()
    y = y.flatten()
    z = np.zeros_like(x)
    dz = np.random.randint(1, 15, size=x.size)
    
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.bar3d(x, y, z, 0.8, 0.8, dz, color=cm.viridis(dz/max(dz)), alpha=0.7)
    
    ax.set_title('3D柱状图')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('高度')
    plt.tight_layout()
    plt.show()


def plot_3d_contour():
    """3D等高线图"""
    x = np.linspace(-3, 3, 50)
    y = np.linspace(-3, 3, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2))
    
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, alpha=0.8)
    fig.colorbar(surf, shrink=0.5, aspect=5)
    
    ax.set_title('3D等高线图')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.tight_layout()
    plt.show()


def plot_horizontal_errorbar():
    """横向误差棒图"""
    y = np.arange(8)
    x = np.random.rand(8) * 100
    xerr = np.random.rand(8) * 8 + 2
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.errorbar(x, y, xerr=xerr, fmt='o', ecolor='red', capsize=5,
                markerfacecolor='blue')
    
    ax.set_title('横向误差棒图')
    ax.set_xlabel('测量值')
    ax.set_ylabel('样本')
    ax.set_yticks(y)
    ax.set_yticklabels([f'样本{i+1}' for i in y])
    plt.tight_layout()
    plt.show()


def plot_matrix_scatter():
    """矩阵散点图"""
    np.random.seed(42)
    n = 50
    v1 = np.random.normal(0, 1, n)
    v2 = np.random.normal(2, 1, n)
    v3 = np.random.normal(-1, 0.8, n)
    vars = [v1, v2, v3]
    names = ['变量1', '变量2', '变量3']
    
    fig, axes = plt.subplots(3, 3, figsize=(9, 9))
    fig.suptitle('矩阵散点图')
    
    for i in range(3):
        for j in range(3):
            ax = axes[i, j]
            if i != j:
                ax.scatter(vars[j], vars[i], alpha=0.6, s=20)
            else:
                ax.hist(vars[i], bins=10, alpha=0.7)
            
            if i == 2:
                ax.set_xlabel(names[j])
            if j == 0:
                ax.set_ylabel(names[i])
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.show()


def plot_stacked_area():
    """堆叠面积图"""
    x = np.arange(2010, 2021)
    data = np.random.randint(5, 30, size=(3, len(x)))
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.stackplot(x, data, labels=['A', 'B', 'C'], 
                colors=['#66b3ff', '#99ff99', '#ffcc99'], alpha=0.8)
    
    ax.set_title('堆叠面积图')
    ax.set_xlabel('年份')
    ax.set_ylabel('数值')
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_bar_with_labels():
    """带数据标签的柱状图"""
    categories = ['一月', '二月', '三月', '四月', '五月']
    values1 = np.random.randint(30, 80, size=5)
    values2 = np.random.randint(20, 60, size=5)
    
    x = np.arange(len(categories))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    rects1 = ax.bar(x - width/2, values1, width, label='系列1', color='lightblue')
    rects2 = ax.bar(x + width/2, values2, width, label='系列2', color='lightgreen')
    
    # 添加标签
    for rect in rects1:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height+1,
                f'{height}', ha='center', va='bottom')
    
    for rect in rects2:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height+1,
                f'{height}', ha='center', va='bottom')
    
    ax.set_title('带数据标签的柱状图')
    ax.set_xlabel('月份')
    ax.set_ylabel('数值')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_polar_line():
    """极坐标折线图"""
    theta = np.linspace(0, 2*np.pi, 100)
    r1 = 2 + np.sin(theta)*2
    r2 = 1 + np.cos(theta)*2
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.plot(theta, r1, 'b-', label='曲线1')
    ax.plot(theta, r2, 'r--', label='曲线2')
    
    ax.set_title('极坐标折线图')
    ax.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 依次显示所有图表
    plot_double_y_axis()
    plot_filled_line_chart()
    plot_grouped_boxplot()
    plot_3d_bar_chart()
    plot_3d_contour()
    plot_horizontal_errorbar()
    plot_matrix_scatter()
    plot_stacked_area()
    plot_bar_with_labels()
    plot_polar_line()
