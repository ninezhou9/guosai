function S = paper_style()
%PAPER_STYLE 论文数据图统一样式：字体、字号、线宽、配色。
%   全部三张图共用，保证同一篇论文内视觉一致。
S.font   = paper_cjk_font();
S.fsTick = 8;      % 坐标轴刻度字号
S.fsLab  = 9;      % 坐标轴标签字号
S.fsTit  = 9;      % 子图标题 (a)/(b)
S.fsLeg  = 7.2;    % 图例
S.fsCb   = 7.5;    % 色条
S.fsNote = 6.8;    % 角标注释
S.axLW   = 0.75;   % 坐标轴线宽
S.cLoad  = [0.130 0.320 0.580];   % 负荷主色（蓝，冷）
S.cPV    = [0.780 0.330 0.050];   % 光伏主色（橙，暖）
S.cGray  = [0.400 0.400 0.400];
S.cRef   = [0.760 0.760 0.760];   % 参考线
S.cInk   = [0.120 0.120 0.120];   % 坐标轴文字
end
