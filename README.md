# LLMWiki

按照最新流程图优化后的研究工程：
- `raw/` 只增不改（论文、笔记、素材）
- `wiki/` 是持续演化的知识层
- Query 的高价值答案必须回写 `wiki/synthesis/`

## 目录结构

```text
your-research-wiki/
├── CLAUDE.md
├── raw/
│   ├── papers/
│   ├── notes/
│   └── assets/
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── overview.md
│   ├── papers/
│   ├── concepts/
│   ├── entities/
│   ├── comparisons/
│   ├── gaps/
│   └── synthesis/
├── prompts/
└── shared/
```

## 快速开始

```bash
python3 scripts/init_wiki.py
python3 scripts/compile_wiki.py
python3 scripts/lint_wiki.py
```

然后：
1. 把新论文放到 `raw/papers/`
2. 运行编译脚本生成 `wiki/papers/` 草稿
3. 用 `prompts/` 中的 Ingest / 讨论 / Idea / Lint 提示词驱动迭代
4. 将 Query 结论写入 `wiki/synthesis/discussion-YYYY-MM-DD.md`

## 核心原则

- `raw/` 只读，`wiki/` 可持续更新。
- `wiki/log.md` 必须 append-only。
- `wiki/gaps/` 与 `wiki/synthesis/` 是创新密度最高的目录。
