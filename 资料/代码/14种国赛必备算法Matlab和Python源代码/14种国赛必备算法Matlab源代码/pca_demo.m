% PCA主成分分析实现（无函数定义）
clc; clear; close all;

% 生成示例数据（100个样本，5个相关特征）
rng(1);  % 设置随机种子
n = 100;  % 样本数
p = 5;    % 原始特征数

% 生成相关特征（前3个特征有较强相关性）
X = randn(n, p);
X(:,2) = X(:,1) * 0.8 + randn(n,1) * 0.2;
X(:,3) = X(:,1) * 0.6 + X(:,2) * 0.3 + randn(n,1) * 0.2;
X(:,4) = randn(n,1);  % 独立特征
X(:,5) = randn(n,1);  % 独立特征

% 数据标准化（均值为0，方差为1）
X_standardized = zscore(X);

% 执行PCA
[coeff, score, latent, ~, explained] = pca(X_standardized);

% 确定保留的主成分数量（累积方差解释率>85%）
cum_explained = cumsum(explained);
num_components = find(cum_explained >= 85, 1, 'first');
if isempty(num_components)
    num_components = p;  % 如果所有主成分都需要
end

% 降维后的数据
X_pca = score(:, 1:num_components);

% 输出结果
disp('PCA主成分分析结果：');
disp('各主成分解释的方差百分比：');
disp(explained');
disp('累积方差解释百分比：');
disp(cum_explained');
disp(['保留的主成分数量：', num2str(num_components)]);
disp(['保留的累积方差解释率：', num2str(cum_explained(num_components)), '%']);
disp('主成分系数矩阵（前3个主成分）：');
disp(coeff(:, 1:min(3, p)));

% 可视化结果
% 1. 方差解释率
figure;
bar(explained);
hold on;
plot(cum_explained, 'r-o', 'LineWidth', 1.5, 'MarkerSize', 6);
xlabel('主成分编号');
ylabel('方差解释率（%）');
title('各主成分的方差解释率');
legend('单个主成分', '累积');
grid on;
xticks(1:p);

% 2. 前两个主成分的散点图
figure;
scatter(X_pca(:,1), X_pca(:,2), 50, 'filled', 'MarkerEdgeColor', 'k');
xlabel(['主成分1 (', num2str(explained(1)), '%)']);
ylabel(['主成分2 (', num2str(explained(2)), '%)']);
title('PCA降维结果（前两个主成分）');
grid on;

% 3. 主成分载荷图
figure;
biplot(coeff(:,1:2), 'scores', score(:,1:2), 'varlabels', arrayfun(@(i) ['特征', num2str(i)], 1:p, 'UniformOutput', false));
title('主成分载荷图');
grid on;
