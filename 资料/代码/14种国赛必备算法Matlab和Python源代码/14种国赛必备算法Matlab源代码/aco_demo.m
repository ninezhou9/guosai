% 蚁群算法(ACO)实现（无函数定义）
clc; clear; close all;

% 解决旅行商问题(TSP)：找到访问所有城市的最短路径

% 生成示例城市坐标（30个城市）
rng(1);  % 设置随机种子
n = 30;  % 城市数量
city_coords = 100 * rand(n, 2);  % 城市坐标

% 计算城市间距离矩阵
distance_matrix = zeros(n);
for i = 1:n
    for j = 1:n
        if i ~= j
            distance_matrix(i,j) = norm(city_coords(i,:) - city_coords(j,:));
        end
    end
end

% 设置ACO参数
num_ants = 30;          % 蚂蚁数量
max_iter = 50;          % 最大迭代次数
alpha = 1;              % 信息素重要程度
beta = 2;               % 启发式信息重要程度
rho = 0.1;              % 信息素挥发系数
Q = 100;                % 信息素增量常数

% 初始化信息素
tau0 = 0.1;  % 初始信息素浓度
tau = tau0 * ones(n);  % 信息素矩阵

% 启发式信息（距离的倒数）
eta = 1 ./ (distance_matrix + eps);  % 避免除以0

% 记录最优解
best_length = Inf;
best_path = [];
best_length_history = [];

% 运行ACO算法
for iter = 1:max_iter
    % 每只蚂蚁构建路径
    paths = zeros(num_ants, n);  % 记录所有蚂蚁的路径
    path_lengths = zeros(num_ants, 1);  % 记录所有蚂蚁的路径长度
    
    for ant = 1:num_ants
        % 随机选择起始城市
        current_city = randi(n);
        visited = false(1, n);
        visited(current_city) = true;
        path = current_city;
        length = 0;
        
        % 构建路径
        for step = 2:n
            % 计算转移概率
            unvisited = find(~visited);
            probabilities = (tau(current_city, unvisited).^alpha) .* (eta(current_city, unvisited).^beta);
            probabilities = probabilities / sum(probabilities);
            
            % 轮盘赌选择下一个城市
            cumulative_probs = cumsum(probabilities);
            r = rand;
            next_city_idx = find(cumulative_probs >= r, 1);
            next_city = unvisited(next_city_idx);
            
            % 更新路径信息
            path = [path, next_city];
            length = length + distance_matrix(current_city, next_city);
            visited(next_city) = true;
            current_city = next_city;
        end
        
        % 回到起始城市，完成回路
        length = length + distance_matrix(path(end), path(1));
        paths(ant, :) = path;
        path_lengths(ant) = length;
        
        % 更新全局最优解
        if length < best_length
            best_length = length;
            best_path = path;
        end
    end
    
    % 信息素挥发
    tau = (1 - rho) * tau;
    
    % 信息素更新
    for ant = 1:num_ants
        path = paths(ant, :);
        L = path_lengths(ant);
        for k = 1:n-1
            i = path(k);
            j = path(k+1);
            tau(i,j) = tau(i,j) + Q / L;
            tau(j,i) = tau(j,i) + Q / L;  % 对称TSP
        end
        % 最后一个城市到第一个城市
        i = path(end);
        j = path(1);
        tau(i,j) = tau(i,j) + Q / L;
        tau(j,i) = tau(j,i) + Q / L;
    end
    
    best_length_history(iter) = best_length;
    fprintf('迭代 %d: 最优路径长度 = %.2f\n', iter, best_length);
end

% 输出结果
disp('蚁群算法求解TSP结果：');
disp(['最优路径长度：', num2str(best_length)]);
disp(['最优路径：', num2str(best_path)]);

% 可视化结果
% 1. 最优路径
figure;
plot(city_coords(best_path, 1), city_coords(best_path, 2), 'o-', 'MarkerFaceColor', 'b');
hold on;
plot([city_coords(best_path(end), 1), city_coords(best_path(1), 1)], ...
     [city_coords(best_path(end), 2), city_coords(best_path(1), 2)], 'o-', 'MarkerFaceColor', 'b');
xlabel('X坐标');
ylabel('Y坐标');
title('TSP最优路径');
grid on;

% 2. 优化过程
figure;
plot(best_length_history);
xlabel('迭代次数');
ylabel('最优路径长度');
title('蚁群算法优化过程');
grid on;
