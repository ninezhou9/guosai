function style_axes(ax, S)
%STYLE_AXES 统一坐标轴外观：字体、刻度方向、线宽、去顶右边框、去掉坐标区工具栏。
set(ax, 'FontName',S.font, 'FontSize',S.fsTick, ...
        'LineWidth',S.axLW, 'TickDir','out', 'TickLength',[0.012 0.012], ...
        'XColor',S.cInk, 'YColor',S.cInk, 'Box','off', 'Color','w');
% 去掉 axes toolbar，否则 exportgraphics 会把右上角悬浮工具栏印进图里
try
    ax.Toolbar = [];
catch
    try, ax.Toolbar.Visible = 'off'; catch, end
end
end
