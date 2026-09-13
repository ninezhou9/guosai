function run_all_figures()
%RUN_ALL_FIGURES 一次生成论文三张数据图（图1~图3），并打印汇总。
% 运行方式（本机）：
%   >> cd('C:\Users\sss\Desktop\国赛\代码\matlab')
%   >> run_all_figures
% 或命令行：
%   "E:\MATLAB\R2025b\bin\matlab.exe" -batch "run_all_figures"
ROOT = 'C:\Users\sss\Desktop\国赛';
OUTDIR = fullfile(ROOT,'代码','figures','论文数据图');
if ~isfolder(OUTDIR), mkdir(OUTDIR); end

t0 = tic;
fprintf('================ 论文数据图生成 ================\n');
fprintf('数据源：%s\n', fullfile(ROOT,'基础数据','附件2.xlsx'));
fprintf('输出目录：%s\n\n', OUTDIR);

fprintf('--- 图1 全年时序热力图 ---\n');       fig1_annual_heatmap();
fprintf('\n--- 图2 典型日分位带 ---\n');       fig2_typical_day_band();
fprintf('\n--- 图3 滞后自相关 ---\n');         fig3_acf();

fprintf('\n================ 生成完毕，用时 %.1f s ================\n', toc(t0));
d = dir(fullfile(OUTDIR,'*'));
d = d(~[d.isdir]);
for k = 1:numel(d)
    fprintf('  %-16s  %8.1f KB\n', d(k).name, d(k).bytes/1024);
end
end
