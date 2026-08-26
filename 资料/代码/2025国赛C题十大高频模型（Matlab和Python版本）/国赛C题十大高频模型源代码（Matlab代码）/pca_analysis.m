% 主成分分析（PCA）（适用于数据降维、指标整合场景）
% 数据生成：模拟企业多维度指标数据
rng(2); % 固定随机种子
X = randn(100,5); % 100个样本,5个指标
X(:,2) = 0.8*X(:,1) + 0.2*randn(100,1); % 指标2与指标1强相关
X(:,3) = 0.7*X(:,1) + 0.3*randn(100,1); % 指标3与指标1强相关

% 数据标准化
X_std = zscore(X);

% 执行PCA
[coeff, score, latent, tsquared, explained] = pca(X_std);

% 计算累计贡献率
cum_explained = cumsum(explained);
n_pc = find(cum_explained >= 85, 1, 'first'); % 选择累计贡献率≥85%的主成分

% 输出结果
fprintf('PCA分析结果：\n');
fprintf('需要的主成分数量：%d\n', n_pc);
fprintf('累计贡献率：%.2f%%\n', cum_explained(n_pc));
fprintf('主成分系数矩阵：\n');
disp(coeff(:,1:n_pc));
fprintf('前5个样本的第一主成分得分：\n');
disp(score(1:5,1));
