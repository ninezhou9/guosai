% 系统动力学(SD)简单模型（无函数定义）
clc; clear; close all;

% 简单人口增长模型
% 状态变量：人口(Population)
% 流率：出生率(BirthRate)和死亡率(DeathRate)
% 辅助变量：出生率系数(birth_coeff)和死亡率系数(death_coeff)

% 时间设置
t_start = 0;
t_end = 50;
dt = 1;
t = t_start:dt:t_end;
n = length(t);

% 初始化变量
Population = zeros(1, n);
Births = zeros(1, n);
Deaths = zeros(1, n);

% 参数设置
Population(1) = 1000;  % 初始人口
birth_coeff = 0.05;    % 出生率系数（5%）
death_coeff = 0.02;    % 死亡率系数（2%）

% 系统动力学模拟（欧拉方法）
for i = 1:n-1
    % 计算流率
    Births(i) = birth_coeff * Population(i);
    Deaths(i) = death_coeff * Population(i);
    
    % 更新状态变量（人口变化 = 出生 - 死亡）
    Population(i+1) = Population(i) + (Births(i) - Deaths(i)) * dt;
end

% 输出结果
disp('系统动力学人口模型结果：');
result_table = table(t', Population', Births', Deaths', ...
    'VariableNames', {'时间', '人口数量', '出生人数', '死亡人数'});
disp(head(result_table, 10));
disp(tail(result_table, 10));

% 可视化结果
figure;
subplot(2,1,1);
plot(t, Population, 'b', 'LineWidth', 1.5);
ylabel('人口数量');
title('人口增长系统动力学模型');
grid on;

subplot(2,1,2);
plot(t, Births, 'g', t, Deaths, 'r', 'LineWidth', 1);
xlabel('时间（年）');
ylabel('人数');
legend('出生人数', '死亡人数');
grid on;

% 加入外部干预的模拟（后期降低出生率）
Population2 = zeros(1, n);
Births2 = zeros(1, n);
Deaths2 = zeros(1, n);

Population2(1) = 1000;  % 初始人口

for i = 1:n-1
    % 第30年开始实施计划生育，降低出生率
    if t(i) < 30
        current_birth_coeff = birth_coeff;
    else
        current_birth_coeff = birth_coeff * 0.5;  % 出生率减半
    end
    
    Births2(i) = current_birth_coeff * Population2(i);
    Deaths2(i) = death_coeff * Population2(i);
    Population2(i+1) = Population2(i) + (Births2(i) - Deaths2(i)) * dt;
end

% 对比可视化
figure;
plot(t, Population, 'b', t, Population2, 'r--', 'LineWidth', 1.5);
xlabel('时间（年）');
ylabel('人口数量');
legend('无干预', '30年开始实施计划生育');
title('不同政策下的人口对比');
grid on;
line([30, 30], [min(Population), max(Population)], 'Color', 'k', 'LineStyle', '-.');
text(30, max(Population)*0.9, '  开始实施计划生育');
