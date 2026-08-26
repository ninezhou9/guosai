% 熵权法实现（无函数定义）
clc; clear; close all;

% 示例数据：6个样本，5个指标（均为效益型）
X = [
    80 90 70 85 95;
    75 85 80 90 85;
    90 80 85 75 90;
    85 95 75 80 80;
    70 75 90 95 75;
    95 70 95 70 85
];
[n, m] = size(X);  % n为样本数，m为指标数

% 1. 数据标准化（效益型指标）
P = X ./ repmat(sum(X), n, 1);

% 2. 计算熵值
k = 1 / log(n);
E = zeros(1, m);
for j = 1:m
    % 处理可能的0值
    P_j = P(:,j);
    P_j(P_j == 0) = eps;  % 替换0为极小值
    E(j) = -k * sum(P_j .* log(P_j));
end

% 3. 计算差异系数
G = 1 - E;

% 4. 计算权重
w = G / sum(G);

% 输出结果
disp('熵权法计算结果：');
disp('各指标熵值：');
disp(E);
disp('各指标权重：');
disp(w);
disp('权重总和：');
disp(sum(w));

% 可视化结果
figure;
pie(w, arrayfun(@(x) ['指标' num2str(x)], 1:m, 'UniformOutput', false));
title('熵权法计算的指标权重分布');
