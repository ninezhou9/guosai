"""Dump exact geometry / colours / fonts of a PPTX slide so the style can be cloned."""
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

path = sys.argv[1]
z = zipfile.ZipFile(path)

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def q(tag):
    pre, local = tag.split(":")
    return "{%s}%s" % (NS[pre], local)


pres = ET.fromstring(z.read("ppt/presentation.xml"))
sld = pres.find(q("p:sldSz"))
CX, CY = int(sld.get("cx")), int(sld.get("cy"))
print(f"slide EMU = {CX} x {CY}   -> px(96dpi-ish) = {CX/9525:.1f} x {CY/9525:.1f}")
EMU_PX = CX / 1280.0  # treat slide as 1280px wide
print(f"EMU per design-px (assuming 1280 wide) = {EMU_PX:.1f}\n")


def px(v):
    return round(int(v) / EMU_PX, 1)


def fill_of(el):
    for tag in ("solidFill", "noFill", "gradFill", "pattFill"):
        f = el.find(".//" + q("a:" + tag))
        if f is not None:
            if tag != "solidFill":
                return tag
            c = f.find(q("a:srgbClr"))
            if c is not None:
                return "#" + c.get("val")
            return "scheme"
    return None


def line_of(el):
    ln = el.find(".//" + q("a:ln"))
    if ln is None:
        return None, None
    w = ln.get("w")
    c = ln.find(q("a:srgbClr"))
    col = "#" + c.get("val") if c is not None else "scheme"
    dash = ln.find(".//" + q("a:prstDash"))
    return col, (round(int(w) / EMU_PX, 2) if w else None), (dash.get("val") if dash is not None else None)


root = ET.fromstring(z.read("ppt/slides/slide1.xml"))
tree = root.find(q("p:cSld")).find(q("p:spTree"))

idx = 0
for el in list(tree):
    tag = el.tag.split("}")[1]
    if tag not in ("sp", "cxnSp", "grpSp"):
        continue
    idx += 1
    nv = el.find(".//" + q("p:cNvPr"))
    name = nv.get("name") if nv is not None else "?"
    xfrm = el.find(".//" + q("a:xfrm"))
    if xfrm is None:
        print(f"[{idx}] {tag} {name!r} (no xfrm)")
        continue
    off, ext = xfrm.find(q("a:off")), xfrm.find(q("a:ext"))
    x, y = px(off.get("x")), px(off.get("y"))
    w, h = px(ext.get("cx")), px(ext.get("cy"))
    flipH = xfrm.get("flipH") == "1"
    sl = el.find(".//" + q("p:spPr")) or el.find(q("p:spPr"))
    f = fill_of(sl) if sl is not None else None
    ln = line_of(sl) if sl is not None else (None, None, None)
    line = f"line={ln[0]} w={ln[1]} dash={ln[2]}"
    print(f"[{idx}] {tag:5s} {name!r:28s} x={x:6.1f} y={y:6.1f} w={w:6.1f} h={h:6.1f} flipH={flipH} fill={f} {line}")
    # text runs
    for para in el.findall(".//" + q("a:p")):
        runs = []
        for r in para.findall(q("a:r")):
            t = r.find(q("a:t"))
            rPr = r.find(q("a:rPr"))
            sz = rPr.get("sz") if rPr is not None else None
            b = rPr.get("b") if rPr is not None else None
            col = None
            if rPr is not None:
                c = rPr.find(".//" + q("a:srgbClr"))
                col = "#" + c.get("val") if c is not None else None
            runs.append(f"{(t.text or '')!r} sz={sz} b={b} {col}")
        if runs:
            algn = para.find(q("a:pPr"))
            al = algn.get("algn") if algn is not None else None
            print(f"        algn={al} :: " + " | ".join(runs))
