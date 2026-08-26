% 随机森林实现（无函数定义）
clc; clear; close all;

% 生成示例数据（回归问题）
rng(1);  % 设置随机种子
n = 500;   % 样本数
p = 15;    % 特征数
X = randn(n, p);  % 特征矩阵
% 生成目标值（非线性关系）
y = 3*sin(X(:,1)) + 2*X(:,2).^2 + 0.5*X(:,3) + 0.1*randn(n,1);

% 划分训练集和测试集
idx = randperm(n);
train_idx = idx(1:350);
test_idx = idx(351:end);
X_train = X(train_idx, :);
y_train = y(train_idx);
X_test = X(test_idx, :);
y_test = y(test_idx);

% 训练随机森林回归模型
numTrees = 50;  % 树的数量
model = TreeBagger(numTrees, X_train, y_train, 'Method', 'regression');

% 预测
y_pred = predict(model, X_test);
y_pred = str2double(y_pred);  % 转换为数值

% 计算性能指标
mse = mean((y_pred - y_test).^2);
rmse = sqrt(mse);
r2 = 1 - sum((y_test - y_pred).^2) / sum((y_test - mean(y_test)).^2);

% 输出结果
disp('随机森林回归结果：');
disp(['测试集MSE：', num2str(mse)]);
disp(['测试集RMSE：', num2str(rmse)]);
disp(['测试集R²：', num2str(r2)]);

% 可视化结果
figure;
scatter(y_test, y_pred, 30, 'filled', 'MarkerEdgeColor', 'k');
hold on;
plot([min(y_test) max(y_test)], [min(y_test) max(y_test)], 'r--', 'LineWidth', 1.5);
xlabel('真实值');
ylabel('预测值');
title('随机森林预测值 vs 真实值');
grid on;
axis equal;
