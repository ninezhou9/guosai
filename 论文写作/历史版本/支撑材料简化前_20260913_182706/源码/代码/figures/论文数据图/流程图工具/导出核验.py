"""用 LibreOffice 实际渲染每份流程图，导出 PDF/PNG，并检查公式残留。

依赖：pymupdf、Pillow、lxml；LibreOffice 需可执行。
python 导出核验.py --soffice /path/to/soffice
可通过 LD_LIBRARY_PATH 指定临时 LibreOffice 的依赖目录。
"""
import argparse
from collections import defaultdict
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as ET
from PIL import Image
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
FORMULA = re.compile(r"[=ΣΔ≤≥±×∈κ₀₁₂₃₄₅₆₇₈₉]|\b[A-Za-z]+_[A-Za-z0-9]+")


def check_source(path):
    with ZipFile(path) as z:
        for name in z.namelist():
            if not (name.startswith("ppt/slides/") and name.endswith(".xml")):
                continue
            root = ET.fromstring(z.read(name))
            assert not root.findall(".//m:oMath", NS), f"数学对象残留：{path}"
            for p in root.findall(".//a:p", NS):
                text = "".join(p.xpath(".//a:t/text()", namespaces=NS))
                assert not FORMULA.search(text), f"公式文字残留：{path} {text}"


def thumbnail(path, png):
    with ZipFile(path) as z:
        files = {name: z.read(name) for name in z.namelist()}
    changed = False
    for name in files:
        if name.startswith("docProps/thumbnail."):
            im = Image.open(png).convert("RGB")
            im.thumbnail((512, 512))
            out = BytesIO()
            im.save(out, format="PNG" if name.endswith(".png") else "JPEG")
            files[name] = out.getvalue()
            changed = True
    if changed:
        with ZipFile(path, "w", ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--soffice", default="libreoffice")
    args = ap.parse_args()
    groups = defaultdict(list)
    for path in sorted(ROOT.glob("问题*/*.pptx")):
        check_source(path)
        groups[path.parent].append(path)
    # 嵌套目录中的可编辑副本也必须与同名主文件同步。
    for path in sorted(ROOT.glob("问题*/*/*.pptx")):
        check_source(path)
        groups[path.parent].append(path)
    report = []
    with tempfile.TemporaryDirectory(prefix="guosai-render-") as tmp:
        for parent, paths in groups.items():
            subprocess.run([
                args.soffice, "-env:UserInstallation="+Path(tmp).as_uri(),
                "--headless", "--convert-to", "pdf", "--outdir", str(parent),
                *map(str, paths),
            ], env={**os.environ, "SAL_USE_VCLPLUGIN": "svp"}, check=True, timeout=180)
            for path in paths:
                pdf, png = path.with_suffix(".pdf"), path.with_suffix(".png")
                assert pdf.exists(), f"未导出：{pdf}"
                with pymupdf.open(pdf) as doc:
                    assert len(doc) == 1, f"意外多页：{pdf}"
                    page = doc[0]
                    assert not FORMULA.search(page.get_text()), f"渲染后仍有公式：{pdf}"
                    scale = 2560 / page.rect.width
                    page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).save(png)
                    report.append({"file": str(path.relative_to(ROOT)), "pages": 1,
                                   "formula_objects": 0, "formula_text": 0,
                                   "png_width": 2560})
                thumbnail(path, png)
                print("已导出并核验：", path.relative_to(ROOT), flush=True)
    (ROOT / "流程图工具/导出核验记录.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
