import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# 设置随机种子
np.random.seed(42)

# 蒙特卡洛模拟：计算π值
def estimate_pi(num_samples):
    # 在[0,1)x[0,1)范围内生成随机点
    x = np.random.rand(num_samples)
    y = np.random.rand(num_samples)
    
    # 计算到原点的距离
    distances = np.sqrt(x**2 + y**2)
    
    # 统计落在单位圆内的点
    inside_circle = distances <= 1
    num_inside = np.sum(inside_circle)
    
    # 估计π值（面积比 = π/4）
    pi_estimate = 4 * (num_inside / num_samples)
    
    return pi_estimate, x, y, inside_circle

# 蒙特卡洛模拟：计算积分
def estimate_integral(num_samples):
    # 积分函数: f(x) = x^2 在[0, 1]区间的积分
    x = np.random.rand(num_samples)
    y = np.random.rand(num_samples)  # y在[0,1)范围内
    
    # 函数值
    f_x = x**2
    
    # 统计在函数下方的点
    below_curve = y <= f_x
    num_below = np.sum(below_curve)
    
    # 估计积分值（面积比）
    integral_estimate = num_below / num_samples
    
    return integral_estimate, x, y, below_curve

# 执行模拟
num_samples = 10000
pi_estimate, x_pi, y_pi, inside_circle = estimate_pi(num_samples)
integral_estimate, x_int, y_int, below_curve = estimate_integral(num_samples)

# 输出结果
print("蒙特卡洛模拟结果：")
print(f"π的估计值: {pi_estimate:.6f}")
print(f"真实π值: {np.pi:.6f}")
print(f"误差: {abs(pi_estimate - np.pi):.6f}\n")

print(f"积分∫x²dx从0到1的估计值: {integral_estimate:.6f}")
print(f"真实积分值: {1/3:.6f}")
print(f"误差: {abs(integral_estimate - 1/3):.6f}")

# 绘制π估计的可视化
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.scatter(x_pi[inside_circle], y_pi[inside_circle], color='blue', s=1, alpha=0.6, label='圆内点')
plt.scatter(x_pi[~inside_circle], y_pi[~inside_circle], color='red', s=1, alpha=0.6, label='圆外点')
circle = Circle((0, 0), 1, fill=False, color='black')
plt.gca().add_patch(circle)
plt.gca().set_aspect('equal', adjustable='box')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.title(f'蒙特卡洛估计π: {pi_estimate:.6f}')
plt.legend(markerscale=5)

# 绘制积分估计的可视化
plt.subplot(1, 2, 2)
x_curve = np.linspace(0, 1, 100)
y_curve = x_curve**2
plt.plot(x_curve, y_curve, 'green', linewidth=2)
plt.scatter(x_int[below_curve], y_int[below_curve], color='blue', s=1, alpha=0.6, label='曲线下方')
plt.scatter(x_int[~below_curve], y_int[~below_curve], color='red', s=1, alpha=0.6, label='曲线上方')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.title(f'蒙特卡洛估计积分: {integral_estimate:.6f}')
plt.legend(markerscale=5)

plt.tight_layout()
plt.show()
