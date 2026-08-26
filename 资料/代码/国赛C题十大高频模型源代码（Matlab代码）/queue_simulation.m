% 系统模拟/队列模拟（适用于排队系统分析场景）
% 数据生成：模拟机场出租车排队系统
rng(4); % 固定随机种子
lambda = 4; % 乘客到达率(辆/分钟)
mu = 6; % 服务率(辆/分钟)
sim_time = 1000; % 模拟时间(分钟)

% 初始化变量
arrival_time = 0;
wait_time = 0;
queue_length = 0;
service_end = 0;
total_wait = 0;
count = 0;

% 执行模拟
while arrival_time < sim_time
    arrival_time = arrival_time + exprnd(1/lambda); % 泊松到达间隔
    if arrival_time > sim_time, break; end
    count = count + 1;
    
    if arrival_time >= service_end
        wait = 0;
        service_end = arrival_time + exprnd(1/mu); % 指数服务时间
    else
        wait = service_end - arrival_time;
        service_end = service_end + exprnd(1/mu);
        queue_length = queue_length + 1;
    end
    total_wait = total_wait + wait;
end

% 输出结果
fprintf('队列模拟结果：\n');
fprintf('模拟乘客总数：%d人\n', count);
fprintf('平均等待时间：%.2f分钟\n', total_wait/count);
fprintf('平均队列长度：%.2f辆\n', queue_length/sim_time);
