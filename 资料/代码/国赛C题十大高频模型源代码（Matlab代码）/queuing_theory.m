% 排队论（生灭过程）（适用于排队系统分析场景）
% 数据生成：模拟机场出租车排队系统参数
lambda = [3, 4, 5]; % 不同到达率(辆/小时)
mu = 6; % 服务率(辆/小时)

% 计算生灭过程稳态指标
for i = 1:length(lambda)
    rho = lambda(i)/mu; % 系统利用率
    if rho >= 1
        fprintf('到达率λ=%.1f时系统不稳定（ρ≥1）\n', lambda(i));
        continue;
    end
    Lq = rho^2/(1 - rho); % 平均队列长度
    Wq = Lq/lambda(i); % 平均等待时间(小时)
    L = rho/(1 - rho); % 系统内平均顾客数
    W = L/lambda(i); % 系统内平均时间(小时)
    
    % 输出结果
    fprintf('到达率λ=%.1f时：\n', lambda(i));
    fprintf('  系统利用率ρ=%.2f\n', rho);
    fprintf('  平均队列长度Lq=%.2f辆\n', Lq);
    fprintf('  平均等待时间Wq=%.2f分钟\n', Wq*60);
    fprintf('  系统内平均时间W=%.2f分钟\n', W*60);
end
