% XGBoost实现（无函数定义）
clc; clear; close all;

% 检查是否安装XGBoost
if ~exist('xgboost', 'file')
    disp('请先安装XGBoost的MATLAB接口');
    return;
end

% 生成示例数据（分类问题）
rng(1);  % 设置随机种子
n = 1000;  % 样本数
p = 10;    % 特征数
X = randn(n, p);  % 特征矩阵
% 生成标签（二分类）
beta = randn(p, 1);
logits = X * beta;
prob = 1 ./ (1 + exp(-logits));
y = binornd(1, prob);

% 划分训练集和测试集
idx = randperm(n);
train_idx = idx(1:700);
test_idx = idx(701:end);
X_train = X(train_idx, :);
y_train = y(train_idx);
X_test = X(test_idx, :);
y_test = y(test_idx);

% 转换为XGBoost所需格式
dtrain = xgb.DMatrix(X_train, 'label', y_train);
dtest = xgb.DMatrix(X_test, 'label', y_test);

% 设置参数
params = struct();
params.objective = 'binary:logistic';
params.eval_metric = 'logloss';
params.max_depth = 3;
params.eta = 0.1;
params.seed = 1;

% 训练模型
model = xgb.train(params, dtrain, 100);

% 预测
y_pred_prob = xgb.predict(model, dtest);
y_pred = round(y_pred_prob);

% 计算准确率
accuracy = mean(y_pred == y_test);

% 输出结果
disp('XGBoost分类结果：');
disp(['测试集准确率：', num2str(accuracy)]);
disp('前10个预测概率：');
disp(y_pred_prob(1:10)');
disp('前10个预测标签：');
disp(y_pred(1:10)');
disp('前10个真实标签：');
disp(y_test(1:10)');

% 可视化结果
figure;
histogram(y_pred_prob(y_test == 0), 20, 'FaceColor', 'b', 'EdgeColor', 'b', 'Alpha', 0.5);
hold on;
histogram(y_pred_prob(y_test == 1), 20, 'FaceColor', 'r', 'EdgeColor', 'r', 'Alpha', 0.5);
xlabel('预测概率');
ylabel('频数');
legend('负样本', '正样本');
title('XGBoost预测概率分布');
grid on;
