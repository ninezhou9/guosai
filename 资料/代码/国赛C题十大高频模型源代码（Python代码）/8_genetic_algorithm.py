import numpy as np
import matplotlib.pyplot as plt

# 设置随机种子
np.random.seed(42)

# 遗传算法参数
POPULATION_SIZE = 50        # 种群大小
GENES = 10                  # 基因数量（变量数量）
GENERATIONS = 100           # 进化代数
MUTATION_RATE = 0.1         # 突变率
CROSSOVER_RATE = 0.8        # 交叉率
LOWER_BOUND = -5.0          # 变量下界
UPPER_BOUND = 5.0           # 变量上界

# 适应度函数：Rastrigin函数（一个复杂的优化测试函数）
def fitness_function(individual):
    A = 10
    return A * len(individual) + sum([(x**2 - A * np.cos(2 * np.pi * x)) for x in individual])

# 初始化种群
population = np.random.uniform(
    low=LOWER_BOUND, 
    high=UPPER_BOUND, 
    size=(POPULATION_SIZE, GENES)
)

# 记录每代的最佳适应度
best_fitness_history = []

# 进化过程
for generation in range(GENERATIONS):
    # 计算适应度
    fitness = np.array([fitness_function(ind) for ind in population])
    
    # 记录最佳适应度
    best_idx = np.argmin(fitness)  # 因为我们要最小化目标函数
    best_fitness = fitness[best_idx]
    best_fitness_history.append(best_fitness)
    
    # 选择：轮盘赌选择（基于适应度的倒数，因为我们要最小化）
    # 转换为最大化问题
    min_fitness = np.min(fitness)
    adjusted_fitness = min_fitness + (np.max(fitness) - fitness)
    probabilities = adjusted_fitness / np.sum(adjusted_fitness)
    
    # 选择新种群
    selected_indices = np.random.choice(
        POPULATION_SIZE, 
        size=POPULATION_SIZE, 
        p=probabilities
    )
    selected_population = population[selected_indices]
    
    # 交叉
    new_population = []
    for i in range(0, POPULATION_SIZE, 2):
        parent1 = selected_population[i]
        if i + 1 < POPULATION_SIZE:
            parent2 = selected_population[i + 1]
        else:
            parent2 = selected_population[0]
            
        # 随机决定是否进行交叉
        if np.random.random() < CROSSOVER_RATE:
            # 单点交叉
            crossover_point = np.random.randint(1, GENES)
            child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
            child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])
            new_population.extend([child1, child2])
        else:
            new_population.extend([parent1, parent2])
    
    # 突变
    for i in range(POPULATION_SIZE):
        for j in range(GENES):
            if np.random.random() < MUTATION_RATE:
                # 高斯突变
                mutation = np.random.normal(0, 0.5)
                new_population[i][j] += mutation
                # 确保在边界内
                new_population[i][j] = np.clip(
                    new_population[i][j], 
                    LOWER_BOUND, 
                    UPPER_BOUND
                )
    
    # 更新种群
    population = np.array(new_population[:POPULATION_SIZE])

# 最终结果
final_fitness = np.array([fitness_function(ind) for ind in population])
best_idx = np.argmin(final_fitness)
best_individual = population[best_idx]
best_final_fitness = final_fitness[best_idx]

# 输出结果
print("遗传算法结果：")
print(f"最佳个体: {best_individual}")
print(f"最佳适应度值: {best_final_fitness:.4f}")

# 绘制适应度进化曲线
plt.figure(figsize=(10, 6))
plt.plot(best_fitness_history)
plt.xlabel('代数')
plt.ylabel('最佳适应度值')
plt.title('遗传算法进化曲线')
plt.grid(True, alpha=0.3)
plt.show()
