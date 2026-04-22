#!/usr/bin/env python3
"""Lint checks aligned with the optimized workflow."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
PAPERS = WIKI / "papers"
SYNTHESIS = WIKI / "synthesis"
GAPS = WIKI / "gaps"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def check_required_files() -> list[str]:
    required = [
        WIKI / "index.md",
        WIKI / "log.md",
        WIKI / "overview.md",
        GAPS / "confirmed-gaps.md",
        GAPS / "hypotheses.md",
        GAPS / "questions.md",
        SYNTHESIS / "field-map.md",
        SYNTHESIS / "shared-assumptions.md",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    return missing


def check_hypothesis_status() -> list[str]:
    text = read(GAPS / "hypotheses.md")
    warnings = []
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("-") and "[" not in line:
            warnings.append(f"wiki/gaps/hypotheses.md:{i} missing [status]")
    return warnings


def check_orphan_papers() -> list[str]:
    index_text = read(WIKI / "index.md")
    linked = set(re.findall(r"papers/([^\s)]+\.md)", index_text))
    warnings = []
    for file in PAPERS.glob("*.md"):
        if file.name not in linked:
            warnings.append(f"orphan paper: wiki/papers/{file.name}")
    return warnings


def check_conflicting_claims() -> list[str]:
    """Heuristic: if both '支持' and '不支持' appear in same paper page, flag for review."""
    warnings = []
    for file in PAPERS.glob("*.md"):
        text = read(file)
        if "支持" in text and "不支持" in text:
            warnings.append(f"possible conflict in {file.relative_to(ROOT)}")
    return warnings


def main() -> None:
    failures = 0
    warnings = []

    missing = check_required_files()
    if missing:
        failures += len(missing)
        for item in missing:
            print(f"[FAIL] missing required file: {item}")

    warnings.extend(check_hypothesis_status())
    warnings.extend(check_orphan_papers())
    warnings.extend(check_conflicting_claims())

    for item in warnings:
        print(f"[WARN] {item}")

    if failures:
        raise SystemExit(1)

    print(f"lint passed with {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
