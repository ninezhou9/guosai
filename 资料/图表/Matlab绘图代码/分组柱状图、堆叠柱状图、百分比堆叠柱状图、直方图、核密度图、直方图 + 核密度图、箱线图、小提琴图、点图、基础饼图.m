% 修复fill函数向量长度错误的10种统计图表代码
% 确保所有fill函数使用的向量长度一致

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
categories = {'A', 'B', 'C', 'D', 'E'};
bar_indices = 1:length(categories);
normal_data = randn(1000, 1);  % 正态分布数据

% 1. 分组柱状图
fprintf('显示分组柱状图...\n');
figure('Name', '分组柱状图', 'Position', [100, 100, 800, 500]);
data_group1 = [23, 45, 56, 78, 32];
data_group2 = [32, 54, 43, 67, 21];
bar_data = [data_group1; data_group2]';

bar(bar_indices, bar_data, 'FaceColor', 'flat');
colormap([0.25, 0.41, 0.88; 0.99, 0.68, 0.27]);
title('分组柱状图');
xlabel('类别');
ylabel('数值');
set(gca, 'XTick', bar_indices, 'XTickLabel', categories);
legend('组1', '组2', 'Location', 'best');
grid on;
box on;
pause(1);

% 2. 堆叠柱状图
fprintf('显示堆叠柱状图...\n');
figure('Name', '堆叠柱状图', 'Position', [100, 100, 800, 500]);
data_base = [23, 45, 56, 78, 32];
data_stack = [10, 20, 15, 25, 5];
stack_data = [data_base; data_stack]';

bar(bar_indices, stack_data, 'stacked', 'FaceColor', 'flat');
colormap([0.25, 0.41, 0.88; 0.99, 0.68, 0.27]);
title('堆叠柱状图');
xlabel('类别');
ylabel('数值');
set(gca, 'XTick', bar_indices, 'XTickLabel', categories);
legend('基础值', '叠加值', 'Location', 'best');
grid on;
box on;
pause(1);

% 3. 百分比堆叠柱状图
fprintf('显示百分比堆叠柱状图...\n');
figure('Name', '百分比堆叠柱状图', 'Position', [100, 100, 800, 500]);
data = [30 25 50 20; 40 25 20 25; 30 50 30 55];
[rows, cols] = size(data);
data_perc = data ./ repmat(sum(data, 2), 1, cols) * 100;

bar(1:rows, data_perc, 'stacked', 'FaceColor', 'flat');
colormap(jet(cols));
title('百分比堆叠柱状图');
xlabel('类别');
ylabel('百分比 (%)');
set(gca, 'XTick', 1:rows, 'XTickLabel', {'A', 'B', 'C'});
legend('组1', '组2', '组3', '组4', 'Location', 'best');
grid on;
box on;
pause(1);

% 4. 直方图
fprintf('显示直方图...\n');
figure('Name', '直方图', 'Position', [100, 100, 800, 500]);
histogram(normal_data, 30, 'FaceColor', [0.53, 0.81, 0.98], 'EdgeColor', 'k');
title('直方图');
xlabel('数值');
ylabel('频数');
grid on;
set(gca, 'GridAlpha', 0.3);
box on;
pause(1);

% 5. 核密度图（修复fill向量长度）
fprintf('显示核密度图...\n');
figure('Name', '核密度图', 'Position', [100, 100, 800, 500]);
[f, xi] = ksdensity(normal_data);

% 确保数组是列向量且长度一致
if isrow(xi), xi = xi'; end
if isrow(f), f = f'; end
% 强制确保两个向量长度相同
min_len = min(length(xi), length(f));
xi = xi(1:min_len);
f = f(1:min_len);

plot(xi, f, 'r-', 'LineWidth', 2);
hold on;

% 正确的填充方式，确保向量长度完全匹配
fill([xi; flipud(xi)], [f; zeros(size(xi))], 'r', 'FaceAlpha', 0.3);

title('核密度图');
xlabel('数值');
ylabel('密度');
grid on;
box on;
pause(1);

% 6. 直方图 + 核密度图（修复fill向量长度）
fprintf('显示直方图+核密度图...\n');
figure('Name', '直方图+核密度图', 'Position', [100, 100, 800, 500]);
histogram(normal_data, 30, 'FaceColor', [0.13, 0.55, 0.13], ...
          'EdgeColor', 'k', 'Normalization', 'pdf');
hold on;

[f, xi] = ksdensity(normal_data);
% 确保向量长度一致
if isrow(xi), xi = xi'; end
if isrow(f), f = f'; end
min_len = min(length(xi), length(f));
xi = xi(1:min_len);
f = f(1:min_len);

plot(xi, f, 'r-', 'LineWidth', 2);

% 填充区域，确保向量长度匹配
fill([xi; flipud(xi)], [f; zeros(size(xi))], 'r', 'FaceAlpha', 0.3);

title('直方图+核密度图');
xlabel('数值');
ylabel('密度');
legend('直方图', '核密度估计', 'Location', 'best');
grid on;
box on;
pause(1);

% 7. 箱线图（完全兼容版本）
fprintf('显示箱线图...\n');
figure('Name', '箱线图', 'Position', [100, 100, 800, 500]);
nSamples = 100;
data_cell = cell(1, 5);
for i = 1:5
    data_cell{i} = randn(nSamples, 1) + i;
end

% 最兼容的方式绘制箱线图
boxplot(cell2mat(data_cell), 'Labels', categories, 'Colors', [0.25, 0.41, 0.88]);

% 尝试设置箱体填充颜色，兼容不同版本
try
    h_boxes = findobj(gca, 'Tag', 'Box');
    if ~isempty(h_boxes) && isprop(h_boxes, 'FaceColor')
        set(h_boxes, 'FaceColor', [0.7, 0.85, 0.95], 'FaceAlpha', 0.8);
    end
catch
    % 忽略错误，使用默认样式
end

title('箱线图');
xlabel('类别');
ylabel('数值');
grid on;
box on;
pause(1);

% 8. 小提琴图（修复fill向量长度）
fprintf('显示小提琴图...\n');
figure('Name', '小提琴图', 'Position', [100, 100, 800, 500]);
% 生成5组数据
v_data1 = randn(100, 1) + 1;
v_data2 = randn(100, 1) + 2;
v_data3 = randn(100, 1) + 3;
v_data4 = randn(100, 1) + 4;
v_data5 = randn(100, 1) + 5;

violin_color = [0.25, 0.41, 0.88];
width = 0.5;

% 绘制第1组小提琴图
[data, xi] = ksdensity(v_data1);
% 确保数据长度一致
min_len = min(length(data), length(xi));
data = data(1:min_len);
xi = xi(1:min_len);
f_scaled = data / max(data) * width/2;

plot(1 - f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
hold on;
plot(1 + f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
% 确保填充向量长度完全匹配
fill([1 - f_scaled; 1 + flipud(f_scaled)], [xi; flipud(xi)], ...
     violin_color, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
median_val = median(v_data1);
plot([1 - width/2, 1 + width/2], [median_val, median_val], 'k-', 'LineWidth', 2);

% 绘制第2组小提琴图
[data, xi] = ksdensity(v_data2);
min_len = min(length(data), length(xi));
data = data(1:min_len);
xi = xi(1:min_len);
f_scaled = data / max(data) * width/2;

plot(2 - f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
plot(2 + f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
fill([2 - f_scaled; 2 + flipud(f_scaled)], [xi; flipud(xi)], ...
     violin_color, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
median_val = median(v_data2);
plot([2 - width/2, 2 + width/2], [median_val, median_val], 'k-', 'LineWidth', 2);

% 绘制第3组小提琴图
[data, xi] = ksdensity(v_data3);
min_len = min(length(data), length(xi));
data = data(1:min_len);
xi = xi(1:min_len);
f_scaled = data / max(data) * width/2;

plot(3 - f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
plot(3 + f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
fill([3 - f_scaled; 3 + flipud(f_scaled)], [xi; flipud(xi)], ...
     violin_color, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
median_val = median(v_data3);
plot([3 - width/2, 3 + width/2], [median_val, median_val], 'k-', 'LineWidth', 2);

% 绘制第4组小提琴图
[data, xi] = ksdensity(v_data4);
min_len = min(length(data), length(xi));
data = data(1:min_len);
xi = xi(1:min_len);
f_scaled = data / max(data) * width/2;

plot(4 - f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
plot(4 + f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
fill([4 - f_scaled; 4 + flipud(f_scaled)], [xi; flipud(xi)], ...
     violin_color, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
median_val = median(v_data4);
plot([4 - width/2, 4 + width/2], [median_val, median_val], 'k-', 'LineWidth', 2);

% 绘制第5组小提琴图
[data, xi] = ksdensity(v_data5);
min_len = min(length(data), length(xi));
data = data(1:min_len);
xi = xi(1:min_len);
f_scaled = data / max(data) * width/2;

plot(5 - f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
plot(5 + f_scaled, xi, 'Color', violin_color, 'LineWidth', 1.5);
fill([5 - f_scaled; 5 + flipud(f_scaled)], [xi; flipud(xi)], ...
     violin_color, 'FaceAlpha', 0.3, 'EdgeColor', 'none');
median_val = median(v_data5);
plot([5 - width/2, 5 + width/2], [median_val, median_val], 'k-', 'LineWidth', 2);

set(gca, 'XTick', 1:5, 'XTickLabel', categories);
title('小提琴图（完全脚本实现）');
xlabel('类别');
ylabel('数值');
xlim([0, 6]);
grid on;
box on;
hold off;
pause(1);

% 9. 点图
fprintf('显示点图...\n');
figure('Name', '点图', 'Position', [100, 100, 800, 500]);
for i = 1:5
    y = randn(50, 1) + i;
    x = i * ones(50, 1);
    scatter(x, y, 30, [0.58, 0.29, 0.63], 'filled', ...
            'MarkerEdgeColor', 'k', 'MarkerFaceAlpha', 0.7);
    hold on;
end

set(gca, 'XTick', 1:5, 'XTickLabel', categories);
title('点图');
xlabel('类别');
ylabel('数值');
grid on;
box on;
pause(1);

% 10. 基础饼图
fprintf('显示基础饼图...\n');
figure('Name', '基础饼图', 'Position', [100, 100, 800, 500]);
pie_values = [23, 45, 56, 78, 32];
pie(pie_values, categories);
title('基础饼图');
axis equal;
pause(1);

fprintf('所有图表显示完成！\n');
