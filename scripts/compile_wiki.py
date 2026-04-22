#!/usr/bin/env python3
"""Compile markdown files from raw/papers into wiki/papers stubs."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RAW_PAPERS = ROOT / "raw" / "papers"
WIKI_PAPERS = ROOT / "wiki" / "papers"
LOG_FILE = ROOT / "wiki" / "log.md"
INDEX_FILE = ROOT / "wiki" / "index.md"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    return text.strip("-") or "untitled"


def first_heading(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Untitled Paper"


def infer_paper_id(source: Path) -> str:
    stem = source.stem
    m = re.match(r"^([0-9]{4}\.[0-9]{4,5})", stem)
    if m:
        return m.group(1)
    return stem


def build_stub(source_file: Path, paper_id: str, title: str) -> str:
    today = date.today().isoformat()
    return f"""---
paper_id: {paper_id}
title: {title}
authors: []
year:
venue:
status: queued
confidence: medium
tags: []
source: {source_file.as_posix()}
imported_at: {today}
---

## 一句话贡献

## 问题设定

## 方法核心

## 实验结论

## 局限和假设

## 与已有工作的关系
- 建立在：
- 被引用：
- 冲突：

## Gap 线索
"""


def append_log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("# Operation Log (append-only)\n\n", encoding="utf-8")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"- {date.today().isoformat()}: {message}\n")


def refresh_index() -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    entries = sorted(WIKI_PAPERS.glob("*.md"))
    lines = ["# Wiki Index", "", "## papers", ""]
    for entry in entries:
        lines.append(f"- papers/{entry.name}")
    lines.append("")
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RAW_PAPERS.mkdir(parents=True, exist_ok=True)
    WIKI_PAPERS.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for source in sorted(RAW_PAPERS.glob("*.md")):
        content = source.read_text(encoding="utf-8", errors="ignore")
        title = first_heading(content)
        paper_id = infer_paper_id(source)
        target = WIKI_PAPERS / f"{paper_id}-{slugify(title)}.md"

        if target.exists():
            skipped += 1
            continue

        target.write_text(build_stub(source, paper_id, title), encoding="utf-8")
        created += 1

    refresh_index()
    append_log(f"compile_wiki created={created}, skipped={skipped}")
    print(f"compile done: created={created}, skipped={skipped}")


if __name__ == "__main__":
    main()
