import numpy as np

# 1. 定义多目标优化问题
def objective_1(x):
    """目标1：成本（越小越好）"""
    x1, x2 = x
    return x1**2 + x2**2

def objective_2(x):
    """目标2：效率（越大越好，后续转为最小化问题）"""
    x1, x2 = x
    return -(2*x1 + 3*x2 - (x1*x2)/5)  # 取负号转为最小化

def evaluate(x):
    """评估个体的两个目标值"""
    return [objective_1(x), objective_2(x)]

# 2. 非支配排序（核心NSGA-II逻辑）
def non_dominated_sort(population, objectives):
    """
    对种群进行非支配排序
    返回：每个个体的排序等级（rank）和支配计数
    """
    n = len(population)
    rank = [0]*n
    dominated = [[] for _ in range(n)]  # 被当前个体支配的个体列表
    domination_count = [0]*n  # 支配当前个体的个体数量
    
    # 计算支配关系
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # 检查i是否支配j
            i_dominates_j = True
            for o in range(2):  # 两个目标
                if objectives[i][o] > objectives[j][o]:
                    i_dominates_j = False
                    break
            if i_dominates_j:
                dominated[i].append(j)
                domination_count[j] += 1
    
    # 计算排序等级
    rank = [0]*n
    current_rank = 0
    while True:
        # 找到当前等级的个体（被支配计数为0）
        current_front = [i for i in range(n) if domination_count[i] == 0 and rank[i] == 0]
        if not current_front:
            break
        # 分配等级
        for i in current_front:
            rank[i] = current_rank
            # 降低被其支配的个体的支配计数
            for j in dominated[i]:
                domination_count[j] -= 1
        current_rank += 1
    return rank

# 3. 计算拥挤度（保持种群多样性）
def crowding_distance(objectives, front_indices):
    """计算同一等级个体的拥挤度"""
    n = len(front_indices)
    if n <= 1:
        return {i: float('inf') for i in front_indices}  # 单个个体拥挤度为无穷大
    
    distance = {i: 0.0 for i in front_indices}
    # 对每个目标维度排序
    for o in range(2):
        # 按目标值排序
        sorted_front = sorted(front_indices, key=lambda x: objectives[x][o])
        # 边界个体拥挤度设为无穷大
        distance[sorted_front[0]] = float('inf')
        distance[sorted_front[-1]] = float('inf')
        # 计算中间个体的拥挤度
        if objectives[sorted_front[-1]][o] - objectives[sorted_front[0]][o] == 0:
            continue  # 目标值无差异，跳过
        for i in range(1, n-1):
            distance[sorted_front[i]] += (objectives[sorted_front[i+1]][o] - objectives[sorted_front[i-1]][o]) / \
                                        (objectives[sorted_front[-1]][o] - objectives[sorted_front[0]][o])
    return distance

# 4. NSGA-II主算法
def nsga2():
    np.random.seed(42)
    pop_size = 50  # 种群大小
    n_iter = 50    # 迭代次数
    dim = 2        # 决策变量维度（x1, x2）
    var_min, var_max = 1, 10  # 变量范围
    
    # 初始化种群
    population = np.random.uniform(var_min, var_max, (pop_size, dim))
    
    for _ in range(n_iter):
        # 评估种群
        objectives = [evaluate(ind) for ind in population]
        
        # 非支配排序
        ranks = non_dominated_sort(population, objectives)
        
        # 选择父代（基于排序和拥挤度）
        # 1. 按等级排序
        sorted_indices = sorted(range(pop_size), key=lambda x: (ranks[x], -crowding_distance(objectives, range(pop_size))[x]))
        # 2. 选择前半部分作为父代
        parents = population[sorted_indices[:pop_size//2]]
        
        # 交叉操作（单点交叉）
        offspring = []
        for i in range(0, len(parents), 2):
            if i+1 >= len(parents):
                offspring.append(parents[i])
                break
            p1, p2 = parents[i], parents[i+1]
            if np.random.rand() < 0.8:  # 交叉概率80%
                cross_point = np.random.randint(1, dim)
                c1 = np.concatenate([p1[:cross_point], p2[cross_point:]])
                c2 = np.concatenate([p2[:cross_point], p1[cross_point:]])
                offspring.extend([c1, c2])
            else:
                offspring.extend([p1, p2])
        
        # 变异操作
        for i in range(len(offspring)):
            if np.random.rand() < 0.1:  # 变异概率10%
                mutate_idx = np.random.randint(dim)
                offspring[i][mutate_idx] += np.random.normal(0, 0.5)
                # 边界处理
                offspring[i][mutate_idx] = np.clip(offspring[i][mutate_idx], var_min, var_max)
        
        # 合并父代和子代，保留最优个体
        combined = np.vstack([population, offspring])
        combined_obj = [evaluate(ind) for ind in combined]
        combined_ranks = non_dominated_sort(combined, combined_obj)
        combined_crowd = crowding_distance(combined_obj, range(len(combined)))
        # 按等级和拥挤度排序，保留前pop_size个
        combined_sorted = sorted(range(len(combined)), key=lambda x: (combined_ranks[x], -combined_crowd[x]))
        population = combined[combined_sorted[:pop_size]]
    
    return population

# 5. 运行并输出结果
population = nsga2()
# 评估最终种群
final_objs = [evaluate(ind) for ind in population]
# 筛选Pareto最优解（等级为0的个体）
ranks = non_dominated_sort(population, final_objs)
pareto_indices = [i for i in range(len(population)) if ranks[i] == 0]
pareto_solutions = population[pareto_indices]

print("NSGA-II多目标优化Pareto最优解（前5个）：")
for i, sol in enumerate(pareto_solutions[:5]):
    x1, x2 = sol
    cost = objective_1(sol)
    efficiency = -objective_2(sol)  # 还原效率值
    print(f"解{i+1}：x1={x1:.2f}, x2={x2:.2f} → 成本={cost:.2f}, 效率={efficiency:.2f}")
