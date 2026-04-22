# LLMWiki

基于 `workflow.md` 的可运行项目骨架，用于论文发现、原文入库、知识编译、可视化讨论与迭代回写。

## 目录

```text
raw/                # 原始资料，只增不改
  papers/
  clips/
wiki/               # 结构化知识库
  papers/
  concepts/
  gaps/
shared/
  research.md       # 多模型协作上下文
scripts/            # 自动化脚本
prompts/            # 提示词模板
```

## 快速开始

1. 将论文 Markdown 放入 `raw/papers/`。
2. 运行编译脚本生成 `wiki/papers/` 条目：
   ```bash
   python3 scripts/compile_wiki.py
   ```
3. 运行质量检查：
   ```bash
   python3 scripts/lint_wiki.py
   ```
4. 复制 `prompts/chatgpt_visualization_prompt.md` 到 ChatGPT，粘贴 `wiki/` 内容生成图谱与研究空白。

## 约定

- `raw/` 目录内容不覆盖历史文件。
- `wiki/` 是可持续演进的知识库。
- `shared/research.md` 用于 Claude/Gemini/Codex 协作讨论。
