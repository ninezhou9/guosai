% LightGBM实现（无函数定义）
clc; clear; close all;

% 检查是否安装LightGBM
if ~exist('lightgbm', 'file')
    disp('请先安装LightGBM的MATLAB接口');
    return;
end

% 生成示例数据（多分类问题）
rng(1);  % 设置随机种子
n = 1000;  % 样本数
p = 12;    % 特征数
X = randn(n, p);  % 特征矩阵
% 生成3类标签
beta1 = randn(p, 1);
beta2 = randn(p, 1);
logit1 = X * beta1;
logit2 = X * beta2;
prob = [exp(logit1) exp(logit2) ones(n,1)];
prob = prob ./ sum(prob, 2);
y = zeros(n, 1);
for i = 1:n
    y(i) = randsample(3, 1, true, prob(i,:));
end

% 划分训练集和测试集
idx = randperm(n);
train_idx = idx(1:700);
test_idx = idx(701:end);
X_train = X(train_idx, :);
y_train = y(train_idx);
X_test = X(test_idx, :);
y_test = y(test_idx);

% 转换为LightGBM所需格式
dtrain = lgb.Dataset(X_train, 'label', y_train);
dtest = lgb.Dataset(X_test, 'label', y_test, 'reference', dtrain);

% 设置参数
params = {
    'objective', 'multiclass'
    'num_class', 3
    'metric', 'multi_logloss'
    'boosting_type', 'gbdt'
    'num_leaves', 31
    'learning_rate', 0.05
    'feature_fraction', 0.9
    'bagging_fraction', 0.8
    'bagging_freq', 5
    'verbose', 0
};

% 训练模型
model = lgb.train(params, dtrain, 100);

% 预测
y_pred_prob = lgb.predict(model, X_test);
y_pred = argmax(reshape(y_pred_prob, [], 3), 2);

% 计算准确率
accuracy = mean(y_pred == y_test);

% 输出结果
disp('LightGBM多分类结果：');
disp(['测试集准确率：', num2str(accuracy)]);
disp('前10个预测类别：');
disp(y_pred(1:10)');
disp('前10个真实类别：');
disp(y_test(1:10)');

% 可视化结果
figure;
confusionchart(y_test, y_pred);
title('LightGBM分类混淆矩阵');
