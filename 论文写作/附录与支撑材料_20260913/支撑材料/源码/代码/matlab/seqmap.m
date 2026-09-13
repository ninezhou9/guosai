function cm = seqmap(c1, c2, c3, n)
%SEQMAP 构造"浅→中→深"的连续顺序色带（三段锚点线性插值），避免彩虹色带。
%   c1/c2/c3 为 1×3 RGB 锚点（浅、中、深），n 为色阶数。
if nargin < 4, n = 256; end
t  = linspace(0,1,n)';
cm = interp1([0 0.5 1], [c1; c2; c3], t, 'linear');
cm = min(max(cm, 0), 1);
end
