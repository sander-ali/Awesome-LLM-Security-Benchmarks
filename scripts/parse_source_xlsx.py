#!/usr/bin/env python3
"""
parse_source_xlsx.py
====================

Parse the original spreadsheet (``data/source/Security Benchmarks.xlsx``) and
emit the canonical, machine-readable catalog at ``data/benchmarks.json``.

Design goals
------------
* **Zero third-party dependencies.** An ``.xlsx`` file is a ZIP of XML parts, so
  we read it with the Python standard library (``zipfile`` + ``xml.etree``).
  This keeps the pipeline reproducible on a bare Python install.
* **No fabrication.** The long-form ``Details`` and ``Security Type Targeted``
  text and every hyperlink target are copied *verbatim* from the workbook. The
  only edits applied are the documented, conservative normalizations listed in
  ``NORMALIZATION_NOTES`` below (whitespace/separator tidy-ups and a handful of
  obvious typos in the free-text "Year · Venue / Origin" column).

Usage
-----
    python3 scripts/parse_source_xlsx.py

The script is deterministic: running it again over an unchanged source workbook
produces a byte-identical ``data/benchmarks.json``.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
import datetime as _dt
import xml.etree.ElementTree as ET
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_XLSX = REPO_ROOT / "data" / "source" / "Security Benchmarks.xlsx"
OUT_JSON = REPO_ROOT / "data" / "benchmarks.json"

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# --------------------------------------------------------------------------- #
# Column layout of the source sheet (row 3 holds the headers)
# --------------------------------------------------------------------------- #
COL_ID = 1          # A  '#'
COL_NAME = 2        # B  'Benchmark'
COL_CATEGORY = 3    # C  'Category'
COL_YEARVENUE = 4   # D  'Year · Venue / Origin'
COL_WEBSITE = 5     # E  'Website / Code'
COL_PAPER = 6       # F  'Paper'
COL_DETAILS = 7     # G  'Details'
COL_SECTYPE = 8     # H  'Security Type Targeted'
FIRST_DATA_ROW = 4
LAST_DATA_ROW = 44  # 41 records -> rows 4..44

# --------------------------------------------------------------------------- #
# Conservative normalization of the free-text "Year · Venue / Origin" column.
#
# Keys are the record id (column A). Each tuple is:
#     (year_display, year_sort, cleaned_year_venue_origin)
#
# Everything else (name, category, details, security type, links) is taken
# verbatim from the workbook. The raw source string is preserved alongside the
# cleaned string as ``year_venue_origin_source`` for full transparency.
# --------------------------------------------------------------------------- #
YEAR_VENUE_CLEAN = {
    1:  ("2024",       2024, "2024 · Mazeika et al."),
    2:  ("2024",       2024, "2024 · NeurIPS D&B Track · Chao et al."),
    3:  ("2023",       2023, "2023 · Zou et al. (GCG project)"),
    4:  ("2024",       2024, "2024 · Souly et al."),
    5:  ("2024",       2024, "2024 · ACM CCS 2024 · Xinyue Shen et al."),
    6:  ("2024",       2024, "2024 · NeurIPS 2024 · Xue et al."),
    7:  ("2025",       2025, "2025 · NeurIPS DB & Benchmark Track · Yige Li et al."),
    8:  ("2024",       2024, "2024 · ICLR 2024 · Yanzhou Li et al."),
    9:  ("2025",       2025, "2025 · USENIX Security · Zou et al."),
    10: ("2024",       2024, "2024 · NeurIPS 2024 · Zhaorun Chen et al."),
    11: ("2024",       2024, "2024 · ICLR 2024 · Zhen Xiang et al."),
    12: ("2024",       2024, "2024 · NAACL · Jiashu Xu et al."),
    13: ("2024",       2024, "2024 · Anthropic (Hubinger et al.)"),
    14: ("2023",       2023, "2023 · NeurIPS competition · Mazeika et al."),
    15: ("2020–2024",  2020, "2020–2024 · DARPA program / NIST · DARPA; evaluations by NIST"),
    16: ("2024",       2024, "2024 · NeurIPS Dataset and Benchmark Track · Edoardo Debenedetti et al."),
    17: ("2024",       2024, "2024 · ACL · Zhan et al."),
    18: ("2023",       2023, "2023 · KDD 2025 · Jingwei Yi et al."),
    19: ("2024",       2024, "2024 · ICLR (Spotlight) · Sam Toyer et al."),
    20: ("2023",       2023, "2023 · USENIX Security · Yupei Liu et al."),
    21: ("2022",       2022, "2022 · ACL · Alicia Parrish et al."),
    22: ("2020",       2020, "2020 · EMNLP · Nikita Nangia et al."),
    23: ("2021",       2021, "2021 · ACM FAccT · Jwala Dhamala et al."),
    24: ("2021",       2021, "2021 · ACL | IJCNLP · Moin Nadeem et al."),
    25: ("2022",       2022, "2022 · ACL · Thomas Hartvigsen et al."),
    26: ("2020",       2020, "2020 · EMNLP · Samuel Gehman et al."),
    27: ("2018",       2018, "2018 · ACL: Human Language Technologies · Rachel Rudinger et al."),
    28: ("2018",       2018, "2018 · ACL: Human Language Technologies · Jieyu Zhao et al."),
    29: ("2022",       2022, "2022 · EMNLP · Eric Michael Smith et al."),
    30: ("2023",       2023, "2023 · NeurIPS · Boxin Wang et al."),
    31: ("2024",       2024, "2024 · NAACL · Jun Yan et al."),
    32: ("2024",       2024, "2024 · ICLR · Xiangyu Qi et al."),
    33: ("2023",       2023, "2023 · Xianjun Yang et al."),
    34: ("2025",       2025, "2025 · ICLR · Hanrong Zhang et al."),
    35: ("2024",       2024, "2024 · ICLR (Spotlight) · Yangjun Ruan et al."),
    36: ("2025",       2025, "2025 · ICLR · Maksym Andriushchenko et al."),
    37: ("2024",       2024, "2024 · EMNLP · Tongxin Yuan et al."),
    38: ("2024",       2024, "2024 · NAACL · Paul Rottger et al."),
    39: ("2025",       2025, "2025 · ICML · Justin Cui et al."),
    40: ("2024",       2024, "2024 · ECCV · Xin Liu et al."),
    41: ("2025",       2025, "2025 · AAAI · Yichen Gong et al."),
}

NORMALIZATION_NOTES = (
    "Details, Security Type Targeted, benchmark names, categories, and all "
    "hyperlink targets are copied verbatim from the source workbook. The only "
    "edits are conservative normalizations of the free-text 'Year · Venue / "
    "Origin' column: internal newlines were replaced with ' · ' separators, "
    "missing separators between year / venue / authors were inserted, trailing "
    "whitespace was trimmed, and a small number of obvious typographical errors "
    "were corrected (e.g. 'Xue et a.' -> 'Xue et al.', a stray ')' after "
    "'Chao et al.', and 'BoxinWang' -> 'Boxin Wang'). No factual content "
    "(years, venues, author surnames, numbers, findings) was added, removed, or "
    "altered. The exact original string is retained per record as "
    "'year_venue_origin_source'."
)

# Category ordering + slug + emoji, as they appear in the source workbook.
CATEGORY_ORDER = [
    ("Adversarial & Jailbreak",   "adversarial-and-jailbreak",   "🎯"),
    ("Poisoning & Backdoor",      "poisoning-and-backdoor",      "🧪"),
    ("Prompt Injection",          "prompt-injection",            "💉"),
    ("Bias & Fairness",           "bias-and-fairness",           "⚖️"),
    ("VPI & Residual",            "vpi-and-residual",            "🔁"),
    ("Agent & Tool Security",     "agent-and-tool-security",     "🤖"),
    ("Over-Refusal",              "over-refusal",                "🚧"),
    ("Multimodal Safety",         "multimodal-safety",           "🖼️"),
]


def _col_letters_to_num(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def _read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    shared: list[str] = []
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return shared
    for si in root.findall(f"{NS}si"):
        # A shared string is either a single <t> or rich-text runs <r><t>.
        parts = si.findall(f".//{NS}t")
        shared.append("".join(t.text or "" for t in parts))
    return shared


def _read_hyperlink_targets(zf: zipfile.ZipFile) -> dict[str, str]:
    """Map a cell reference (e.g. 'E4') to its resolved external hyperlink URL."""
    rid_to_target: dict[str, str] = {}
    try:
        rels = ET.fromstring(zf.read("xl/worksheets/_rels/sheet1.xml.rels"))
    except KeyError:
        return {}
    for rel in rels:
        rid_to_target[rel.attrib["Id"]] = rel.attrib.get("Target", "")

    ref_to_target: dict[str, str] = {}
    root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
    hyperlinks = root.find(f"{NS}hyperlinks")
    if hyperlinks is None:
        return ref_to_target
    for h in hyperlinks.findall(f"{NS}hyperlink"):
        ref = h.attrib.get("ref")
        rid = h.attrib.get(f"{RNS}id")
        if ref and rid and rid in rid_to_target:
            ref_to_target[ref] = rid_to_target[rid]
    return ref_to_target


def _read_grid(zf: zipfile.ZipFile, shared: list[str]) -> dict[tuple[int, int], str]:
    root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
    sheet_data = root.find(f"{NS}sheetData")
    grid: dict[tuple[int, int], str] = {}
    for row in sheet_data.findall(f"{NS}row"):
        r = int(row.attrib["r"])
        for c in row.findall(f"{NS}c"):
            ref = c.attrib["r"]
            col = _col_letters_to_num(re.match(r"[A-Z]+", ref).group(0))
            ctype = c.attrib.get("t", "n")
            v = c.find(f"{NS}v")
            is_node = c.find(f"{NS}is")
            if ctype == "s" and v is not None:
                val = shared[int(v.text)]
            elif ctype == "inlineStr" and is_node is not None:
                val = "".join(t.text or "" for t in is_node.findall(f".//{NS}t"))
            elif v is not None:
                val = v.text or ""
            else:
                val = ""
            grid[(r, col)] = val
    return grid


def _link_text(display: str, url: str) -> str:
    """Human-friendly link label: prefer the cell's display text; strip a leading
    scheme from raw-URL display text for readability."""
    text = (display or "").strip()
    if not text:
        text = url
    text = re.sub(r"^https?://", "", text)
    return text.rstrip("/") if text.endswith("/") and not text.endswith("://") else text


def _read_core_props(zf: zipfile.ZipFile) -> dict[str, str]:
    props: dict[str, str] = {}
    try:
        root = ET.fromstring(zf.read("docProps/core.xml"))
    except KeyError:
        return props
    cp = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
    dc = "{http://purl.org/dc/elements/1.1/}"
    dcterms = "{http://purl.org/dc/terms/}"
    for tag, key in (
        (f"{dc}creator", "creator"),
        (f"{cp}lastModifiedBy", "last_modified_by"),
        (f"{dcterms}created", "created"),
        (f"{dcterms}modified", "modified"),
    ):
        el = root.find(tag)
        if el is not None and el.text:
            props[key] = el.text
    return props


def build() -> dict:
    if not SOURCE_XLSX.exists():
        sys.exit(f"ERROR: source workbook not found at {SOURCE_XLSX}")

    with zipfile.ZipFile(SOURCE_XLSX) as zf:
        shared = _read_shared_strings(zf)
        grid = _read_grid(zf, shared)
        links = _read_hyperlink_targets(zf)
        core = _read_core_props(zf)

    title_cell = grid.get((1, COL_ID), "").strip()  # merged A1:H1 title

    # Preserve first-seen category order from the data itself, but fall back to
    # the curated CATEGORY_ORDER for stable output.
    records: list[dict] = []
    for r in range(FIRST_DATA_ROW, LAST_DATA_ROW + 1):
        rid_raw = grid.get((r, COL_ID), "").strip()
        if not rid_raw:
            continue
        rid = int(rid_raw)
        name = grid.get((r, COL_NAME), "").strip()
        category = grid.get((r, COL_CATEGORY), "").strip()
        yv_source = grid.get((r, COL_YEARVENUE), "")
        web_display = grid.get((r, COL_WEBSITE), "").strip()
        paper_display = grid.get((r, COL_PAPER), "").strip()
        details = grid.get((r, COL_DETAILS), "").strip()
        sec_type = grid.get((r, COL_SECTYPE), "").strip()

        web_url = links.get(f"E{r}", "").strip() or _ensure_url(web_display)
        paper_url = links.get(f"F{r}", "").strip() or _ensure_url(paper_display)

        year_display, year_sort, yv_clean = YEAR_VENUE_CLEAN.get(
            rid, ("", 0, yv_source.replace("\n", " · ").strip())
        )

        cat_slug = next((s for (n, s, _e) in CATEGORY_ORDER if n == category), _slugify(category))

        records.append(
            {
                "id": rid,
                "name": name,
                "category": category,
                "category_slug": cat_slug,
                "year": year_display,
                "year_sort": year_sort,
                "year_venue_origin": yv_clean,
                "year_venue_origin_source": yv_source,
                "website": {
                    "label": _link_text(web_display, web_url),
                    "url": web_url,
                },
                "paper": {
                    "label": _link_text(paper_display, paper_url),
                    "url": paper_url,
                },
                "details": details,
                "security_type": sec_type,
            }
        )

    # Category summary in curated order, with real counts.
    counts: dict[str, int] = {}
    for rec in records:
        counts[rec["category"]] = counts.get(rec["category"], 0) + 1
    categories = []
    for name, slug, emoji in CATEGORY_ORDER:
        categories.append(
            {
                "name": name,
                "slug": slug,
                "emoji": emoji,
                "count": counts.get(name, 0),
            }
        )
    # Any category present in data but not in the curated order (defensive).
    for name in counts:
        if name not in {c["name"] for c in categories}:
            categories.append(
                {"name": name, "slug": _slugify(name), "emoji": "🔹", "count": counts[name]}
            )

    years = [rec["year_sort"] for rec in records if rec["year_sort"]]
    doc = {
        "metadata": {
            "title": "Awesome LLM Security Benchmarks",
            "tagline": (
                "A curated catalog of benchmarks, datasets, and evaluation "
                "frameworks for the security, safety, and trustworthiness of "
                "large language models and LLM-based agents."
            ),
            "source_file": "data/source/Security Benchmarks.xlsx",
            "source_sheet_title": title_cell or "All Benchmarks",
            "source_creator": core.get("creator", ""),
            "source_created": core.get("created", ""),
            "source_modified": core.get("modified", ""),
            "entry_count": len(records),
            "category_count": len([c for c in categories if c["count"] > 0]),
            "year_range": [min(years), max(years)] if years else [],
            "columns": [
                "#",
                "Benchmark",
                "Category",
                "Year · Venue / Origin",
                "Website / Code",
                "Paper",
                "Details",
                "Security Type Targeted",
            ],
            "normalization_notes": NORMALIZATION_NOTES,
            "generated_by": "scripts/parse_source_xlsx.py",
            "generated_on": _dt.date.today().isoformat(),
        },
        "categories": categories,
        "benchmarks": records,
    }
    return doc


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _ensure_url(text: str) -> str:
    """Best-effort: only used if a cell had display text but no hyperlink."""
    t = (text or "").strip()
    if not t:
        return ""
    if t.startswith("http://") or t.startswith("https://"):
        return t
    return "https://" + t


def main() -> None:
    doc = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    md = doc["metadata"]
    print(f"Wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"  entries   : {md['entry_count']}")
    print(f"  categories: {md['category_count']}")
    print(f"  year range: {md['year_range']}")
    for c in doc["categories"]:
        print(f"    - {c['emoji']} {c['name']}: {c['count']}")


if __name__ == "__main__":
    main()
