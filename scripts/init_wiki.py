#!/usr/bin/env python3
"""Initialize repository structure and seed wiki files."""

from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIRECTORIES = [
    "raw/papers",
    "raw/notes",
    "raw/assets",
    "wiki/papers",
    "wiki/concepts",
    "wiki/entities",
    "wiki/comparisons",
    "wiki/gaps",
    "wiki/synthesis",
    "shared",
    "prompts",
]

SEED_FILES = {
    "wiki/index.md": "# Wiki Index\n\n- papers/\n- concepts/\n- entities/\n- comparisons/\n- gaps/\n- synthesis/\n",
    "wiki/overview.md": "# Overview\n\n- 研究方向：\n- 当前主线：\n- 最近更新：\n",
    "wiki/log.md": f"# Operation Log (append-only)\n\n- {date.today().isoformat()}: init wiki structure\n",
    "wiki/gaps/confirmed-gaps.md": "# Confirmed Gaps\n\n- \n",
    "wiki/gaps/hypotheses.md": "# Hypotheses\n\n- [draft] \n",
    "wiki/gaps/questions.md": "# Open Questions\n\n- \n",
    "wiki/synthesis/field-map.md": "# Field Map\n\n- 主线方法：\n- 关键分支：\n",
    "wiki/synthesis/shared-assumptions.md": "# Shared Assumptions\n\n- \n",
}


def main() -> None:
    for rel in DIRECTORIES:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0

    for rel, content in SEED_FILES.items():
        file = ROOT / rel
        if file.exists():
            skipped += 1
            continue
        file.write_text(content, encoding="utf-8")
        created += 1

    print(f"init done: created_files={created}, skipped_existing={skipped}")


if __name__ == "__main__":
    main()
