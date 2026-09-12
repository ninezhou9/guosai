function [L,V,xc,doyM,mLab,meta] = load_annex2()
%LOAD_ANNEX2 读取 2025 全年小区负载与光伏实际功率（附件2.xlsx）。
%   输出
%     L   365×144 double，小区负载实际功率 / kW，行=日期(1/1→12/31)，列=10 min 时段
%     V   365×144 double，光伏发电实际功率 / kW，同上
%     xc  1×144 double，时段中心时刻 / h（0.0833:1/6:23.9167）
%     doyM 1×12 double，各月 1 日的年内日序（用于热力图纵轴月份刻度）
%     mLab 1×12 cell，月份标签 {'1月',...,'12月'}
%     meta 结构体，数据来源与校验信息
ROOT = 'C:\Users\sss\Desktop\国赛';
XLS  = fullfile(ROOT,'基础数据','附件2.xlsx');
assert(isfile(XLS), '找不到数据文件：%s', XLS);

SH_LOAD = '小区负载';
SH_PV   = '光伏发电实际功率';
L = readmatrix(XLS,'Sheet',SH_LOAD,'Range','B2:EO366');
V = readmatrix(XLS,'Sheet',SH_PV  ,'Range','B2:EO366');

% ---- 结构校验：与 代码/q2_solution.py 中的断言保持一致 ----
assert(isequal(size(L),[365 144]), '负载表尺寸异常：%s', mat2str(size(L)));
assert(isequal(size(V),[365 144]), '光伏表尺寸异常：%s', mat2str(size(V)));
assert(all(isfinite(L(:))) && all(isfinite(V(:))), '数据中存在 NaN/Inf');
assert(all(L(:)>=0) && all(V(:)>=0), '数据中存在负功率');

xc = (0.5:143.5)/6;                        % 10 min 时段中心，单位 h
doyM = days(datetime(2025,1:12,1) - datetime(2025,1,1)) + 1;
mLab = arrayfun(@(m) sprintf('%d月',m), 1:12, 'Uni', 0);

meta = struct('file',XLS,'load_sheet',SH_LOAD,'pv_sheet',SH_PV, ...
    'shape',size(L),'N',numel(L), ...
    'load_min',min(L(:)),'load_max',max(L(:)), ...
    'pv_min',min(V(:)),'pv_max',max(V(:)), ...
    'date_range','2025-01-01 ~ 2025-12-31','dt_min',10);
end
