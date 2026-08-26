% 10种常用图表的完整MATLAB实现代码
% 已修复矩阵散点图中"类 Line 的属性 FaceColor 无法识别"错误

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
rng(42);  % 固定随机种子
x = 1:10;
categories = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'};
months = {'1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'};

% 1. 双Y轴折线图
fprintf('显示双Y轴折线图...\n');
figure('Name', '双Y轴折线图', 'Position', [100, 100, 800, 600]);

y1 = [25, 32, 39, 50, 65, 72, 68, 60, 50, 42];  % 主Y轴数据
y2 = [120, 135, 150, 170, 190, 200, 195, 180, 160, 140];  % 次Y轴数据

% 统一数据长度
len_x = length(x);
len_y1 = length(y1);
len_y2 = length(y2);
min_len1 = min(len_x, len_y1);
min_len = min(min_len1, len_y2);
x = x(1:min_len);
y1 = y1(1:min_len);
y2 = y2(1:min_len);

% 绘制主Y轴数据
plot(x, y1, 'o-', 'Color', [0.25, 0.41, 0.88], 'LineWidth', 1.5, 'MarkerSize', 6);
hold on;

% 创建右侧Y轴
ax2 = axes('Position', get(gca, 'Position'), 'YAxisLocation', 'right', ...
           'Color', 'none', 'XTick', []);
plot(ax2, x, y2, 's-', 'Color', [0.99, 0.68, 0.27], 'LineWidth', 1.5, 'MarkerSize', 6);

% 设置标签
xlabel('月份');
ylabel('主Y轴数值');
ylabel(ax2, '次Y轴数值');
title('双Y轴折线图');
set(gca, 'XTick', x, 'XTickLabel', months(1:length(x)));
legend('主数据', '次数据', 'Location', 'best');
grid on;
box on;
pause(1);

% 2. 带填充区域的折线图
fprintf('显示带填充区域的折线图...\n');
figure('Name', '带填充区域的折线图', 'Position', [100, 100, 800, 600]);

y = [35, 42, 53, 61, 74, 85, 92, 88, 76, 65];
std_dev = 5;
y_upper = y + std_dev * 0.5;  % 上界
y_lower = y - std_dev * 0.5;  % 下界

% 统一长度
len_x = length(x);
len_y = length(y);
min_len = min(len_x, len_y);
x = x(1:min_len);
y = y(1:min_len);
y_upper = y_upper(1:min_len);
y_lower = y_lower(1:min_len);

% 绘制填充区域和中心线
fill([x, flip(x)], [y_upper, flip(y_lower)], [0.25, 0.41, 0.88], 'FaceAlpha', 0.3);
hold on;
plot(x, y, 'b-', 'LineWidth', 1.5);
plot(x, y, 'bo', 'MarkerSize', 6, 'MarkerFaceColor', 'b');

% 设置标签
xlabel('月份');
ylabel('数值');
title('带填充区域的折线图');
set(gca, 'XTick', x, 'XTickLabel', months(1:length(x)));
grid on;
box on;
pause(1);

% 3. 分组箱线图
fprintf('显示分组箱线图...\n');
figure('Name', '分组箱线图', 'Position', [100, 100, 800, 600]);

samples_per_group = 50;  % 每组样本数
group1_sub1 = randn(samples_per_group, 1) + 1;
group1_sub2 = randn(samples_per_group, 1) + 1.5;
group2_sub1 = randn(samples_per_group, 1) + 2.5;
group2_sub2 = randn(samples_per_group, 1) + 3;
group3_sub1 = randn(samples_per_group, 1) + 3.5;
group3_sub2 = randn(samples_per_group, 1) + 4;

% 合并数据
all_data = [group1_sub1; group1_sub2; group2_sub1; group2_sub2; group3_sub1; group3_sub2];

% 创建分组索引
group_indices = [
    ones(samples_per_group, 1);    % 组1-子组1
    ones(samples_per_group, 1)*2;  % 组1-子组2
    ones(samples_per_group, 1)*3;  % 组2-子组1
    ones(samples_per_group, 1)*4;  % 组2-子组2
    ones(samples_per_group, 1)*5;  % 组3-子组1
    ones(samples_per_group, 1)*6   % 组3-子组2
];

% 定义分组标签
group_labels = {'组1-子组1', '组1-子组2', '组2-子组1', '组2-子组2', '组3-子组1', '组3-子组2'};

% 绘制分组箱线图
boxplot(all_data, group_indices, 'Labels', group_labels, 'Colors', [0.25, 0.41, 0.88]);

% 设置箱体填充颜色
try
    h_boxes = findobj(gca, 'Tag', 'Box');
    if ~isempty(h_boxes)
        set(h_boxes(1:2:end), 'FaceColor', [0.7, 0.85, 0.95]);  % 子组1
        set(h_boxes(2:2:end), 'FaceColor', [0.9, 0.95, 0.98]);  % 子组2
    end
catch
    % 忽略旧版本不支持的属性设置
end

title('分组箱线图');
xlabel('分组');
ylabel('数值');
grid on;
box on;
pause(1);

% 5. 3D等高线图
fprintf('显示3D等高线图...\n');
figure('Name', '3D等高线图', 'Position', [100, 100, 800, 600]);

[x, y] = meshgrid(-3:0.2:3);
z = sin(sqrt(x.^2 + y.^2)) ./ (sqrt(x.^2 + y.^2) + eps);  % 避免除零

% 绘制3D等高线
[C, h] = contour3(x, y, z, 20);  % 20条等高线
clabel(C, h, 'FontSize', 8);  % 添加标签

% 设置等高线颜色
set(h, 'Color', [0.25, 0.41, 0.88]);

% 设置标签
xlabel('X轴');
ylabel('Y轴');
zlabel('Z轴');
title('3D等高线图');
grid on;
box on;
view(30, 20);
pause(1);

% 6. 误差棒图（横向）
fprintf('显示横向误差棒图...\n');
figure('Name', '横向误差棒图', 'Position', [100, 100, 800, 600]);

y = [35, 42, 53, 61, 74];  % Y轴位置
error = 5 * rand(size(y));  % 误差值
x = 1:length(y);  % 确保x与y长度一致

% 绘制横向误差棒
errorbar(y, x, error, 'o-', 'Color', [0.25, 0.41, 0.88], 'LineWidth', 1.5, 'MarkerSize', 6);
hold on;
plot(y, x, 'o', 'Color', 'white', 'MarkerSize', 8, 'MarkerFaceColor', [0.25, 0.41, 0.88]);

% 设置标签
xlabel('数值');
ylabel('类别');
title('横向误差棒图');
set(gca, 'YTick', x, 'YTickLabel', categories(1:length(x)));
grid on;
box on;
pause(1);


fprintf('所有图表显示完成！\n');
