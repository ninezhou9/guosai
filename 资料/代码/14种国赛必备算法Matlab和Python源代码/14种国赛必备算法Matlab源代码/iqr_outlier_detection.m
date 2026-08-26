% IQR异常值检测实现（无函数定义）
clc; clear; close all;

% 生成示例数据（含异常值）
rng(1);  % 设置随机种子
n = 200;  % 正常数据点数量
data_normal = randn(n, 1) * 10 + 50;  % 均值50，标准差10的正态分布

% 添加异常值
n_outliers = 10;
outliers = [rand(n_outliers/2, 1)*20 + 100;  % 高值异常
            rand(n_outliers/2, 1)*20];       % 低值异常
data = [data_normal; outliers];

% 计算四分位数和IQR
Q1 = quantile(data, 0.25);  % 第一四分位数
Q3 = quantile(data, 0.75);  % 第三四分位数
IQR = Q3 - Q1;              % 四分位距

% 确定异常值阈值
lower_bound = Q1 - 1.5 * IQR;  % 下界
upper_bound = Q3 + 1.5 * IQR;  % 上界

% 检测异常值
is_outlier = (data < lower_bound) | (data > upper_bound);
outlier_values = data(is_outlier);
normal_values = data(~is_outlier);

% 输出结果
disp('IQR异常值检测结果：');
disp(['第一四分位数(Q1)：', num2str(Q1)]);
disp(['第三四分位数(Q3)：', num2str(Q3)]);
disp(['四分位距(IQR)：', num2str(IQR)]);
disp(['下界：', num2str(lower_bound)]);
disp(['上界：', num2str(upper_bound)]);
disp(['检测到的异常值数量：', num2str(sum(is_outlier))]);
disp('异常值：');
disp(outlier_values');

% 可视化结果
figure;
boxplot(data);
title('数据箱线图（含异常值）');
ylabel('数值');

figure;
histogram(data, 30);
hold on;
yline(lower_bound, 'r--', '下界');
yline(upper_bound, 'r--', '上界');
scatter(outlier_values, zeros(size(outlier_values)), 50, 'ro', 'filled', 'DisplayName', '异常值');
xlabel('数值');
ylabel('频数');
title('数据分布与异常值检测');
legend();
grid on;
