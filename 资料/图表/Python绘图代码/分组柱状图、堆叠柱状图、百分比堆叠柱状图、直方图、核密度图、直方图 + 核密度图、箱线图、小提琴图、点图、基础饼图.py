import numpy as np
import matplotlib.pyplot as plt

# 最简化的字体设置，确保兼容性
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 基础样式设置
plt.rcParams["figure.figsize"] = (8, 5)
plt.rcParams["figure.dpi"] = 80
plt.rcParams["font.size"] = 12

# 1. 分组柱状图
def plot_grouped_bar():
    categories = ['产品A', '产品B', '产品C', '产品D', '产品E']
    group1 = [80, 95, 75, 110, 90]
    group2 = [65, 85, 70, 95, 80]
    group3 = [50, 70, 60, 85, 75]
    
    x = np.arange(len(categories))
    width = 0.25
    
    fig, ax = plt.subplots()
    ax.bar(x - width, group1, width, label='2021年')
    ax.bar(x, group2, width, label='2022年')
    ax.bar(x + width, group3, width, label='2023年')
    
    ax.set_xlabel('产品类别')
    ax.set_ylabel('销售额 (万元)')
    ax.set_title('不同年份各产品销售额对比')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    
    plt.tight_layout()
    plt.show()

# 2. 堆叠柱状图
def plot_stacked_bar():
    categories = ['一月', '二月', '三月', '四月', '五月', '六月']
    group1 = [40, 50, 45, 60, 55, 70]
    group2 = [20, 30, 25, 35, 30, 40]
    group3 = [10, 15, 12, 20, 18, 25]
    
    fig, ax = plt.subplots()
    ax.bar(categories, group1, label='产品X')
    ax.bar(categories, group2, bottom=group1, label='产品Y')
    ax.bar(categories, group3, bottom=np.array(group1)+np.array(group2), label='产品Z')
    
    ax.set_xlabel('月份')
    ax.set_ylabel('销量 (件)')
    ax.set_title('各月份产品销量堆叠图')
    ax.legend()
    
    plt.tight_layout()
    plt.show()

# 3. 百分比堆叠柱状图
def plot_percentage_stacked_bar():
    categories = ['华东', '华北', '华南', '西部', '东北']
    group1 = [50, 40, 60, 30, 45]
    group2 = [30, 35, 25, 40, 30]
    group3 = [20, 25, 15, 30, 25]
    
    total = np.array(group1) + np.array(group2) + np.array(group3)
    group1_perc = group1 / total * 100
    group2_perc = group2 / total * 100
    group3_perc = group3 / total * 100
    
    fig, ax = plt.subplots()
    ax.bar(categories, group1_perc, label='线上销售')
    ax.bar(categories, group2_perc, bottom=group1_perc, label='门店销售')
    ax.bar(categories, group3_perc, bottom=group1_perc+group2_perc, label='经销商')
    
    ax.set_xlabel('地区')
    ax.set_ylabel('销售占比 (%)')
    ax.set_title('各地区销售渠道占比')
    ax.legend()
    
    plt.tight_layout()
    plt.show()

# 4. 直方图
def plot_histogram():
    # 使用固定数据而非随机生成
    data = np.array([55, 62, 68, 72, 75, 78, 82, 85, 88, 92] * 50)
    data = np.append(data, [65, 68, 70, 73, 76, 80, 83, 86, 89, 95] * 35)
    
    fig, ax = plt.subplots()
    ax.hist(data, bins=20, alpha=0.7)
    
    ax.set_xlabel('分数')
    ax.set_ylabel('频数')
    ax.set_title('学生成绩分布直方图')
    
    plt.tight_layout()
    plt.show()

# 5. 核密度图
def plot_kde():
    # 使用固定数据点
    x1 = np.linspace(-3, 3, 100)
    kde1 = np.exp(-0.5 * x1**2) / np.sqrt(2 * np.pi)  # 标准正态分布
    
    x2 = np.linspace(0, 6, 100)
    kde2 = np.exp(-0.5 * ((x2 - 3) / 1.5)**2) / (1.5 * np.sqrt(2 * np.pi))  # 偏移正态分布
    
    fig, ax = plt.subplots()
    ax.plot(x1, kde1, label='组A')
    ax.plot(x2, kde2, label='组B')
    ax.fill_between(x1, kde1, alpha=0.3)
    ax.fill_between(x2, kde2, alpha=0.3)
    
    ax.set_xlabel('值')
    ax.set_ylabel('密度')
    ax.set_title('数据核密度分布图')
    ax.legend()
    
    plt.tight_layout()
    plt.show()

# 6. 直方图 + 核密度图
def plot_histogram_with_kde():
    # 固定数据
    data = np.array([30, 35, 40, 45, 50, 55, 60, 65, 70, 75] * 40)
    
    # 固定的核密度曲线
    x = np.linspace(20, 85, 100)
    kde = np.exp(-0.5 * ((x - 50) / 15)**2) / (15 * np.sqrt(2 * np.pi))
    
    fig, ax = plt.subplots()
    ax.hist(data, bins=15, density=True, alpha=0.6)
    ax.plot(x, kde, color='red', linewidth=2)
    
    ax.set_xlabel('数值')
    ax.set_ylabel('密度')
    ax.set_title('数据分布 (直方图 + 核密度图)')
    
    plt.tight_layout()
    plt.show()

# 7. 箱线图
def plot_boxplot():
    # 固定的四组数据
    data = [
        [45, 50, 55, 60, 65, 48, 52, 58, 62, 53],
        [55, 60, 65, 70, 75, 58, 62, 68, 72, 63],
        [35, 40, 45, 50, 55, 38, 42, 48, 52, 43],
        [65, 70, 75, 80, 85, 68, 72, 78, 82, 73]
    ]
    
    fig, ax = plt.subplots()
    bp = ax.boxplot(data, patch_artist=True)
    
    # 简单着色
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    
    ax.set_xticklabels(['A组', 'B组', 'C组', 'D组'])
    ax.set_ylabel('测量值')
    ax.set_title('四组数据的箱线图比较')
    
    plt.tight_layout()
    plt.show()

# 8. 小提琴图
def plot_violinplot():
    # 固定的三组数据
    data = [
        [ -2, -1, 0, 1, 2 ] * 40,  # 正态分布模拟
        [ 0, 1, 2, 3, 4 ] * 40,    # 偏态分布模拟
        [ -3, -2, -1, 0, 1, 2, 3 ] * 28  # 均匀分布模拟
    ]
    
    fig, ax = plt.subplots()
    parts = ax.violinplot(data, showmedians=True)
    
    # 简单着色
    for pc in parts['bodies']:
        pc.set_facecolor('lightgreen')
        pc.set_alpha(0.7)
    
    ax.set_xticklabels(['正态分布', '偏态分布', '均匀分布'])
    ax.set_ylabel('数值')
    ax.set_title('不同分布数据的小提琴图')
    
    plt.tight_layout()
    plt.show()

# 9. 点图
def plot_dotplot():
    categories = ['方法A', '方法B', '方法C', '方法D']
    # 固定的四组数据点
    data = [
        [5, 5.2, 5.4, 5.6, 5.8, 6.0, 6.2],
        [7, 7.2, 7.4, 7.6, 7.8, 8.0, 8.2],
        [9, 9.2, 9.4, 9.6, 9.8, 10.0, 10.2],
        [11, 11.2, 11.4, 11.6, 11.8, 12.0, 12.2]
    ]
    
    fig, ax = plt.subplots()
    for i, values in enumerate(data):
        y = [i + np.random.normal(0, 0.05) for _ in values]
        ax.scatter(values, y, alpha=0.7)
    
    # 平均值
    means = [np.mean(values) for values in data]
    ax.scatter(means, range(len(categories)), color='red', s=100, marker='X', label='平均值')
    
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories)
    ax.set_xlabel('性能指标')
    ax.set_title('不同方法的性能比较点图')
    ax.legend()
    
    plt.tight_layout()
    plt.show()

# 10. 基础饼图
def plot_piechart():
    labels = ['直接访问', '搜索引擎', '社交媒体', '广告推广', '外部链接']
    sizes = [30, 25, 20, 15, 10]
    
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # 保证饼图是正圆形
    ax.set_title('网站流量来源分布')
    
    plt.tight_layout()
    plt.show()

# 运行所有图表
if __name__ == "__main__":
    plot_grouped_bar()
    plot_stacked_bar()
    plot_percentage_stacked_bar()
    plot_histogram()
    plot_kde()
    plot_histogram_with_kde()
    plot_boxplot()
    plot_violinplot()
    plot_dotplot()
    plot_piechart()
