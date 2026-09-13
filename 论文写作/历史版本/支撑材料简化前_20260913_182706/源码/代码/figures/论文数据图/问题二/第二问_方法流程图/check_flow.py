"""Verify the rendered Q2 flowchart: colour probes + ink coverage + text presence."""
from PIL import Image
import numpy as np
import sys

path = sys.argv[1]
img = Image.open(path).convert("RGB")
W, H = img.size
sx, sy = W / 1280.0, H / 720.0
print(f"image={W}x{H} scale=({sx:.3f},{sy:.3f})")


def hexrgb(t):
    return "#%02X%02X%02X" % tuple(int(v) for v in t)


def near(a, b, tol=20):
    return all(abs(int(x) - int(y)) <= tol for x, y in zip(a, b))


NAVY = (30, 79, 168)        # #1E4FA8
NODE = (240, 245, 252)      # #F0F5FC
ACCENT = (232, 239, 248)    # #E8EFF8
BAND = (247, 249, 252)      # #F7F9FC
DARKBLUE = (14, 63, 140)    # #0E3F8C
WHITE = (255, 255, 255)

probes = [
    ("页眉深蓝顶条", (640, 36), NAVY),
    ("阶段一标签底色", (300, 114), NAVY),
    ("阶段二标签底色", (900, 338), NAVY),
    ("节点1 填充", (200, 160), NODE),
    ("节点1 深蓝描边", (41, 215), NAVY),
    ("节点1 编号方块", (69, 169), NAVY),
    ("节点2 填充", (640, 160), NODE),
    ("节点3 填充", (1050, 160), NODE),
    ("节点4 填充", (200, 400), NODE),
    ("节点5 填充", (640, 400), NODE),
    ("节点6 填充(强调)", (1050, 400), ACCENT),
    ("行内箭头1", (425, 215), NAVY),
    ("行内箭头2(第二阶段)", (425, 439), NAVY),
    ("折返横线", (600, 314), NAVY),
    ("折返竖线(右)", (1055, 300), NAVY),
    ("折返竖线(左)", (225, 340), NAVY),
    ("入输出箭头", (1055, 525), NAVY),
    ("底部口径框", (400, 580), BAND),
    ("底部输出框", (1000, 560), ACCENT),
    ("页脚右侧留白", (1270, 710), WHITE),
]

ok = 0
total = 0
for name, (x, y), expect in probes:
    px = min(int(round(x * sx)), W - 1)
    py = min(int(round(y * sy)), H - 1)
    rgb = img.getpixel((px, py))
    hit = near(rgb, expect)
    total += 1
    ok += 1 if hit else 0
    print(f"  [{'HIT ' if hit else 'MISS'}] {name:20s} @({px},{py}) = {hexrgb(rgb)} expect {hexrgb(expect)}")

print(f"\ncolour probes: {ok}/{total}")

arr = np.asarray(img).astype(int)
lum = arr.sum(axis=2)

# text ink inside node-1 title row and body (slide coords)
def ink(x0, y0, x1, y1, thresh=560):
    a = lum[int(y0 * sy):int(y1 * sy), int(x0 * sx):int(x1 * sx)]
    return (a < thresh).mean()


regions = [
    ("节点1 标题行墨量", (84, 152, 360, 180)),
    ("节点1 正文墨量", (84, 190, 390, 285)),
    ("节点2 正文墨量", (499, 190, 805, 285)),
    ("节点3 正文墨量", (914, 190, 1220, 285)),
    ("节点4 正文墨量", (84, 414, 390, 509)),
    ("节点5 正文墨量", (499, 414, 805, 509)),
    ("节点6 正文墨量", (914, 414, 1220, 509)),
    ("标签一文字墨量", (60, 100, 580, 130)),
    ("口径框文字墨量", (56, 556, 744, 630)),
    ("输出框文字墨量", (796, 556, 1224, 630)),
]
print("\ntext ink (fraction of dark pixels per region):")
for name, (x0, y0, x1, y1) in regions:
    print(f"  {name:16s} {ink(x0, y0, x1, y1) * 100:5.2f}%")

print("\nnon-white coverage by 72px band:")
band = int(72 * sy)
for i in range(10):
    y0, y1 = i * band, min((i + 1) * band, H)
    if y0 >= H:
        break
    print(f"  y {i*72:3d}-{min((i+1)*72,720):3d}: {(lum[y0:y1] < 730).mean()*100:5.1f}%")
