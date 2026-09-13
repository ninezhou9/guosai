function [r, lagsH] = acf_10min(A, maxLagH)
%ACF_10MIN 10 min 分辨率时间序列的滞后自相关（Pearson，偏置估计量，r(0)=1）。
%   A       365×144 矩阵（行=日，列=10 min 时段）
%   maxLagH 最大滞后时间 / h
%   返回 r (1×maxLagSteps+1) 与 lagsH（单位 h）
%
%   说明：展开顺序必须是"按时间先后"，即先把 A 转置成 144×365 再按列展开，
%   得到 [第1天 00:10…24:00, 第2天 00:10…24:00, …]。
%   直接写 A(:) 会变成"先遍历日期、再遍历时刻"的错误顺序。
maxLagSteps = round(maxLagH*6);
x = reshape(A.', 1, []);          % 按时间顺序展开
x = double(x(:).');
assert(all(isfinite(x)), '序列中存在 NaN/Inf');
x = x - mean(x);
c = xcorr(x, maxLagSteps);         % 长度为 2*L+1，索引 L+1 对应 lag 0
c = c(maxLagSteps+1:end);
r = c / c(1);                      % 偏置估计：分母为 sum(x^2)，即除以 N
lagsH = (0:maxLagSteps)/6;
end
