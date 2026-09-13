function fig1_annual_heatmap()
%FIG1_ANNUAL_HEATMAP
% 图1 负荷与光伏全年时序分布特征
% 内容：双层"日期×日内时刻"热力图，上=负荷 L(d,t)，下=光伏 V(d,t)，共享横轴。
% 数据：附件2.xlsx（365 天 × 144 个 10 min 时段），直接使用原始实际数据，
%       不做平滑、不补值、不一致化处理。
% 版式：24 cm × 14 cm（约 12:7），白底，无网格、无 3D、无阴影。
% 输出：300 dpi PNG + SVG 矢量图 + FIG（figures/论文数据图/）。

S = paper_style();
[L, V, xc, doyM, mLab] = load_annex2();
OUTDIR = fig_outdir();
base = fullfile(OUTDIR, '图1_负荷与光伏全年时序分布特征');

fig = figure('Units','centimeters','Position',[2 2 24 14],'Color','w');

% ---------- 版面（手工定位，便于放两条独立色条）----------
pTop = [0.085 0.565 0.655 0.330];
pBot = [0.085 0.120 0.655 0.330];
pCbT = [0.762 0.565 0.015 0.330];
pCbB = [0.762 0.120 0.015 0.330];

ax1 = axes(fig,'Position',pTop);
ax2 = axes(fig,'Position',pBot);
% axes() 的 NextPlot 默认为 'replace'，必须 hold on 才不会互相清除图元
hold(ax1,'on'); hold(ax2,'on');

% ---------- 色带：负荷=冷色系，光伏=暖色系，均为连续顺序色带 ----------
cmLoad = seqmap([0.955 0.965 0.985], [0.420 0.600 0.780], [0.060 0.160 0.360], 256);
cmPV   = seqmap([1.000 0.980 0.945], [0.980 0.720 0.340], [0.660 0.130 0.030], 256);

% 色标范围：取数据真实极值并圆整到百位，不截断、不夸大
cl_load = [floor(min(L(:))/100)*100, ceil(max(L(:))/100)*100];
cl_pv   = [floor(min(V(:))/100)*100, ceil(max(V(:))/100)*100];

imagesc(ax1, xc, 1:365, L);
set(ax1,'YDir','reverse','XLim',[0 24],'YLim',[0.5 365.5],'Layer','top');
colormap(ax1, cmLoad); clim(ax1, cl_load);

imagesc(ax2, xc, 1:365, V);
set(ax2,'YDir','reverse','XLim',[0 24],'YLim',[0.5 365.5],'Layer','top');
colormap(ax2, cmPV);  clim(ax2, cl_pv);

% ---------- 坐标轴 ----------
xt = 0:3:24;
xtl = arrayfun(@(h) sprintf('%02d:00',h), xt, 'Uni', 0);

for ax = [ax1 ax2]
    style_axes(ax, S);
    set(ax,'XTick',xt,'YTick',doyM,'YTickLabel',mLab, ...
           'XLim',[0 24],'YLim',[0.5 365.5], ...
           'TickLength',[0.008 0.008],'FontSize',6.8);
    ylabel(ax,'日期','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);
end
set(ax1,'XTickLabel',[]);
set(ax2,'XTickLabel',xtl,'FontSize',7.5);
xlabel(ax2,'时刻','FontName',S.font,'FontSize',S.fsLab,'Color',S.cInk);

title(ax1,'(a) 负荷时序热力图','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);
title(ax2,'(b) 光伏时序热力图','FontName',S.font,'FontSize',S.fsTit, ...
      'FontWeight','normal','Color',S.cInk);

% ---------- 两条独立色条 ----------
cb1 = colorbar(ax1); cb1.Units = 'normalized'; cb1.Position = pCbT;
cb2 = colorbar(ax2); cb2.Units = 'normalized'; cb2.Position = pCbB;
for cb = [cb1 cb2]
    cb.FontName = S.font; cb.FontSize = S.fsCb;
    cb.LineWidth = S.axLW; cb.TickDirection = 'out';
    cb.Title.FontName = S.font; cb.Title.FontSize = S.fsCb; cb.Title.FontWeight = 'normal';
end
cb1.Title.String = '负荷功率/kW';
cb2.Title.String = '光伏功率/kW';

% ---------- 输出 ----------
fprintf('图1 负荷色标范围 = [%.1f, %.1f] kW\n', cl_load(1), cl_load(2));
fprintf('图1 光伏色标范围 = [%.1f, %.1f] kW\n', cl_pv(1), cl_pv(2));
save_fig_multi(fig, base);
close(fig);
end

function d = fig_outdir()
ROOT = 'C:\Users\sss\Desktop\国赛';
d = fullfile(ROOT,'代码','figures','论文数据图');
if ~isfolder(d), mkdir(d); end
end
