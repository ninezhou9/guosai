% 蒙特卡洛模拟（适用于风险分析与不确定性评估场景）
% 数据生成：模拟农作物种植收益风险分析
rng(9); % 固定随机种子
n_sim = 10000; % 模拟次数

% 随机变量参数（正态分布）
price_mean = 2.5; % 价格均值(元/斤)
price_std = 0.3; % 价格标准差
yield_mean = 800; % 产量均值(斤/亩)
yield_std = 50; % 产量标准差
cost = 1000; % 固定成本(元/亩)

% 执行蒙特卡洛模拟
price = normrnd(price_mean, price_std, n_sim, 1);
yield = normrnd(yield_mean, yield_std, n_sim, 1);
profit = price .* yield - cost; % 计算亩收益

% 统计结果
profit_mean = mean(profit);
profit_std = std(profit);
profit_95ci = prctile(profit, [2.5, 97.5]); % 95%置信区间
loss_prob = sum(profit < 0)/n_sim; % 亏损概率

% 输出结果
fprintf('蒙特卡洛模拟结果：\n');
fprintf('模拟次数：%d\n', n_sim);
fprintf('亩收益均值：%.2f元，标准差：%.2f元\n', profit_mean, profit_std);
fprintf('亩收益95%%置信区间：[%.2f, %.2f]元\n', profit_95ci(1), profit_95ci(2));
fprintf('亏损概率：%.2f%%\n', loss_prob*100);
