function c = tint(c, a)
%TINT 把颜色 c 按权重 a 与白色混合（等价于 alpha=a 的半透明叠加，但为不透明色）。
%   用于矢量导出：SVG/PDF 的 painters 渲染器对 patch 透明度支持不佳，
%   改用"与白混合得到的浅色"可保证矢量输出颜色完全一致。
c = a*reshape(c,1,3) + (1-a)*ones(1,3);
end
