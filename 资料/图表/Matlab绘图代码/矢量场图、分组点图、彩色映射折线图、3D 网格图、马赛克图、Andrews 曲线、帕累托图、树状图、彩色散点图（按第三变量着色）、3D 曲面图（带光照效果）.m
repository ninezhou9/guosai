% 10种特殊图表的MATLAB实现代码
% 修复了"viridis"颜色映射无法识别的错误，兼容所有MATLAB版本
% 确保中文正常显示

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
x = linspace(-2, 2, 20);
y = linspace(-2, 2, 20);
[X, Y] = meshgrid(x, y);

% 1. 矢量场图
fprintf('显示矢量场图...\n');
figure('Name', '矢量场图', 'Position', [100, 100, 800, 600]);

% 计算矢量场
U = -Y;  % x方向分量
V = X;   % y方向分量
speed = sqrt(U.^2 + V.^2);  % 矢量大小

% 绘制矢量场
quiver(X, Y, U, V, 0.5);  % 0.5控制箭头密度
hold on;
% 添加流线增强显示
streamline(X, Y, U, V, X(1:3:end,1:3:end), Y(1:3:end,1:3:end));
% 添加颜色映射（使用兼容的jet）
colormap jet;
colorbar;
caxis([0, max(speed(:))]);

title('矢量场图 (漩涡场示例)');
xlabel('X轴');
ylabel('Y轴');
axis equal;
box on;
pause(1);

% 2. 分组点图
fprintf('显示分组点图...\n');
figure('Name', '分组点图', 'Position', [100, 100, 800, 600]);

% 生成三组数据
group1_x = randn(50, 1) + 1;
group1_y = randn(50, 1) + 1;
group2_x = randn(50, 1) + 4;
group2_y = randn(50, 1) + 2;
group3_x = randn(50, 1) + 2;
group3_y = randn(50, 1) + 5;

% 绘制分组点
scatter(group1_x, group1_y, 50, 'r', 'filled', 'MarkerEdgeColor', 'k');
hold on;
scatter(group2_x, group2_y, 50, 'g', 'filled', 'MarkerEdgeColor', 'k');
scatter(group3_x, group3_y, 50, 'b', 'filled', 'MarkerEdgeColor', 'k');

% 添加分组中心标记
plot(mean(group1_x), mean(group1_y), 'ro', 'MarkerSize', 10, 'MarkerFaceColor', 'w', 'LineWidth', 2);
plot(mean(group2_x), mean(group2_y), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'w', 'LineWidth', 2);
plot(mean(group3_x), mean(group3_y), 'bo', 'MarkerSize', 10, 'MarkerFaceColor', 'w', 'LineWidth', 2);

title('分组点图');
xlabel('X值');
ylabel('Y值');
legend('组1', '组2', '组3', '组中心');
grid on;
box on;
pause(1);

% 3. 彩色映射折线图
fprintf('显示彩色映射折线图...\n');
figure('Name', '彩色映射折线图', 'Position', [100, 100, 800, 600]);

% 生成数据
t = linspace(0, 10*pi, 500);
y = sin(t) .* cos(0.5*t);
c = cos(t);  % 用于颜色映射的值

% 将c标准化到0-1范围，确保RGB值有效
c_normalized = (c - min(c)) / (max(c) - min(c));

% 创建彩色映射折线
for i = 1:length(t)-1
    % 确保RGB值都在0-1范围内
    r = c_normalized(i);
    g = 0.5;
    b = 1 - c_normalized(i);
    
    % 额外安全检查
    r = max(0, min(1, r));
    g = max(0, min(1, g));
    b = max(0, min(1, b));
    
    plot(t(i:i+1), y(i:i+1), 'LineWidth', 2, 'Color', [r, g, b]);
    hold on;
end

% 添加颜色条
colormap('hsv');
colorbar;
caxis([min(c), max(c)]);

title('彩色映射折线图 (颜色随cos(t)变化)');
xlabel('t');
ylabel('sin(t)·cos(0.5t)');
grid on;
box on;
pause(1);

% 4. 3D网格图（修复颜色映射兼容性问题）
fprintf('显示3D网格图...\n');
figure('Name', '3D网格图', 'Position', [100, 100, 800, 600]);

% 生成数据
[X, Y] = meshgrid(-3:0.1:3);
Z = sin(sqrt(X.^2 + Y.^2)) ./ (sqrt(X.^2 + Y.^2) + eps);

% 绘制3D网格
mesh(X, Y, Z);

% 核心修复：使用所有MATLAB版本都支持的颜色映射
colormap(jet);  % jet是MATLAB最早支持的颜色映射之一
colorbar;

title('3D网格图');
xlabel('X轴');
ylabel('Y轴');
zlabel('Z轴');
view(30, 30);
grid on;
box on;
pause(1);

% 5. 马赛克图
fprintf('显示马赛克图...\n');
figure('Name', '马赛克图', 'Position', [100, 100, 800, 600]);

% 创建分类数据
categories1 = {'A', 'B', 'C'};
categories2 = {'X', 'Y', 'Z', 'W'};

% 数据矩阵
data = [
    15 20 10 5;   % A类数据
    10 15 25 10;  % B类数据
    5 10 15 20    % C类数据
];

% 计算比例
row_totals = sum(data, 2);
col_totals = sum(data, 1);
total = sum(row_totals);

% 绘制马赛克图
x = 0;
colors = lines(size(data, 1));  % 为每行分配不同颜色

for i = 1:size(data, 1)
    y = 0;
    row_frac = row_totals(i) / total;
    for j = 1:size(data, 2)
        col_frac = col_totals(j) / total;
        rect_width = col_frac;
        rect_height = row_frac * (data(i,j) / row_totals(i));
        
        rectangle('Position', [x, y, rect_width, rect_height], ...
                  'FaceColor', colors(i,:), 'EdgeColor', 'w', 'LineWidth', 2);
        hold on;
        
        y = y + rect_height;
    end
    x = x + rect_width;
end

% 添加标签
text(0.1, 1.02, categories1(1));
text(0.4, 1.02, categories1(2));
text(0.7, 1.02, categories1(3));

text(-0.05, 0.15, categories2(1), 'Rotation', 90);
text(-0.05, 0.4, categories2(2), 'Rotation', 90);
text(-0.05, 0.65, categories2(3), 'Rotation', 90);
text(-0.05, 0.85, categories2(4), 'Rotation', 90);

title('马赛克图 (分类数据比例可视化)');
axis([-0.1 1 0 1.1]);
axis off;
box on;
pause(1);

% 6. Andrews曲线
fprintf('显示Andrews曲线...\n');
figure('Name', 'Andrews曲线', 'Position', [100, 100, 800, 600]);

% 生成多元数据
num_samples = 20;
num_features = 5;
data1 = randn(num_samples, num_features) + 0.5;
data2 = randn(num_samples, num_features) - 0.5;
data3 = randn(num_samples, num_features) + 1.5;
all_data = [data1; data2; data3];
labels = [ones(num_samples,1); 2*ones(num_samples,1); 3*ones(num_samples,1)];

% 计算Andrews曲线
t = linspace(-pi, pi, 200);
for i = 1:size(all_data, 1)
    x = all_data(i,:);
    % Andrews曲线公式
    f = x(1)/sqrt(2) + ...
        x(2)*sin(t) + ...
        x(3)*cos(t) + ...
        x(4)*sin(2*t) + ...
        x(5)*cos(2*t);
    
    % 根据类别设置颜色
    if labels(i) == 1
        color = 'r';
    elseif labels(i) == 2
        color = 'g';
    else
        color = 'b';
    end
    
    plot(t, f, color, 'LineWidth', 0.8);
    hold on;
end

title('Andrews曲线 (多元数据分类可视化)');
xlabel('t');
ylabel('函数值');
legend('类别1', '类别2', '类别3');
grid on;
box on;
pause(1);

% 7. 帕累托图
fprintf('显示帕累托图...\n');
figure('Name', '帕累托图', 'Position', [100, 100, 800, 600]);

% 生成数据
defects = [30, 15, 10, 8, 5, 4, 3, 2, 1, 1];
categories = {'缺陷A', '缺陷B', '缺陷C', '缺陷D', '缺陷E', '缺陷F', '缺陷G', '缺陷H', '缺陷I', '缺陷J'};

% 按降序排序
[sorted_defects, idx] = sort(defects, 'descend');
sorted_categories = categories(idx);

% 计算累积百分比
cum_percent = cumsum(sorted_defects) / sum(sorted_defects) * 100;

% 创建双Y轴
bar(sorted_defects, 'FaceColor', [0.25, 0.41, 0.88]);
hold on;
ax2 = axes('Position', get(gca, 'Position'), 'YAxisLocation', 'right', ...
           'Color', 'none', 'XTick', []);
plot(ax2, cum_percent, 'r-o', 'LineWidth', 1.5, 'MarkerSize', 6);

% 设置标签
xlabel('缺陷类型');
ylabel('缺陷数量');
ylabel(ax2, '累积百分比 (%)');
title('帕累托图 (80/20法则示例)');
set(gca, 'XTick', 1:length(sorted_categories), 'XTickLabel', sorted_categories, 'XTickLabelRotation', 45);
ylim(ax2, [0, 110]);
line(ax2, xlim, [80, 80], 'Color', 'k', 'LineStyle', '--');  % 80%参考线
legend('缺陷数量', '累积百分比', 'Location', 'best');
grid on;
box on;
pause(1);

% 8. 树状图
fprintf('显示树状图...\n');
figure('Name', '树状图', 'Position', [100, 100, 800, 600]);

% 生成随机数据并计算距离
data = rand(10, 5);  % 10个样本，5个特征
dist_matrix = pdist(data);  % 计算两两样本间的距离
linkage_matrix = linkage(dist_matrix, 'ward');  % 层次聚类

% 绘制树状图
dendrogram(linkage_matrix, 'Labels', {'样本1', '样本2', '样本3', '样本4', '样本5', ...
                                      '样本6', '样本7', '样本8', '样本9', '样本10'});

title('树状图 (层次聚类结果)');
xlabel('样本');
ylabel('距离');
grid on;
box on;
pause(1);

% 9. 彩色散点图（按第三变量着色）
fprintf('显示彩色散点图...\n');
figure('Name', '彩色散点图', 'Position', [100, 100, 800, 600]);

% 生成数据
n = 200;
x = randn(n, 1);
y = randn(n, 1);
z = x .* exp(-x.^2 - y.^2);  % 第三变量，用于着色

% 绘制彩色散点图
scatter(x, y, 50, z, 'filled', 'MarkerEdgeColor', 'k');
colormap(jet);  % 使用兼容的颜色映射
colorbar;

title('彩色散点图 (按第三变量着色)');
xlabel('X值');
ylabel('Y值');
annotation('textbox', [0.05, 0.9, 0.2, 0.05], 'String', '颜色表示: z = x·exp(-x²-y²)', ...
           'EdgeColor', 'none', 'BackgroundColor', 'w');
grid on;
box on;
pause(1);

% 10. 3D曲面图（带光照效果）
fprintf('显示3D曲面图...\n');
figure('Name', '3D曲面图', 'Position', [100, 100, 800, 600]);

% 生成数据
[X, Y] = meshgrid(-3:0.1:3);
Z = sin(sqrt(X.^2 + Y.^2)) ./ (sqrt(X.^2 + Y.^2) + eps);

% 绘制带光照的3D曲面
surf(X, Y, Z);
colormap(jet);  % 使用兼容的颜色映射
colorbar;

% 添加光照效果
light('Position', [1, 1, 1]);
light('Position', [-1, -1, 1]);
material('dull');  % 设置材质
shading interp;    % 平滑着色

title('3D曲面图 (带光照效果)');
xlabel('X轴');
ylabel('Y轴');
zlabel('Z轴');
view(30, 30);
grid on;
box on;
pause(1);

fprintf('所有图表显示完成！\n');
