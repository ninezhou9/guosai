% 粒子群优化(PSO)实现（无函数定义）
clc; clear; close all;

% 定义优化问题：Sphere函数
% f(x) = sum(x_i^2)，x_i∈[-100,100]，最小值在x=0处，f(x)=0

% 参数设置
n = 10;  % 变量维度
lb = -100 * ones(1, n);  % 下界
ub = 100 * ones(1, n);   % 上界

% 定义目标函数（匿名函数）
objFun = @(x) sum(x.^2, 2);

% 设置PSO参数
options = optimoptions('particleswarm', ...
    'SwarmSize', 50, ...
    'MaxIterations', 100, ...
    'InertiaRange', [0.4, 0.9], ...
    'SocialAdjustmentWeight', 1.5, ...
    'CognitiveAdjustmentWeight', 1.5, ...
    'Display', 'iter', ...
    'PlotFcn', @pswplotbestf, ...
    'Seed', 1);

% 运行粒子群优化
[x_opt, fval_opt, exitflag, output] = particleswarm(objFun, n, lb, ub, options);

% 输出结果
disp('粒子群优化结果：');
disp(['最优解：', num2str(x_opt)]);
disp(['最优目标函数值：', num2str(fval_opt)]);
disp(['迭代次数：', num2str(output.iterations)]);
disp(['函数评价次数：', num2str(output.funccount)]);

% 可视化优化过程
figure;
plot(output.bestf);
xlabel('迭代次数');
ylabel('最佳目标函数值');
title('粒子群优化过程');
grid on;
semilogy;  % 对数坐标
