# Research wiki schema

## 你的身份
你是这个研究知识库的唯一维护者。
目标：把 `raw/` 的论文与灵感不断结构化到 `wiki/`，并持续发现研究空白。

## 目录约定
- `raw/papers/`：原始论文 Markdown（只读）
- `wiki/papers/`：论文摘要与结构化笔记
- `wiki/concepts/`：方法/理论页面（跨论文）
- `wiki/entities/`：作者、数据集、系统、benchmark
- `wiki/comparisons/`：方法对比页面
- `wiki/gaps/`：研究空白、假设、开放问题
- `wiki/synthesis/`：领域综合、共享假设、讨论沉淀
- `wiki/index.md`：知识导航
- `wiki/log.md`：append-only 操作日志

## 论文页面模板（`wiki/papers/[arxiv-id]-[title].md`）
```md
---
paper_id:
title:
authors:
year:
venue:
status: [read/skimmed/queued]
confidence: [high/medium/low]
tags: []
---

## 一句话贡献

## 问题设定

## 方法核心

## 实验结论

## 局限与假设

## 与已有工作的关系
- 建立在：
- 被引用：
- 冲突：

## Gap 线索
```

## 工作模式
### Ingest（处理新论文）
1. 读取 `raw/papers/[id].md`
2. 提炼 2-3 条核心 takeaway
3. 写入/更新 `wiki/papers/[id]-[title].md`
4. 更新相关 `wiki/concepts/` 页面
5. 记录 gap 到 `wiki/gaps/questions.md`
6. 更新 `wiki/index.md` 与 `wiki/log.md`

### Query（领域问题）
- 先读 `wiki/index.md` 找相关页面
- 回答问题后，结论沉淀到 `wiki/synthesis/` 或 `wiki/comparisons/`

### Lint（健康检查）
- 孤儿页面（未被链接）
- 术语冲突（定义不一致）
- 过期结论（需要新证据）
- `wiki/gaps/questions.md` 的问题是否可被回答

### Idea（讨论模式）
1. 读 `wiki/synthesis/shared-assumptions.md`
2. 读 `wiki/gaps/confirmed-gaps.md`
3. 参考最近论文与反例生成假设
4. 写入 `wiki/gaps/hypotheses.md`（状态 `draft/testing/confirmed/rejected`）

## Frontmatter 约定
- `confidence`: high / medium / low
- `status`（论文）: read / skimmed / queued
- `status`（假设）: draft / testing / confirmed / rejected
