import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import matplotlib.colors as mcolors
import matplotlib

# 优化中文字体配置，使用更通用的字体方案
plt.rcParams["font.family"] = ["Microsoft YaHei", "WenQuanYi Micro Hei", "Heiti TC", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 检测并显示当前使用的字体
def check_font():
    try:
        # 尝试获取配置的字体
        font = matplotlib.font_manager.findfont(matplotlib.font_manager.FontProperties(family=plt.rcParams["font.family"]))
        print(f"当前使用的字体: {font}")
        return True
    except:
        print("警告: 未找到指定的中文字体，尝试备选方案...")
        # 简化的字体检测方案
        available_fonts = set()
        font_manager = matplotlib.font_manager.FontManager()
        for font in font_manager.ttflist:
            available_fonts.add(font.name)
        
        # 常见中文字体列表
        chinese_fonts = ["WenQuanYi Micro Hei", "Heiti TC", "SimHei", 
                        "Microsoft YaHei", "Arial Unicode MS", "SimSun", "NSimSun"]
        
        # 查找可用的中文字体
        for font in chinese_fonts:
            if font in available_fonts:
                plt.rcParams["font.family"] = [font, "sans-serif"]
                print(f"已自动切换到可用字体: {font}")
                return True
        
        # 如果没有找到中文字体，使用默认字体并警告
        print("警告: 系统中未找到可用的中文字体，中文可能无法正常显示。")
        print("建议安装WenQuanYi Micro Hei或SimHei等中文字体。")
        return False

# 设置图表风格
plt.style.use('seaborn-v0_8-dark-palette')
# 设置默认图像大小和分辨率
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["figure.dpi"] = 100

# 1. 基础散点图
def plot_scatter_basic():
    np.random.seed(42)
    x = np.random.randn(100) * 10
    y = 2 * x + np.random.randn(100) * 15 + 50
    
    plt.figure()
    plt.scatter(x, y, c='#2c7fb8', alpha=0.7, edgecolors='w', s=80, linewidth=1.5)
    plt.title('基础散点图', fontsize=16, pad=20)
    plt.xlabel('X轴数据', fontsize=12, labelpad=10)
    plt.ylabel('Y轴数据', fontsize=12, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 2. 带趋势线的散点图
def plot_scatter_with_trend():
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    y = 3 * x + 15 + np.random.randn(100) * 5
    
    # 计算趋势线
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    trend_line = slope * x + intercept
    
    plt.figure()
    plt.scatter(x, y, c='#e41a1c', alpha=0.6, edgecolors='w', s=60, linewidth=1, label='数据点')
    plt.plot(x, trend_line, 'b--', linewidth=2.5, 
             label=f'趋势线: y = {slope:.2f}x + {intercept:.2f}\nR² = {r_value**2:.4f}')
    plt.title('带趋势线的散点图', fontsize=16, pad=20)
    plt.xlabel('X轴', fontsize=12, labelpad=10)
    plt.ylabel('Y轴', fontsize=12, labelpad=10)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 3. 分组散点图
def plot_scatter_grouped():
    np.random.seed(42)
    groups = 4
    points_per_group = 50
    
    # 生成四组不同的数据
    x = [np.random.normal(i*3, 1.2, points_per_group) for i in range(groups)]
    y = [np.random.normal(i*2 + 5, 1.0, points_per_group) for i in range(groups)]
    labels = ['组A', '组B', '组C', '组D']
    colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c']
    markers = ['o', 's', '^', 'D']
    
    plt.figure()
    for i in range(groups):
        plt.scatter(x[i], y[i], c=colors[i], label=labels[i], alpha=0.7, 
                   edgecolors='w', s=70, marker=markers[i], linewidth=1.5)
    
    plt.title('分组散点图', fontsize=16, pad=20)
    plt.xlabel('X轴指标', fontsize=12, labelpad=10)
    plt.ylabel('Y轴指标', fontsize=12, labelpad=10)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 4. 气泡图
def plot_bubble():
    np.random.seed(42)
    n = 50
    x = np.random.rand(n) * 100  # X坐标
    y = np.random.rand(n) * 100  # Y坐标
    sizes = np.random.rand(n) * 500 + 50  # 气泡大小
    colors = np.random.rand(n)  # 颜色值
    
    plt.figure()
    scatter = plt.scatter(x, y, s=sizes, c=colors, alpha=0.7, 
                         edgecolors='w', linewidth=1, cmap='viridis')
    
    # 添加颜色条
    cbar = plt.colorbar(scatter)
    cbar.set_label('重要程度', fontsize=12, labelpad=10)
    
    plt.title('气泡图', fontsize=16, pad=20)
    plt.xlabel('市场份额 (%)', fontsize=12, labelpad=10)
    plt.ylabel('增长率 (%)', fontsize=12, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 5. 基础折线图
def plot_line_basic():
    np.random.seed(42)
    x = np.linspace(0, 12, 100)
    y = np.sin(x) * 10 + 50 + np.random.randn(100) * 2
    
    plt.figure()
    plt.plot(x, y, color='#984ea3', linewidth=2.5, linestyle='-', 
             marker='o', markersize=6, markerfacecolor='#ffff99', 
             markeredgecolor='#984ea3', markeredgewidth=1.5)
    
    plt.title('基础折线图', fontsize=16, pad=20)
    plt.xlabel('时间', fontsize=12, labelpad=10)
    plt.ylabel('数值', fontsize=12, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 6. 多系列折线图
def plot_line_multi_series():
    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    
    # 生成三个不同的系列
    y1 = np.sin(x) * 10 + 50 + np.random.randn(50) * 1.5
    y2 = np.cos(x) * 8 + 30 + np.random.randn(50) * 1.2
    y3 = (np.sin(x) + np.cos(x)) * 5 + 20 + np.random.randn(50) * 1.0
    
    plt.figure()
    plt.plot(x, y1, label='系列一', color='#e41a1c', linewidth=2, 
             marker='o', markersize=5, alpha=0.8)
    plt.plot(x, y2, label='系列二', color='#377eb8', linewidth=2, 
             linestyle='--', marker='s', markersize=5, alpha=0.8)
    plt.plot(x, y3, label='系列三', color='#4daf4a', linewidth=2, 
             linestyle='-.', marker='^', markersize=5, alpha=0.8)
    
    plt.title('多系列折线图', fontsize=16, pad=20)
    plt.xlabel('时间', fontsize=12, labelpad=10)
    plt.ylabel('数值', fontsize=12, labelpad=10)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 7. 带误差线的折线图
def plot_line_with_error():
    np.random.seed(42)
    x = np.arange(1, 13)  # 12个数据点，例如12个月
    y = np.sin(x/2) * 10 + 50 + np.random.randn(12) * 3
    y_err = np.random.rand(12) * 4 + 1  # 误差值
    
    plt.figure()
    plt.errorbar(x, y, yerr=y_err, fmt='-o', ecolor='#fb9a99', elinewidth=2,
                 capsize=5, capthick=2, color='#e41a1c', linewidth=2.5, 
                 markersize=8, markerfacecolor='#ffffff', markeredgewidth=2)
    
    plt.title('带误差线的折线图', fontsize=16, pad=20)
    plt.xlabel('月份', fontsize=12, labelpad=10)
    plt.ylabel('测量值', fontsize=12, labelpad=10)
    plt.xticks(x)  # 显示所有x刻度
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 8. 阶梯折线图
def plot_step_line():
    np.random.seed(42)
    x = np.linspace(0, 10, 20)
    y = np.cumsum(np.random.randn(20) * 2 + 5)  # 累积和，模拟某种指标变化
    
    plt.figure()
    plt.step(x, y, where='mid', color='#ff7f00', linewidth=2.5, 
             marker='s', markersize=8, markerfacecolor='#ffffcc', 
             markeredgecolor='#ff7f00', markeredgewidth=2)
    
    plt.title('阶梯折线图', fontsize=16, pad=20)
    plt.xlabel('时间点', fontsize=12, labelpad=10)
    plt.ylabel('累计值', fontsize=12, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 9. 基础柱状图
def plot_bar_basic():
    np.random.seed(42)
    categories = ['产品A', '产品B', '产品C', '产品D', '产品E', '产品F']
    values = np.random.randint(50, 200, len(categories))
    
    plt.figure()
    bars = plt.bar(categories, values, 
                   color=plt.cm.viridis(np.linspace(0, 0.9, len(categories))), 
                   edgecolor='w', linewidth=1.5)
    
    # 添加数据标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 3,
                f'{height}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.title('基础柱状图', fontsize=16, pad=20)
    plt.xlabel('产品类别', fontsize=12, labelpad=10)
    plt.ylabel('销量', fontsize=12, labelpad=10)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 10. 水平柱状图
def plot_bar_horizontal():
    np.random.seed(42)
    categories = ['地区A', '地区B', '地区C', '地区D', '地区E', '地区F']
    values = np.random.randint(100, 500, len(categories))
    
    plt.figure()
    bars = plt.barh(categories, values, 
                    color=plt.cm.plasma(np.linspace(0.2, 0.9, len(categories))), 
                    edgecolor='w', linewidth=1.5)
    
    # 添加数据标签
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 10, bar.get_y() + bar.get_height()/2.,
                f'{width}', va='center', fontsize=10, fontweight='bold')
    
    plt.title('水平柱状图', fontsize=16, pad=20)
    plt.xlabel('销售额', fontsize=12, labelpad=10)
    plt.ylabel('地区', fontsize=12, labelpad=10)
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# 运行所有图表
if __name__ == "__main__":
    # 检查字体配置，如果失败则提示用户
    font_available = check_font()
    if not font_available:
        print("注意：由于缺少中文字体，图表中的中文可能无法正常显示。")
    
    plot_scatter_basic()
    plot_scatter_with_trend()
    plot_scatter_grouped()
    plot_bubble()
    plot_line_basic()
    plot_line_multi_series()
    plot_line_with_error()
    plot_step_line()
    plot_bar_basic()
    plot_bar_horizontal()
