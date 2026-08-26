% Prophet时间序列预测（无函数定义）
clc; clear; close all;

% 检查是否安装Prophet
if ~exist('prophet', 'file')
    disp('请先安装Prophet的MATLAB接口');
    return;
end

% 生成示例时间序列数据（带季节性和趋势）
dates = datetime(2020, 1, 1):datetime(2023, 12, 31);
n = length(dates);
trend = linspace(100, 300, n);  % 趋势成分
seasonality = 50 * sin(2*pi*(1:365:365*4)'/365);  % 年度季节性
noise = 10 * randn(n, 1);  % 噪声
y = trend + seasonality(1:n) + noise;

% 准备Prophet所需数据格式
data = table();
data.ds = dates';
data.y = y;

% 创建模型
m = prophet();

% 拟合模型
[model, history] = fit(m, data);

% 预测未来365天
future = make_future_dataframe(m, 365);
forecast = predict(model, future);

% 输出结果
disp('Prophet预测结果：');
disp('最后10个历史数据点：');
disp(tail(history, 10));
disp('前10个预测数据点：');
disp(head(forecast, 10));

% 可视化结果
figure;
plot(history.ds, history.y, 'b', 'LineWidth', 1);
hold on;
plot(forecast.ds, forecast.yhat, 'r', 'LineWidth', 1);
plot(forecast.ds, forecast.yhat_lower, 'r--', 'LineWidth', 0.5);
plot(forecast.ds, forecast.yhat_upper, 'r--', 'LineWidth', 0.5);
xlabel('日期');
ylabel('值');
legend('历史数据', '预测值', '预测下限', '预测上限');
title('Prophet时间序列预测');
grid on;
xlim([min(data.ds) max(forecast.ds)]);
