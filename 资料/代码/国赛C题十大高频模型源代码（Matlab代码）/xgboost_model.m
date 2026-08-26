% XGBoost模型（适用于分类与回归场景，需安装XGBoost工具箱）
% 数据生成：模拟企业信誉分类数据
rng(7); % 固定随机种子
X = randn(300,3); % 3个特征,300个样本
y = [ones(150,1); zeros(150,1)]; % 标签(0:低信誉,1:高信誉)

% 转换数据格式
dtrain = xgb.DMatrix(X, y);

% 设置参数并训练
params = {'objective', 'binary:logistic', 'max_depth', 3, 'eta', 0.1, 'num_round', 100};
model = xgb.train(params, dtrain);

% 预测与评估
y_pred_prob = xgb.predict(model, X);
y_pred = y_pred_prob >= 0.5;
accuracy = sum(y_pred == y)/length(y);

% 获取特征重要性
feat_importance = xgb.get_score(model, 'gain');

% 输出结果
fprintf('XGBoost模型结果：\n');
fprintf('预测准确率：%.2f%%\n', accuracy*100);
fprintf('特征重要性（增益）：\n');
disp(feat_importance);
fprintf('前5个样本的预测概率：\n');
disp(y_pred_prob(1:5));
