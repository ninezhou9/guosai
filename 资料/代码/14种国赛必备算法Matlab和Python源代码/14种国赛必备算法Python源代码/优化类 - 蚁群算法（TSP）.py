import numpy as np

# 1. 生成城市坐标（10个城市）
np.random.seed(42)
n_cities = 10
cities = np.random.uniform(0, 100, (n_cities, 2))

# 2. 计算距离矩阵
def calc_distance_matrix(points):
    n = len(points)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i][j] = np.linalg.norm(points[i] - points[j])
    return dist

dist_matrix = calc_distance_matrix(cities)

# 3. 蚁群算法核心实现
def aco_tsp():
    n_ants = 30    # 蚂蚁数量
    n_iter = 50    # 迭代次数
    alpha = 1.0    # 信息素重要性
    beta = 2.0     # 启发式因子重要性
    rho = 0.5      # 信息素挥发系数
    Q = 100        # 信息素增量
    
    n = n_cities
    tau = np.ones((n, n))  # 信息素矩阵
    eta = 1 / (dist_matrix + 1e-10)  # 启发式信息（距离倒数）
    
    best_path = None
    best_dist = float('inf')
    
    for _ in range(n_iter):
        paths = []
        path_dists = []
        
        # 每个蚂蚁构建路径
        for _ in range(n_ants):
            path = [np.random.randint(n)]  # 随机起点
            visited = set(path)
            
            while len(path) < n:
                current = path[-1]
                unvisited = [i for i in range(n) if i not in visited]
                # 计算转移概率
                prob = (tau[current, unvisited]** alpha) * (eta[current, unvisited] ** beta)
                prob /= prob.sum()
                # 选择下一个城市
                next_city = np.random.choice(unvisited, p=prob)
                path.append(next_city)
                visited.add(next_city)
            
            # 计算路径距离
            path_dist = sum(dist_matrix[path[i], path[i+1]] for i in range(n-1))
            path_dist += dist_matrix[path[-1], path[0]]  # 回到起点
            paths.append(path)
            path_dists.append(path_dist)
            
            # 更新全局最优
            if path_dist < best_dist:
                best_dist = path_dist
                best_path = path
        
        # 信息素更新
        tau *= (1 - rho)  # 挥发
        for i in range(n_ants):
            path = paths[i]
            for j in range(n):
                u, v = path[j], path[(j+1)%n]
                tau[u, v] += Q / path_dists[i]
                tau[v, u] += Q / path_dists[i]  # 无向图
        
    return best_path, best_dist

# 4. 运行优化
best_path, best_dist = aco_tsp()
print(f"蚁群算法最优路径（城市索引）：{[x+1 for x in best_path]}")  # 索引从1开始
print(f"最短路径总距离：{best_dist:.2f}")
