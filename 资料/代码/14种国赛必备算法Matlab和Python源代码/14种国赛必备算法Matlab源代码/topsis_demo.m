% TOPSIS法实现（无函数定义）
clc; clear; close all;

% 示例数据：5个方案，4个指标（前2个为效益型，后2个为成本型）
X = [
    89 56 90 78;
    76 78 88 67;
    92 88 76 89;
    67 67 95 76;
    87 76 87 65
];
[n, m] = size(X);  % n为方案数，m为指标数

% 指标类型：1表示效益型，0表示成本型
type = [1, 1, 0, 0];

% 1. 数据标准化
Z = zeros(n, m);
for j = 1:m
    if type(j) == 1  % 效益型指标
        Z(:,j) = X(:,j) / sqrt(sum(X(:,j).^2));
    else  % 成本型指标
        Z(:,j) = (1./X(:,j)) / sqrt(sum((1./X(:,j)).^2));
    end
end

% 2. 确定权重（此处使用等权重，也可替换为熵权等）
w = ones(1, m) / m;

% 3. 计算加权标准化矩阵
V = Z .* repmat(w, n, 1);

% 4. 确定正负理想解
V_plus = max(V);  % 正理想解
V_minus = min(V); % 负理想解

% 5. 计算各方案到理想解的距离
D_plus = sqrt(sum((V - repmat(V_plus, n, 1)).^2, 2));
D_minus = sqrt(sum((V - repmat(V_minus, n, 1)).^2, 2));

% 6. 计算贴近度并排序
C = D_minus ./ (D_plus + D_minus);
[~, rank] = sort(C, 'descend');

% 输出结果
disp('TOPSIS法计算结果：');
disp('各方案贴近度：');
disp(C);
disp('方案排序（从优到劣）：');
disp(rank');

% 可视化结果
figure;
bar(C);
xlabel('方案编号');
ylabel('贴近度');
title('各方案TOPSIS贴近度');
xticklabels(1:n);
grid on;
