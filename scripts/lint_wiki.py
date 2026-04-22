#!/usr/bin/env python3
"""Simple lint checks for wiki papers."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI_PAPERS = ROOT / "wiki" / "papers"


def check_required_sections(text: str, required: list[str]) -> list[str]:
    missing = []
    for section in required:
        if section not in text:
            missing.append(section)
    return missing


def main() -> None:
    required = [
        "## Metadata",
        "## TL;DR",
        "## Key Ideas",
        "## Method",
        "## Results",
        "## Limitations",
        "## Open Questions / Gaps",
    ]

    errors = 0
    files = sorted(WIKI_PAPERS.glob("*.md"))

    if not files:
        print("lint warning: no wiki papers found")
        return

    for file in files:
        text = file.read_text(encoding="utf-8", errors="ignore")
        missing = check_required_sections(text, required)
        if missing:
            errors += 1
            print(f"[FAIL] {file.relative_to(ROOT)} missing: {', '.join(missing)}")
        else:
            print(f"[PASS] {file.relative_to(ROOT)}")

    if errors:
        raise SystemExit(1)

    print("lint passed")


if __name__ == "__main__":
    main()
