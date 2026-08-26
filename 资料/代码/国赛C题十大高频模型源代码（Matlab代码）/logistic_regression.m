% Logistic回归模型（适用于二分类预测场景）
% 数据生成：模拟企业违约预测数据
rng(3); % 固定随机种子
% 修正：使用行向量而非列向量进行加法，解决维度不匹配问题
X = [randn(100,2)+[1, 0.5]; randn(100,2)+[-1, -0.5]]; % 2个特征,200个样本
y = [zeros(100,1); ones(100,1)]; % 标签(0:不违约,1:违约)

% 拟合Logistic回归模型
glm_model = glmfit(X, y, 'binomial', 'link', 'logit');

% 预测与评估
y_pred_prob = glmval(glm_model, X, 'logit');
y_pred = y_pred_prob >= 0.5; % 分类阈值
accuracy = sum(y_pred == y)/length(y);

% 输出结果
fprintf('Logistic回归结果：\n');
fprintf('回归系数：\n');
disp(glm_model);
fprintf('预测准确率：%.2f%%\n', accuracy*100);
fprintf('前5个样本的违约概率：\n');
disp(y_pred_prob(1:5));
