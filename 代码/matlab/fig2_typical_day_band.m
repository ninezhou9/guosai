function fig2_typical_day_band()
%FIG2_TYPICAL_DAY_BAND
% 图2 负荷与光伏典型日分布及波动区间
% 内容：24 h 典型日分位带图。对全年 365 天中同一 10 min 时刻的样本求分位数，
%       上方面板负荷、下方面板光伏；(a)/(b) 各含 Q50 中位线、Q25~Q75 深带、Q10~Q90 浅带。
% 数据：附件2.xlsx，全年同时刻样本，不做样条平滑，曲线直接由 10 min 分位结果连线。
% 输出：300 dpi PNG + SVG + FIG。

S = paper_style();
[L, V, xc] = load_annex2();
OUTDIR = fig_outdir();
base = fullfile(OUTDIR, '图2_负荷与光伏典型日分布及波动区间');

P = [10 25 50 75 90];              % 需要的分位点
qL = prctile(L, P, 1);             % 5×144，跨日按"同一时刻"统计
qV = prctile(V, P, 1);

fig = figure('Units','centimeters','Position',[2 2 22 14],'Color','w');
ax1 = axes(fig,'Position',[0.100 0.578 0.870 0.310]);
ax2 = axes(fig,'Position',[0.100 0.135 0.870 0.310]);
% axes() 的 NextPlot 默认为 'replace'，必须 hold on 才不会互相清除图元
hold(ax1,'on'); hold(ax2,'on');

xt  = 0:3:24;
xtl = arrayfun(@(h) sprintf('%02d:00',h), xt, 'Uni', 0);

draw_panel(ax1, xc, qL, S.cLoad, S, xt, xtl, []);
draw_panel(ax2, xc, qV, S.cPV , S, xt, xtl, xtl);

% 纵轴范围：各自独立，按真实分位带上下界留少量余量（不强行统一量程）
set(ax1,'YLim',[min(qL(1,:))*0.96, max(qL(5,:))*1.07]);
set(ax2,'YLim',[0, max(qV(5,:))*1.12]);

title(ax1,'(a) 负荷典型日分布','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);
title(ax2,'(b) 光伏典型日分布','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);
xlabel(ax2,'时刻','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);
ylabel(ax1,'功率/kW','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);
ylabel(ax2,'功率/kW','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);

fprintf('图2 负荷 Q50 范围 = [%.0f, %.0f] kW；Q10~Q90 最大带宽 = %.0f kW (第 %d 时段)\n', ...
    min(qL(3,:)), max(qL(3,:)), max(qL(5,:)-qL(1,:)), ...
    find((qL(5,:)-qL(1,:))==max(qL(5,:)-qL(1,:)),1));
fprintf('图2 光伏 Q50 峰值 = %.0f kW (第 %d 时段，约 %s)\n', ...
    max(qV(3,:)), find(qV(3,:)==max(qV(3,:)),1), hhmm(find(qV(3,:)==max(qV(3,:)),1)));
fprintf('图2 光伏 Q50 白天持续时长(>0) = %.1f h\n', sum(qV(3,:)>0)/6);

save_fig_multi(fig, base);
close(fig);
end

% ---------------------------------------------------------------
function draw_panel(ax, xc, q, C, S, xt, xtl, showXLab)
q10 = q(1,:); q25 = q(2,:); q50 = q(3,:); q75 = q(4,:); q90 = q(5,:);
xx  = [xc, fliplr(xc)];

% 用"与白混合的浅色"代替 alpha，保证 SVG/PDF 矢量输出颜色一致
h90 = fill(ax, xx, [q10, fliplr(q90)], tint(C,0.22), 'EdgeColor','none');
h75 = fill(ax, xx, [q25, fliplr(q75)], tint(C,0.45), 'EdgeColor','none');
hm  = plot(ax, xc, q50, '-', 'Color', C, 'LineWidth', 1.8);

style_axes(ax, S);
xticks(ax, xt);
if isempty(showXLab)
    xticklabels(ax, []);            % 上面板隐藏刻度文字，与下面板共享横轴
else
    xticklabels(ax, xtl);
end
set(ax,'XLim',[0 24],'FontSize',S.fsTick);

legend(ax, [hm h75 h90], ...
    {'中位数 Q_{50}','Q_{25}~Q_{75} 分位带','Q_{10}~Q_{90} 分位带'}, ...
    'Location','northwest','Box','off','FontName',S.font,'FontSize',S.fsLeg, ...
    'TextColor',S.cInk);
end

% ---------------------------------------------------------------
function s = hhmm(k)
% 第 k 个 10 min 时段中心的时刻字符串
m = 10*k; s = sprintf('%02d:%02d', floor(m/60), mod(m,60));
end

function d = fig_outdir()
ROOT = 'C:\Users\sss\Desktop\国赛';
d = fullfile(ROOT,'代码','figures','论文数据图');
if ~isfolder(d), mkdir(d); end
end
