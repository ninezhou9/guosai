function verify_acf()
%VERIFY_ACF 独立交叉验证图3 的自相关结果（临时诊断脚本）。
[L, V] = load_annex2();
MAXLAG_H = 168;
for which = 1:2
    if which == 1, A = L; nm = '负荷'; else, A = V; nm = '光伏'; end
    [r, lagsH] = acf_10min(A, MAXLAG_H);
    x = reshape(A.', 1, []);
    N = numel(x);
    fprintf('\n=== %s (N=%d) ===\n', nm, N);
    fprintf('   滞后h   FFT-xcorrACF   直接Pearson    偏差\n');
    for Lh = [1 6 12 24 48 72 96 120 144 168]
        k = Lh*6;
        a = x(1:N-k).'; b = x(1+k:N).';
        rr = corr(a, b);
        ra = at(r, lagsH, Lh);
        fprintf('   %5d   %10.4f   %10.4f   %+.4f\n', Lh, ra, rr, ra-rr);
    end
    % 逐日配对相关性（日滞后 k 天），验证"周周期"是否真实存在
    fprintf('   逐日配对（365 天两两按日滞后）:\n');
    for k = [1 2 3 4 7 14]
        cc = zeros(365-k,1);
        for d = 1:365-k
            cc(d) = corr(A(d,:).', A(d+k,:).');
        end
        fprintf('     日滞后 %2d 天: 均值=%.4f  中位=%.4f  最小=%.4f  最大=%.4f\n', ...
            k, mean(cc), median(cc), min(cc), max(cc));
    end
end
end

function y = at(r, lagsH, lh)
k = find(abs(lagsH - lh) < 1e-9, 1);
y = r(k);
end
