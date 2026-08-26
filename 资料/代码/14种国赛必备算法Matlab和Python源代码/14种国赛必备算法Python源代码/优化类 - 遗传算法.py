import numpy as np

# 1. 待优化函数（求最小值：f(x1,x2) = x1² + x2²）
def objective_function(individual):
    x1, x2 = individual
    return x1**2 + x2**2

# 2. 遗传算法核心实现
def genetic_algorithm():
    np.random.seed(42)
    pop_size = 50  # 种群大小
    n_iter = 100   # 迭代次数
    dim = 2        # 变量维度（x1, x2）
    bounds = [-10, 10]  # 变量范围
    
    # 初始化种群
    population = np.random.uniform(bounds[0], bounds[1], (pop_size, dim))
    
    for _ in range(n_iter):
        # 计算适应度（函数值越小，适应度越高）
        fitness = np.array([1 / (objective_function(ind) + 1e-10) for ind in population])
        # 轮盘赌选择
        prob = fitness / fitness.sum()
        selected_indices = np.random.choice(pop_size, size=pop_size, p=prob)
        selected = population[selected_indices]
        
        # 交叉操作（单点交叉）
        for i in range(0, pop_size, 2):
            if np.random.rand() < 0.8:  # 交叉概率80%
                cross_point = np.random.randint(1, dim)
                selected[i, cross_point:], selected[i+1, cross_point:] = \
                selected[i+1, cross_point:].copy(), selected[i, cross_point:].copy()
        
        # 变异操作（高斯变异）
        for i in range(pop_size):
            if np.random.rand() < 0.1:  # 变异概率10%
                mutate_idx = np.random.randint(dim)
                selected[i, mutate_idx] += np.random.normal(0, 0.5)
                # 边界处理
                selected[i, mutate_idx] = np.clip(selected[i, mutate_idx], bounds[0], bounds[1])
        
        population = selected
    
    # 找到最优解
    best_idx = np.argmin([objective_function(ind) for ind in population])
    best_solution = population[best_idx]
    return best_solution, objective_function(best_solution)

# 3. 运行优化
best_sol, best_val = genetic_algorithm()
print(f"遗传算法最优解：x1={best_sol[0]:.4f}, x2={best_sol[1]:.4f}")
print(f"最优函数值：{best_val:.4f}（理论最小值0）")
