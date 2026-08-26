import numpy as np

# 1. 待优化函数（Rastrigin函数，多峰函数，最小值0）
def rastrigin(x):
    A = 10
    return A * len(x) + sum([xi**2 - A * np.cos(2 * np.pi * xi) for xi in x])

# 2. PSO核心实现
def pso_algorithm():
    np.random.seed(42)
    pop_size = 30  # 粒子数量
    n_iter = 100   # 迭代次数
    dim = 2        # 变量维度
    bounds = [-5.12, 5.12]  # 变量范围
    
    # 初始化粒子位置和速度
    x = np.random.uniform(bounds[0], bounds[1], (pop_size, dim))  # 位置
    v = np.random.uniform(-1, 1, (pop_size, dim))                 # 速度
    
    # 个体最优和全局最优
    p_best = x.copy()  # 每个粒子的最优位置
    p_best_val = np.array([rastrigin(ind) for ind in x])  # 个体最优值
    g_best_idx = np.argmin(p_best_val)  # 全局最优索引
    g_best = x[g_best_idx].copy()       # 全局最优位置
    
    # 迭代优化
    for _ in range(n_iter):
        # 更新速度和位置
        r1, r2 = np.random.rand(pop_size, dim), np.random.rand(pop_size, dim)
        w = 0.7       # 惯性权重
        c1, c2 = 2, 2 # 学习因子
        v = w * v + c1 * r1 * (p_best - x) + c2 * r2 * (g_best - x)
        x = np.clip(x + v, bounds[0], bounds[1])  # 位置限制
        
        # 更新最优解
        current_val = np.array([rastrigin(ind) for ind in x])
        # 更新个体最优
        mask = current_val < p_best_val
        p_best[mask] = x[mask]
        p_best_val[mask] = current_val[mask]
        # 更新全局最优
        current_g_best_idx = np.argmin(p_best_val)
        if p_best_val[current_g_best_idx] < rastrigin(g_best):
            g_best = p_best[current_g_best_idx].copy()
    
    return g_best, rastrigin(g_best)

# 3. 运行优化
best_sol, best_val = pso_algorithm()
print(f"PSO最优解：x1={best_sol[0]:.4f}, x2={best_sol[1]:.4f}")
print(f"最优函数值：{best_val:.4f}（理论最小值0）")
