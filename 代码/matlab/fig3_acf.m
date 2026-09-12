function fig3_acf()
%FIG3_ACF
% 图3 负荷与光伏序列的滞后自相关特征
% 内容：10 min 分辨率全年序列的 Pearson 自相关曲线（r(0)=1，偏置估计量），
%       滞后 0~168 h，覆盖完整 7 天。上=(a)负荷，下=(b)光伏。
%       在 24 / 48 / 72 / 168 h 处绘制淡色垂直参考线，重点标记并标注
%       24 h 与 168 h 的实际 ρ 值：24 h=昨日同刻，72 h=近 3 日，168 h=上周同刻/近 7 日。
% 说明：95% 显著性区间按真实样本量计算（±1.96/√N），N=52560 时约 ±0.009，
%       视觉意义极有限，按要求不绘制，仅在图外脚注中注明数值。
% 数据：附件2.xlsx 原始实际功率，不做平滑、不造峰，若数据本身无对应峰值即如实显示。
% 输出：300 dpi PNG + SVG + FIG。

S = paper_style();
[L, V] = load_annex2();
OUTDIR = fig_outdir();
base = fullfile(OUTDIR, '图3_负荷与光伏序列的滞后自相关特征');

MAXLAG_H = 168;
[rL, lagsH] = acf_10min(L, MAXLAG_H);
[rV, ~]      = acf_10min(V, MAXLAG_H);

N   = numel(L);
sig = 1.96/sqrt(N);
fprintf('图3 样本量 N = %d，95%% 显著性区间 = ±%.5f（过窄，按要求不绘制）\n', N, sig);
for lh = [0 1 24 48 72 168]
    fprintf('  滞后 %3d h :  负荷 rho=%.4f  |  光伏 rho=%.4f\n', ...
        lh, at(rL,lagsH,lh), at(rV,lagsH,lh));
end

fig = figure('Units','centimeters','Position',[2 2 22 14.5],'Color','w');
ax1 = axes(fig,'Position',[0.098 0.560 0.875 0.320]);
ax2 = axes(fig,'Position',[0.098 0.145 0.875 0.320]);
% axes() 的 NextPlot 默认为 'replace'，必须 hold on 才不会互相清除图元
hold(ax1,'on'); hold(ax2,'on');

draw_panel(ax1, lagsH, rL, S.cLoad, S, false);
draw_panel(ax2, lagsH, rV, S.cPV , S, true);

title(ax1,'(a) 负荷序列滞后自相关','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);
title(ax2,'(b) 光伏序列滞后自相关','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);
xlabel(ax2,'滞后时间/h','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);
ylabel(ax1,'自相关系数','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);
ylabel(ax2,'自相关系数','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);

annotation(fig,'textbox',[0 0.004 1 0.032], ...
    'String', sprintf('注：24 h 对应昨日同刻，72 h 对应近 3 日，168 h 对应上周同刻及近 7 日；95%% 自相关显著性区间按真实样本量计算为 ±%.4f（N = %d），过窄未绘制。', sig, N), ...
    'HorizontalAlignment','center','VerticalAlignment','middle', ...
    'EdgeColor','none','FitBoxToText','on','Margin',0, ...
    'FontName',S.font,'FontSize',S.fsNote,'Color',S.cGray);

save_fig_multi(fig, base);
close(fig);
end

% ---------------------------------------------------------------
function draw_panel(ax, lagsH, r, C, S, showXLab)
REF = [24 48 72 168];

plot(ax, lagsH, r, '-', 'Color', C, 'LineWidth', 1.7);
style_axes(ax, S);
set(ax,'XLim',[0 168],'FontSize',S.fsTick,'YDir','normal');

nLag = round(168*6)+1;
ymn  = min(r(1:nLag));
R    = 1 - ymn;
ylo  = ymn - 0.05*R;
yhi  = 1   + 0.10*R;
ylim(ax, [ylo yhi]);

for lh = REF
    xline(ax, lh, ':', 'Color', S.cRef, 'LineWidth', 0.7);
end

% 重点标记 24 h（昨日）与 168 h（上周）
for lh = [24 168]
    yv = at(r, lagsH, lh);
    plot(ax, lh, yv, 'o', 'MarkerSize',4.8, 'MarkerFaceColor',C, ...
         'MarkerEdgeColor','w', 'LineWidth',0.6);
    if lh > 150
        ha = 'right'; dx = -2.5; dy = -0.045;
    else
        ha = 'left';  dx =  2.5; dy =  0.022;
    end
    text(ax, lh+dx, yv+dy*R, sprintf('%d h: \\rho = %.3f', lh, yv), ...
        'FontName',S.font,'FontSize',S.fsLeg,'Color',S.cInk, ...
        'HorizontalAlignment',ha,'VerticalAlignment','bottom');
end

xticks(ax, 0:24:168);
if ~showXLab, xticklabels(ax, []); end
end

% ---------------------------------------------------------------
function y = at(r, lagsH, lh)
k = find(abs(lagsH - lh) < 1e-9, 1);
assert(~isempty(k), '滞后 %g h 超出计算范围', lh);
y = r(k);
end

function d = fig_outdir()
ROOT = 'C:\Users\sss\Desktop\国赛';
d = fullfile(ROOT,'代码','figures','论文数据图');
if ~isfolder(d), mkdir(d); end
end
