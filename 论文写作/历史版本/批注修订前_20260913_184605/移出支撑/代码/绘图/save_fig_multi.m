function files = save_fig_multi(fig, base)
%SAVE_FIG_MULTI 统一输出：300 dpi PNG + SVG 矢量图 + 可编辑 FIG。
%   base 为不含扩展名的绝对路径（可含中文）。
pngFile = [base '.png'];
svgFile = [base '.svg'];
figFile = [base '.fig'];

exportgraphics(fig, pngFile, 'Resolution', 300, 'BackgroundColor','white');
try
    exportgraphics(fig, svgFile, 'ContentType','vector', 'BackgroundColor','white');
catch ME
    print(fig, svgFile, '-dsvg', '-vector');
    fprintf('  [提示] exportgraphics 导出 SVG 失败(%s)，已回退 print -dsvg\n', ME.identifier);
end
savefig(fig, figFile);
files = {pngFile, svgFile, figFile};
for k = 1:numel(files)
    d = dir(files{k});
    if isempty(d)
        fprintf('  [异常] 未生成 %s\n', files{k});
    else
        fprintf('  [输出] %s  (%.1f KB)\n', files{k}, d.bytes/1024);
    end
end
end
