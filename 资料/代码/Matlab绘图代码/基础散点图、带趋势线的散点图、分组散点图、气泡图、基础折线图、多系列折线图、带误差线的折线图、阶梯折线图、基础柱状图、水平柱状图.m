% 10种基础图表的MATLAB实现
% 包含中文显示设置，代码可直接运行

% 设置中文字体支持，确保中文正常显示
try
    set(0, 'DefaultTextFontName', 'SimHei');   % 优先尝试SimHei字体
    set(0, 'DefaultAxesFontName', 'SimHei');
catch
    try
        set(0, 'DefaultTextFontName', 'WenQuanYi Micro Hei');  % 次选文泉驿微米黑
        set(0, 'DefaultAxesFontName', 'WenQuanYi Micro Hei');
    catch
        set(0, 'DefaultTextFontName', 'Heiti TC');  % Mac系统备选黑体
        set(0, 'DefaultAxesFontName', 'Heiti TC');
    end
end

% 生成基础示例数据
rng(42);  % 设置随机种子，保证结果可重复
x = linspace(0, 10, 100);  % 生成0到10之间的100个均匀点
y = sin(x) + randn(1, 100)*0.2;  % 带噪声的正弦曲线
categories = {'A', 'B', 'C', 'D', 'E'};  % 类别标签
values = [23, 45, 56, 78, 32];  % 柱状图数据
bar_indices = 1:length(categories);  % 柱状图索引

% 1. 基础散点图
fprintf('显示第 1 种图表: 基础散点图...\n');
figure('Name', '基础散点图', 'Position', [100, 100, 800, 500]);
scatter(x, y, 50, 'b', 'filled', 'MarkerEdgeColor', 'k');  % 蓝色填充散点，黑色边缘
title('基础散点图');
xlabel('X轴');
ylabel('Y轴');
grid on;  % 显示网格
grid minor;  % 显示次要网格
set(gca, 'GridLineStyle', '--', 'GridAlpha', 0.7);  % 网格线样式为虚线，透明度0.7
box on;  % 显示坐标轴边框
pause(1);  % 暂停1秒，便于观察

% 2. 带趋势线的散点图
fprintf('显示第 2 种图表: 带趋势线的散点图...\n');
figure('Name', '带趋势线的散点图', 'Position', [100, 100, 800, 500]);
scatter(x, y, 50, 'b', 'filled', 'MarkerEdgeColor', 'k');
hold on;  % 保持当前图形，后续绘图叠加
p = polyfit(x, y, 1);  % 一阶多项式拟合（线性趋势）
y_trend = polyval(p, x);  % 计算趋势线数值
plot(x, y_trend, 'r--', 'LineWidth', 2);  % 红色虚线趋势线
title('带趋势线的散点图');
xlabel('X轴');
ylabel('Y轴');
legend('数据点', '趋势线', 'Location', 'best');  % 添加图例
grid on;
box on;
pause(1);

% 3. 分组散点图
fprintf('显示第 3 种图表: 分组散点图...\n');
figure('Name', '分组散点图', 'Position', [100, 100, 800, 500]);
groups = randi(3, 1, 100);  % 生成3个随机分组
colors = lines(3);  % 生成3种不同颜色
for i = 1:3
    idx = groups == i;  % 找到第i组的索引
    scatter(x(idx), y(idx), 50, colors(i,:), 'filled', 'MarkerEdgeColor', 'k');
    hold on;
end
title('分组散点图');
xlabel('X轴');
ylabel('Y轴');
legend('组1', '组2', '组3', 'Location', 'best');
grid on;
box on;
pause(1);

% 4. 气泡图
fprintf('显示第 4 种图表: 气泡图...\n');
figure('Name', '气泡图', 'Position', [100, 100, 800, 500]);
sizes = randi([10, 200], 1, 100);  % 气泡大小随机
scatter(x, y, sizes, sizes, 'filled', 'MarkerEdgeColor', 'k');  % 气泡大小和颜色都由sizes决定
colorbar;  % 显示颜色条
caxis([min(sizes), max(sizes)]);  % 设置颜色范围
title('气泡图');
xlabel('X轴');
ylabel('Y轴');
grid on;
box on;
pause(1);

% 5. 基础折线图
fprintf('显示第 5 种图表: 基础折线图...\n');
figure('Name', '基础折线图', 'Position', [100, 100, 800, 500]);
plot(x, sin(x), 'b-', 'LineWidth', 2);  % 蓝色实线，线宽2
title('基础折线图');
xlabel('X轴');
ylabel('Y轴');
grid on;
set(gca, 'GridAlpha', 0.3);  % 网格透明度0.3
box on;
pause(1);

% 6. 多系列折线图
fprintf('显示第 6 种图表: 多系列折线图...\n');
figure('Name', '多系列折线图', 'Position', [100, 100, 800, 500]);
% 同时绘制三条不同样式的曲线
plot(x, sin(x), 'b-', x, cos(x), 'r--', x, sin(x)+cos(x), 'g-.', 'LineWidth', 2);
title('多系列折线图');
xlabel('X轴');
ylabel('Y轴');
legend('sin(x)', 'cos(x)', 'sin(x)+cos(x)', 'Location', 'best');
grid on;
box on;
pause(1);

% 7. 带误差线的折线图
fprintf('显示第 7 种图表: 带误差线的折线图...\n');
figure('Name', '带误差线的折线图', 'Position', [100, 100, 800, 500]);
y_vals = sin(x);
error = rand(1, length(x)) * 0.2 + 0.1;  % 随机误差值
% 绘制带误差线的折线图
h = errorbar(x, y_vals, error, 'o-', 'MarkerFaceColor', 'b', 'LineWidth', 1.5, 'CapSize', 5);
set(h, 'Color', 'r');  % 设置线条颜色为红色
title('带误差线的折线图');
xlabel('X轴');
ylabel('Y轴');
grid on;
box on;
pause(1);

% 8. 阶梯折线图
fprintf('显示第 8 种图表: 阶梯折线图...\n');
figure('Name', '阶梯折线图', 'Position', [100, 100, 800, 500]);
step_data = cumsum(randn(1, 100));  % 随机游走数据
stairs(x, step_data, 'm-', 'LineWidth', 2);  % 品红色阶梯线
title('阶梯折线图');
xlabel('X轴');
ylabel('累积值');
grid on;
box on;
pause(1);

% 9. 基础柱状图
fprintf('显示第 9 种图表: 基础柱状图...\n');
figure('Name', '基础柱状图', 'Position', [100, 100, 800, 500]);
bar(bar_indices, values, 'FaceColor', [0.53, 0.81, 0.98]);  % 浅蓝色柱子
title('基础柱状图');
xlabel('类别');
ylabel('数值');
set(gca, 'XTick', bar_indices, 'XTickLabel', categories);  % 设置X轴标签
grid on;
set(gca, 'GridAlpha', 0.3, 'GridLineStyle', '--');
box on;
pause(1);

% 10. 水平柱状图
fprintf('显示第 10 种图表: 水平柱状图...\n');
figure('Name', '水平柱状图', 'Position', [100, 100, 800, 500]);
barh(bar_indices, values, 'FaceColor', [0.75, 0.91, 0.72]);  % 浅绿色水平柱子
title('水平柱状图');
xlabel('数值');
ylabel('类别');
set(gca, 'YTick', bar_indices, 'YTickLabel', categories);  % 设置Y轴标签
grid on;
set(gca, 'GridAlpha', 0.3, 'GridLineStyle', '--');
box on;
pause(1);

fprintf('所有10种图表显示完成！\n');
