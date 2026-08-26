from __future__ import annotations

import json
import logging
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.CRITICAL)


ROOT = Path(r"C:\Users\qwerq\Desktop\数模\优秀论文")
OUT = Path(r"C:\Users\qwerq\Desktop\数模\优秀论文语料审计.json")

SECTION_PATTERNS = {
    "摘要": r"摘\s*要",
    "关键词": r"关\s*键\s*词",
    "问题重述": r"问题\s*(?:重述|提出|背景)",
    "问题分析": r"问题\s*分析",
    "模型假设": r"模型\s*假设|基本\s*假设",
    "符号说明": r"符号\s*(?:说明|约定)",
    "数据预处理": r"数据\s*(?:预处理|处理|清洗)",
    "模型建立": r"模型.{0,4}(?:建立|构建)",
    "模型求解": r"模型.{0,4}求解|求解\s*过程",
    "结果分析": r"结果\s*(?:分析|讨论)",
    "模型检验": r"模型.{0,4}(?:检验|验证)|误差\s*分析|灵敏度\s*分析|敏感性\s*分析",
    "模型评价": r"模型.{0,4}(?:评价|优缺点|推广)|优点|缺点",
    "参考文献": r"参考\s*文献",
    "附录": r"附\s*录",
}

STYLE_TERMS = [
    "本文", "我们", "针对问题", "针对第", "首先", "其次", "然后", "最后",
    "因此", "从而", "进而", "综上", "结果表明", "由图", "由表", "可知",
    "建立", "构建", "求得", "得到", "计算得", "验证", "检验", "灵敏度",
    "敏感性", "误差", "稳健", "鲁棒", "显著", "较好", "合理", "有效",
    "创新", "推广", "局限", "不足", "假设", "约束", "目标函数",
]


def year_of(path: Path) -> str:
    match = re.search(r"(20\d{2})年", str(path))
    return match.group(1) if match else "其他"


def is_paper(path: Path) -> bool:
    text = str(path)
    return "优秀论文" in text and "赛题" not in text and "论文格式规范" not in text


def read_selected_pages(reader: PdfReader) -> tuple[str, list[int]]:
    n = len(reader.pages)
    indices = list(range(min(8, n)))
    indices += list(range(max(8, n - 3), n))
    indices = sorted(set(indices))
    chunks = []
    for index in indices:
        try:
            chunks.append(reader.pages[index].extract_text() or "")
        except Exception:
            chunks.append("")
    return "\n".join(chunks), indices


def main() -> None:
    rows = []
    errors = []
    for path in sorted(ROOT.rglob("*.pdf")):
        if not is_paper(path):
            continue
        try:
            reader = PdfReader(path)
            text, selected = read_selected_pages(reader)
            compact = re.sub(r"\s+", "", text)
            sections = {
                name: bool(re.search(pattern, text, re.I | re.S))
                for name, pattern in SECTION_PATTERNS.items()
            }
            terms = {term: compact.count(term) for term in STYLE_TERMS}
            rows.append({
                "path": str(path),
                "name": path.name,
                "year": year_of(path),
                "pages": len(reader.pages),
                "selected_pages": [i + 1 for i in selected],
                "extracted_chars": len(compact),
                "sections": sections,
                "terms": terms,
                "opening_excerpt": compact[:700],
            })
        except Exception as exc:
            errors.append({"path": str(path), "error": repr(exc)})

    usable = [row for row in rows if row["extracted_chars"] >= 1000]
    section_counts = Counter()
    term_counts = Counter()
    by_year = defaultdict(lambda: {"files": 0, "usable": 0, "pages": []})
    for row in rows:
        yr = by_year[row["year"]]
        yr["files"] += 1
        yr["pages"].append(row["pages"])
        if row["extracted_chars"] >= 1000:
            yr["usable"] += 1
            section_counts.update(name for name, found in row["sections"].items() if found)
            term_counts.update(row["terms"])

    year_summary = {}
    for year, data in sorted(by_year.items()):
        pages = data.pop("pages")
        year_summary[year] = {
            **data,
            "median_pages": statistics.median(pages) if pages else None,
            "mean_pages": round(statistics.mean(pages), 1) if pages else None,
        }

    result = {
        "method": "Extracted pages 1-8 and final 3 pages of each PDF classified as an excellent paper.",
        "paper_count": len(rows),
        "usable_text_count": len(usable),
        "errors": errors,
        "year_summary": year_summary,
        "section_frequency_usable": {
            name: {
                "count": section_counts[name],
                "rate": round(section_counts[name] / len(usable), 3) if usable else 0,
            }
            for name in SECTION_PATTERNS
        },
        "style_term_totals": dict(term_counts.most_common()),
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ["paper_count", "usable_text_count", "errors", "year_summary", "section_frequency_usable", "style_term_totals"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
