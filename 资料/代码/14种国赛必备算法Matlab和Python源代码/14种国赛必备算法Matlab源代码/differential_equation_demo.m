% 微分方程模型求解（无函数定义）
clc; clear; close all;

% 求解洛伦兹系统（Lorenz system）
% dx/dt = sigma*(y - x)
% dy/dt = x*(rho - z) - y
% dz/dt = x*y - beta*z

% 参数设置
sigma = 10;
beta = 8/3;
rho = 28;

% 时间范围
tspan = [0 50];

% 初始条件
x0 = [1; 1; 1];

% 定义微分方程（使用匿名函数代替函数定义）
f = @(t, x) [sigma*(x(2) - x(1)); 
             x(1)*(rho - x(3)) - x(2); 
             x(1)*x(2) - beta*x(3)];

% 求解微分方程
[t, x] = ode45(f, tspan, x0);

% 输出结果
disp('微分方程求解结果：');
result_table = table(t(1:10), x(1:10,1), x(1:10,2), x(1:10,3), ...
    'VariableNames', {'时间', 'x(t)', 'y(t)', 'z(t)'});
disp(result_table);

% 可视化结果
figure;
subplot(3,1,1);
plot(t, x(:,1), 'LineWidth', 1);
ylabel('x(t)');
title('洛伦兹系统的解');
grid on;

subplot(3,1,2);
plot(t, x(:,2), 'LineWidth', 1);
ylabel('y(t)');
grid on;

subplot(3,1,3);
plot(t, x(:,3), 'LineWidth', 1);
xlabel('时间 t');
ylabel('z(t)');
grid on;

% 绘制三维相图
figure;
plot3(x(:,1), x(:,2), x(:,3), 'LineWidth', 0.5);
xlabel('x');
ylabel('y');
zlabel('z');
title('洛伦兹吸引子');
grid on;
axis equal;
