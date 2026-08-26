import numpy as np
from scipy.optimize import minimize

# 生成数据
np.random.seed(42)
n = 10
A = np.random.randn(5, n)
b = np.random.rand(5) * 10
lb = np.zeros(n)
ub = np.ones(n) * 10

# 定义目标函数1: 最小化
def objective1(x):
    return np.sum(x**2)

# 定义目标函数2: 最小化
def objective2(x):
    return np.sum((x - 5)** 2)

# 约束条件
constraints = [{'type': 'ineq', 'fun': lambda x: b - np.dot(A, x)}]

# 边界条件
bounds = [(lb[i], ub[i]) for i in range(n)]

# 权重法求解多目标优化
weights = np.linspace(0, 1, 5)
results = []

for w in weights:
    # 组合目标函数
    def combined_objective(x):
        return w * objective1(x) + (1 - w) * objective2(x)
    
    # 初始猜测值
    x0 = np.random.rand(n) * 10
    
    # 求解
    solution = minimize(combined_objective, x0, constraints=constraints, bounds=bounds, method='SLSQP')
    results.append({
        'weight': w,
        'x': solution.x,
        'obj1': objective1(solution.x),
        'obj2': objective2(solution.x)
    })

# 输出结果
print("多目标规划模型结果：")
print("权重 | 目标函数1值 | 目标函数2值")
print("-" * 40)
for res in results:
    print(f"{res['weight']:.1f} | {res['obj1']:.4f} | {res['obj2']:.4f}")
