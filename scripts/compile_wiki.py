#!/usr/bin/env python3
"""Compile markdown files from raw/papers into wiki/papers stubs."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RAW_PAPERS = ROOT / "raw" / "papers"
WIKI_PAPERS = ROOT / "wiki" / "papers"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    return text.strip("-") or "untitled"


def first_heading(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return "Untitled Paper"


def build_stub(source_file: Path, title: str) -> str:
    today = date.today().isoformat()
    return f"""# {title}

## Metadata
- source: `{source_file.as_posix()}`
- imported_at: {today}
- status: draft

## TL;DR
- 

## Key Ideas
- 

## Method
- 

## Results
- 

## Limitations
- 

## Backlinks
- 

## Open Questions / Gaps
- 
"""


def main() -> None:
    RAW_PAPERS.mkdir(parents=True, exist_ok=True)
    WIKI_PAPERS.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for source in sorted(RAW_PAPERS.glob("*.md")):
        content = source.read_text(encoding="utf-8", errors="ignore")
        title = first_heading(content)
        out_name = f"{slugify(title)}.md"
        target = WIKI_PAPERS / out_name

        if target.exists():
            skipped += 1
            continue

        target.write_text(build_stub(source, title), encoding="utf-8")
        created += 1

    print(f"compile done: created={created}, skipped={skipped}")


if __name__ == "__main__":
    main()
