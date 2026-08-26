% 遗传算法(GA)实现（无函数定义）
clc; clear; close all;

% 定义优化问题：Rastrigin函数（多峰函数，难以优化）
% f(x) = A*n + sum([(x_i^2 - A*cos(2*pi*x_i)) for x_i in x])
% 其中A=10，x_i∈[-5.12,5.12]，最小值在x=0处，f(x)=0

% 参数设置
n = 5;  % 变量维度
A = 10;
lb = -5.12 * ones(1, n);  % 下界
ub = 5.12 * ones(1, n);   % 上界

% 定义目标函数（匿名函数，不使用函数定义）
objFun = @(x) A*n + sum(x.^2 - A*cos(2*pi*x), 2);

% 设置GA参数
options = optimoptions('ga', ...
    'PopulationSize', 100, ...
    'MaxGenerations', 50, ...
    'EliteCount', 5, ...
    'CrossoverFraction', 0.8, ...
    'MutationFcn', @mutationgaussian, ...
    'Display', 'iter', ...
    'PlotFcn', @gaplotbestf, ...
    'Seed', 1);

% 运行遗传算法
[x_opt, fval_opt, exitflag, output] = ga(objFun, n, [], [], [], [], lb, ub, [], options);

% 输出结果
disp('遗传算法优化结果：');
disp(['最优解：', num2str(x_opt)]);
disp(['最优目标函数值：', num2str(fval_opt)]);
disp(['迭代次数：', num2str(output.generations)]);
disp(['函数评价次数：', num2str(output.funccount)]);

% 可视化优化过程
figure;
plot(output.bestf);
xlabel('迭代次数');
ylabel('最佳目标函数值');
title('遗传算法优化过程');
grid on;
semilogy;  % 对数坐标更清晰展示收敛过程
