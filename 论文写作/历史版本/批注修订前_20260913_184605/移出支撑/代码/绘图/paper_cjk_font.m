function f = paper_cjk_font()
%PAPER_CJK_FONT 选择本机可用的中文论文常用字体，找不到则回退 Helvetica。
cands = {'SimSun','宋体','NSimSun','新宋体','Microsoft YaHei','微软雅黑', ...
         'SimHei','黑体','Noto Sans CJK SC','Source Han Sans SC'};
av = listfonts;
f = 'Helvetica';
for k = 1:numel(cands)
    if any(strcmpi(av, cands{k}))
        f = cands{k};
        return
    end
end
warning('paper_cjk_font:noCJK', '未找到中文字体，已回退到 Helvetica，图中中文可能显示为方框。');
end
