% 修复瀑布图vertcat维度错误的10种图表代码
% 包括环形图、雷达图、热图等，重点修复瀑布图的维度问题

% 设置中文字体支持
try
    set(0, 'DefaultTextFontName', 'SimHei');
    set(0, 'DefaultAxesFontName', 'SimHei');
catch
    try
        set(0, 'DefaultTextFontName', 'WenQuanYi Micro Hei');
        set(0, 'DefaultAxesFontName', 'WenQuanYi Micro Hei');
    catch
        set(0, 'DefaultTextFontName', 'Heiti TC');
        set(0, 'DefaultAxesFontName', 'Heiti TC');
    end
end

% 生成基础数据
rng(42);  % 固定随机种子，确保结果可重复
categories = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'};  % 增加类别数量以匹配瀑布图数据
values = [35, 25, 20, 15, 5];  % 基础数值
months = {'1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'};

% 1. 环形图
fprintf('显示环形图...\n');
figure('Name', '环形图', 'Position', [100, 100, 700, 700]);

% 绘制饼图作为基础
pie(values, categories(1:length(values)));
hold on;

% 绘制白色圆形形成环形效果
theta = linspace(0, 2*pi, 100);
r = 0.6;  % 环形内径大小
plot(r*cos(theta), r*sin(theta), 'w-', 'LineWidth', 15);

title('环形图');
axis equal;
box on;
pause(1);

% 2. 雷达图
fprintf('显示雷达图...\n');
figure('Name', '雷达图', 'Position', [100, 100, 700, 600]);

% 生成三组雷达图数据（确保维度一致）
data = [
    90 85 75 95 65;  % 第一组数据
    70 80 90 60 85;  % 第二组数据
    85 70 95 80 75]; % 第三组数据

% 数据维度和角度计算
n = size(data, 2);  % 维度数量
angles = linspace(0, 2*pi, n+1);  % 角度（闭合）

% 绘制雷达图网格
for i = 0:20:100
    plot(i/100*cos(angles), i/100*sin(angles), 'k--', 'LineWidth', 0.5);
    hold on;
end
% 绘制角度线
for i = 1:n
    plot([0 cos(angles(i))], [0 sin(angles(i))], 'k--', 'LineWidth', 0.5);
end

% 绘制各组数据
colors = [[0.25, 0.41, 0.88]; [0.99, 0.68, 0.27]; [0.3, 0.75, 0.93]];
for i = 1:size(data, 1)
    % 闭合数据（确保长度一致）
    plot_data = [data(i,:) data(i,1)];
    x_coords = plot_data./100.*cos(angles);
    y_coords = plot_data./100.*sin(angles);
    
    % 确保坐标长度一致
    len1 = length(x_coords);
    len2 = length(y_coords);
    min_len = min(len1, len2);
    x_coords = x_coords(1:min_len);
    y_coords = y_coords(1:min_len);
    
    plot(x_coords, y_coords, 'Color', colors(i,:), 'LineWidth', 2);
    fill(x_coords, y_coords, colors(i,:), 'FaceAlpha', 0.3);
    hold on;
end

% 设置标签和标题
for i = 1:n
    % 放置标签
    plot_text_pos = 1.1 * cos(angles(i));
    plot_text_pos2 = 1.1 * sin(angles(i));
    text(plot_text_pos, plot_text_pos2, categories(i), ...
         'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
end

title('雷达图');
axis equal;
xlim([-1.2 1.2]);
ylim([-1.2 1.2]);
legend('组1', '组2', '组3', 'Location', 'best');
box on;
hold off;
pause(1);

% 3. 热图
fprintf('显示热图...\n');
figure('Name', '热图', 'Position', [100, 100, 800, 600]);

% 生成随机矩阵数据
matrix_data = rand(10, 10);  % 10x10随机矩阵

% 绘制热图
imagesc(matrix_data);
colormap(jet);  % 使用jet颜色映射
colorbar;  % 显示颜色条

% 设置标签
set(gca, 'XTick', 1:10, 'XTickLabel', 1:10, ...
         'YTick', 1:10, 'YTickLabel', 1:10);
title('热图');
xlabel('X轴');
ylabel('Y轴');
box on;
pause(1);

% 4. 相关性热图
fprintf('显示相关性热图...\n');
figure('Name', '相关性热图', 'Position', [100, 100, 800, 600]);

% 生成多元数据并计算相关系数
n_vars = 8;  % 变量数量
n_obs = 100; % 观测值数量
data = randn(n_obs, n_vars);  % 生成多元正态分布数据
corr_matrix = corrcoef(data);  % 计算相关系数矩阵

% 绘制相关性热图
imagesc(corr_matrix);
colormap(jet);  % 使用jet颜色映射
colorbar;  % 显示颜色条

% 在热图上标注相关系数
for i = 1:n_vars
    for j = 1:n_vars
        text(j, i, sprintf('%.2f', corr_matrix(i,j)), ...
             'HorizontalAlignment', 'center', ...
             'VerticalAlignment', 'middle', ...
             'Color', 'w', 'FontWeight', 'bold');
    end
end

% 设置标签
var_names = {'变量1', '变量2', '变量3', '变量4', '变量5', '变量6', '变量7', '变量8'};
set(gca, 'XTick', 1:n_vars, 'XTickLabel', var_names, ...
         'YTick', 1:n_vars, 'YTickLabel', var_names, ...
         'XTickLabelRotation', 45);
title('相关性热图');
box on;
pause(1);

% 5. 3D散点图
fprintf('显示3D散点图...\n');
figure('Name', '3D散点图', 'Position', [100, 100, 800, 600]);

% 生成3D数据（确保维度一致）
n_points = 200;
x = randn(n_points, 1);
y = randn(n_points, 1);
z = x + y + 0.5*randn(n_points, 1);  % 具有一定相关性的数据
colors = z;  % 用z值作为颜色

% 确保所有向量长度一致
len1 = length(x);
len2 = length(y);
len3 = length(z);
min_len1 = min(len1, len2);
min_len = min(min_len1, len3);
x = x(1:min_len);
y = y(1:min_len);
z = z(1:min_len);

% 绘制3D散点图
scatter3(x, y, z, 50, colors, 'filled', 'MarkerEdgeColor', 'k');
colormap(jet);
colorbar;

title('3D散点图');
xlabel('X轴');
ylabel('Y轴');
zlabel('Z轴');
grid on;
box on;
view(3);  % 设置3D视角
pause(1);

% 6. 3D曲面图
fprintf('显示3D曲面图...\n');
figure('Name', '3D曲面图', 'Position', [100, 100, 800, 600]);

% 生成网格数据（确保维度匹配）
[x, y] = meshgrid(-3:0.1:3);
% 确保x和y维度一致
rows_x = size(x, 1);
cols_x = size(x, 2);
rows_y = size(y, 1);
cols_y = size(y, 2);

min_rows = min(rows_x, rows_y);
min_cols = min(cols_x, cols_y);
x = x(1:min_rows, 1:min_cols);
y = y(1:min_rows, 1:min_cols);

z = sin(sqrt(x.^2 + y.^2)) ./ (sqrt(x.^2 + y.^2) + eps);  % 避免除零

% 绘制3D曲面
surf(x, y, z);
colormap(jet);
colorbar;

title('3D曲面图');
xlabel('X轴');
ylabel('Y轴');
zlabel('Z轴');
grid on;
box on;
view(3);
pause(1);

% 7. 等高线图
fprintf('显示等高线图...\n');
figure('Name', '等高线图', 'Position', [100, 100, 800, 600]);

% 使用与3D曲面图相同的数据（确保维度匹配）
[x, y] = meshgrid(-3:0.1:3);
% 确保x和y维度一致
rows_x = size(x, 1);
cols_x = size(x, 2);
rows_y = size(y, 1);
cols_y = size(y, 2);

min_rows = min(rows_x, rows_y);
min_cols = min(cols_x, cols_y);
x = x(1:min_rows, 1:min_cols);
y = y(1:min_rows, 1:min_cols);

z = sin(sqrt(x.^2 + y.^2)) ./ (sqrt(x.^2 + y.^2) + eps);

% 绘制等高线图
contourf(x, y, z, 30);  % 30条等高线
colormap(jet);
colorbar;

title('等高线图');
xlabel('X轴');
ylabel('Y轴');
grid on;
box on;
axis equal;
pause(1);

% 8. 瀑布图（重点修复vertcat错误）
fprintf('显示瀑布图...\n');
figure('Name', '瀑布图', 'Position', [100, 100, 800, 600]);

% 生成瀑布图数据
data = [100, -20, 30, -15, 25, -10, 15, -5];
n = length(data);
x = 1:n;

% 确保x和data长度严格一致
if length(x) ~= length(data)
    x = 1:length(data);  % 重新生成x以匹配data长度
end

% 计算累积值，使用水平串联而非垂直串联来避免维度错误
cum_data = cumsum(data);
base = zeros(1, n);  % 创建与data相同长度的行向量
if n > 1
    base(2:end) = cum_data(1:end-1);  % 正确赋值基础值，避免vertcat
end

% 绘制瀑布图
b = bar(x, data, 'FaceColor', 'flat');

% 设置不同颜色（正数蓝色，负数红色）
cdata = zeros(length(data), 3);
for i = 1:length(data)
    if data(i) >= 0
        cdata(i,:) = [0.25, 0.41, 0.88];  % 蓝色
    else
        cdata(i,:) = [0.99, 0.25, 0.25];  % 红色
    end
end
set(b, 'CData', cdata);

% 调整柱子位置以匹配基础值
for i = 1:length(b)
    b(i).YData = b(i).YData + base(i);
end

% 添加连接线
hold on;
plot(x, cum_data, 'k-', 'LineWidth', 1.5);
plot(x, cum_data, 'ko', 'MarkerSize', 6);

title('瀑布图');
xlabel('类别');
ylabel('数值');
set(gca, 'XTick', x, 'XTickLabel', categories(1:length(x)));
grid on;
box on;
pause(1);

% 9. 面积图
fprintf('显示面积图...\n');
figure('Name', '面积图', 'Position', [100, 100, 800, 600]);

% 生成面积图数据（确保维度一致）
x = 1:12;  % 12个月份
y1 = [35, 42, 53, 61, 74, 85, 92, 88, 76, 65, 52, 40];
y2 = [20, 25, 30, 35, 40, 45, 50, 48, 42, 35, 28, 22];

% 确保y1和y2长度一致
len_y1 = length(y1);
len_y2 = length(y2);
min_len_ys = min(len_y1, len_y2);
y1 = y1(1:min_len_ys);
y2 = y2(1:min_len_ys);
x = x(1:min_len_ys);

% 绘制堆叠面积图（使用矩阵转置确保维度正确）
area(x, [y1', y2']);
colormap([0.25, 0.41, 0.88; 0.99, 0.68, 0.27]);

title('面积图');
xlabel('月份');
ylabel('数值');
set(gca, 'XTick', x, 'XTickLabel', months(1:length(x)));
legend('系列1', '系列2', 'Location', 'best');
grid on;
box on;
pause(1);

% 10. 时间序列图
fprintf('显示时间序列图...\n');
figure('Name', '时间序列图', 'Position', [100, 100, 1000, 600]);

% 生成时间序列数据（确保维度一致）
dates = datetime(2023, 1, 1):datetime(2023, 12, 31);  % 2023年全年日期
n_days = length(dates);
% 生成带有趋势和季节性的时间序列
trend = linspace(100, 200, n_days);
seasonality = 20 * sin(2*pi*(1:n_days)/30);  % 月度周期
noise = 5 * randn(1, n_days);  % 随机噪声

% 确保所有时间序列组件长度一致
len_dates = length(dates);
len_trend = length(trend);
len_season = length(seasonality);
len_noise = length(noise);

min_len1 = min(len_dates, len_trend);
min_len2 = min(len_season, len_noise);
min_len = min(min_len1, min_len2);

dates = dates(1:min_len);
trend = trend(1:min_len);
seasonality = seasonality(1:min_len);
noise = noise(1:min_len);

ts_data = trend + seasonality + noise;

% 绘制时间序列图
plot(dates, ts_data, 'b-', 'LineWidth', 1.2);

title('时间序列图');
xlabel('日期');
ylabel('数值');
grid on;
box on;
% 设置x轴标签格式
datetick('x', 'mm月', 'keeplimits');
xticks(dates(1:30:end));  % 每月显示一个标签
pause(1);

fprintf('所有图表显示完成！\n');
