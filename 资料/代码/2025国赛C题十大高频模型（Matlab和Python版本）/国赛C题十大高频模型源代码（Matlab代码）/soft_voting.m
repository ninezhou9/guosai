% Soft Voting集成学习（适用于分类预测场景）
% 数据生成：模拟企业违约预测数据
rng(6); % 固定随机种子
X = [randn(100,2)+[1;0.5]; randn(100,2)+[-1;-0.5]]; % 2个特征,200个样本
y = [ones(100,1); zeros(100,1)]; % 标签(0:不违约,1:违约)

% 训练基分类器
% 1. Logistic回归
mdl1 = glmfit(X, y, 'binomial');
y1_prob = glmval(mdl1, X, 'logit');
y1 = y1_prob >= 0.5;

% 2. SVM
mdl2 = fitcsvm(X, y);
y2 = predict(mdl2, X);
y2_prob = mdl2.Fitted.values(:,2); % 正类概率

% 3. 决策树
mdl3 = fitctree(X, y);
y3 = predict(mdl3, X);
y3_prob = cell2mat(predict(mdl3, X, 'PredictMethod', 'probability'))(:,2); % 正类概率

% 计算权重（基于准确率）
acc1 = sum(y1 == y)/length(y);
acc2 = sum(y2 == y)/length(y);
acc3 = sum(y3 == y)/length(y);
weights = [acc1, acc2, acc3]/sum([acc1, acc2, acc3]);

% 加权投票
y_final_prob = weights(1)*y1_prob + weights(2)*y2_prob + weights(3)*y3_prob;
y_final = y_final_prob >= 0.5;
final_acc = sum(y_final == y)/length(y);

% 输出结果
fprintf('Soft Voting集成学习结果：\n');
fprintf('基分类器准确率：Logistic=%.2f, SVM=%.2f, 决策树=%.2f\n', acc1, acc2, acc3);
fprintf('集成学习准确率：%.2f%%\n', final_acc*100);
