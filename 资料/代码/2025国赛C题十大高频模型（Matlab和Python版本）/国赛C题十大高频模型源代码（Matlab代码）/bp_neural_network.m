% BP神经网络（适用于非线性预测场景）
% 数据生成：模拟非线性预测数据（如乘客里程预测）
rng(5); % 固定随机种子
x = linspace(0, 2*pi, 200)'; % 输入变量
y = sin(x) + 0.1*randn(200,1); % 输出变量（带噪声）

% 数据归一化
x_norm = (x - min(x))/(max(x)-min(x));
y_norm = (y - min(y))/(max(y)-min(y));

% 构建与训练BP网络
net = newff(x_norm, y_norm, 5, {'tansig', 'purelin'}, 'trainlm');
net.trainParam.epochs = 1000; % 训练次数
net.trainParam.goal = 1e-5; % 训练目标误差
net = train(net, x_norm, y_norm);

% 预测与评估
y_pred_norm = sim(net, x_norm);
y_pred = y_pred_norm*(max(y)-min(y)) + min(y); % 反归一化
mse_error = mean((y - y_pred).^2);

% 输出结果
fprintf('BP神经网络结果：\n');
fprintf('训练误差（MSE）：%.6f\n', mse_error);
fprintf('前5个样本预测值：\n');
disp(y_pred(1:5));
fprintf('前5个样本真实值：\n');
disp(y(1:5));
