% NSGA-II多目标优化实现（无函数定义）
clc; clear; close all;

% 定义多目标优化问题：ZDT1测试函数
% 目标函数：
% f1(x1) = x1
% f2(x) = g(x) * (1 - sqrt(x1/g(x)))
% 其中g(x) = 1 + 9*(sum(x(2:n))/(n-1))
% 决策变量x_i∈[0,1]，n≥2

% 参数设置
n = 5;  % 决策变量维度
lb = zeros(1, n);  % 下界
ub = ones(1, n);   % 上界

% 定义目标函数（匿名函数，返回两个目标值）
objFun = @(x) [
    x(:,1);  % f1
    (1 + 9*mean(x(:,2:end), 2)) .* (1 - sqrt(x(:,1) ./ (1 + 9*mean(x(:,2:end), 2) + eps)))  % f2
];

% 设置NSGA-II参数
options = optimoptions('gamultiobj', ...
    'PopulationSize', 100, ...
    'MaxGenerations', 50, ...
    'CrossoverFraction', 0.8, ...
    'MutationFcn', @mutationgaussian, ...
    'ParetoFraction', 0.3, ...
    'Display', 'iter', ...
    'PlotFcn', {@gaplotpareto}, ...
    'Seed', 1);

% 运行NSGA-II算法
[x_opt, fval_opt, exitflag, output] = gamultiobj(objFun, n, [], [], [], [], lb, ub, [], options);

% 输出结果
disp('NSGA-II多目标优化结果：');
disp(['找到的帕累托最优解数量：', num2str(size(x_opt, 1))]);
disp('前5个帕累托最优解的目标函数值：');
disp(head(fval_opt, 5));

% 可视化帕累托前沿
figure;
scatter(fval_opt(:,1), fval_opt(:,2), 50, 'filled', 'MarkerEdgeColor', 'k');
xlabel('目标函数 f1');
ylabel('目标函数 f2');
title('ZDT1问题的帕累托前沿');
grid on;
axis equal;
