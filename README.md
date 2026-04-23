# LLMWiki 使用说明

此版本仅针对“积累科研领域经验 + 和 LLM 协作讨论 idea”这个需求设计。

## 一、目录结构设计

wiki 是 LLM 完全拥有的层，你读它，LLM 写它。好的问答结果本身也应该写回 wiki，成为新的页面，这样你的探索过程也在知识库里积累复利。@Karpathy

参考目录结构是：sources/（论文摘要）、entities/（作者、数据集、系统）、concepts/（方法、理论）、syntheses/（跨论文综合）、comparisons/（方法对比）、questions/（研究问题），通过 wikilinks 互联。

具体结构如下：  
gaps/ 和 synthesis/ 这两个目录是你的需求相比 Karpathy 通用场景最大的扩展，也是 idea 生成的核心积累地。

```text
your-research-wiki/
│
├── CLAUDE.md             ← 最重要的文件，schema 和操作规范
│
├── raw/                  ← 只增不改，LLM 读取但不写入
│   ├── papers/           ← MinerU 转换的 PDF → .md
│   ├── notes/            ← 你自己的笔记、arXiv 页面 clip
│   └── assets/           ← 图片、图表（本地存储）
│
└── wiki/                 ← LLM 写，你读
    ├── index.md          ← 所有页面目录（标题 + 一句话摘要）
    ├── log.md            ← 操作日志（append-only，可 grep）
    ├── overview.md       ← 领域全景综述（持续更新）
    │
    ├── papers/           ← 每篇论文一个页面
    │   └── [arxiv-id]-[short-title].md
    │
    ├── concepts/         ← 每个方法/理论一个页面（跨论文综合）
    │   └── [method-name].md
    │
    ├── entities/         ← 作者组、数据集、系统、benchmark
    │   └── [name].md
    │
    ├── comparisons/      ← 方法对比表（你问的答案直接写回这里）
    │   └── [topic]-comparison.md
    │
    ├── gaps/             ← ★ 核心：研究空白和假设
    │   ├── confirmed-gaps.md   ← 已验证的研究空白
    │   ├── hypotheses.md       ← 创新假设（含状态：draft/testing/rejected）
    │   └── questions.md        ← 待探索的开放问题
    │
    └── synthesis/        ← ★ 核心：你的综合理解
        ├── field-map.md          ← 该领域的方法谱系和演化逻辑
        ├── shared-assumptions.md ← 所有论文共同的隐含假设
        └── discussion-[date].md  ← 每轮多模型讨论的结论（写回）
```

## 二、CLAUDE.md 模板（学术研究版）

CLAUDE.md 是整个系统最重要的文件，它把一个通用 LLM 变成一个有纪律的知识工作者，编码了：域内哪些实体和关系存在、何时创建新页面 vs 更新已有页面、哪些内容是私有的。

以下是针对科研场景的完整 CLAUDE.md 模板：

```markdown
# Research Wiki Schema

## 你的身份
你是这个研究知识库的唯一维护者。
你的目标：将 raw/ 中的论文积累成有结构的知识，帮助发现研究空白和创新方向。
你写 wiki/，用户读 wiki/。用户提供原材料和方向判断，你做所有整理工作。

## 目录约定
- raw/papers/ → 原始论文 Markdown，只读
- wiki/papers/ → 论文摘要页，你写
- wiki/concepts/ → 方法/理论概念页，跨论文综合
- wiki/entities/ → 作者组、数据集、benchmark
- wiki/comparisons/ → 对比表（对比类问题的答案直接存这里）
- wiki/gaps/ → 研究空白、假设、开放问题
- wiki/synthesis/ → 领域综合理解，定期更新
- wiki/index.md → 所有页面目录，每次操作后更新
- wiki/log.md → 操作日志，append-only

## 论文摘要页格式（wiki/papers/）
---
paper_id: [arXiv ID]
title:
authors:
year:
venue:
status: [read/skimmed/queued]
confidence: [high/medium/low] # 根据我读得多仔细
tags: []
---

## 一句话贡献
[用一句话说清这篇论文的核心贡献]

## 问题设定
[这篇论文要解决什么问题？为什么之前的方法不够好？]

## 方法核心
[用自己的话解释关键方法，公式用 LaTeX，重点不是复述而是理解]

## 实验结论
[关键数值结果，和 baseline 的对比]

## 局限性和假设
[论文自己承认的局限 + 你识别到的隐含假设]

## 与已有工作的关系
- 建立在: [[concept-name]], [[paper-id]]
- 被引用: （lint 时填写）
- 矛盾: （如有，显式标注）

## Gap 线索
[这篇论文暗示但没做的方向，直接写，哪怕粗糙]

## 操作
**Ingest（处理新论文）：**
1. 读取 raw/papers/[id].md
2. 和用户讨论 2-3 个关键 takeaway
3. 写 wiki/papers/[id].md
4. 更新相关 wiki/concepts/ 页面（引用新证据、更新理解）
5. 如有矛盾，在两个页面都标注
6. 更新 wiki/gaps/questions.md（如发现新问题）
7. 更新 wiki/index.md 和 wiki/log.md

**Query（问答）：**
- 先读 wiki/index.md 找相关页面
- 答案如有价值，主动问用户是否写入 wiki
- 对比类问题 → 写入 wiki/comparisons/
- 综合分析 → 写入 wiki/synthesis/

**Lint（健康检查）：**
检查并报告：
- 孤儿页面（没有入链）
- 矛盾（显式标注冲突论文/概念）
- 过时声明（被新论文否定的结论）
- 缺少独立页面的高频概念（出现 3+ 次但没有 concepts/ 页面）
- wiki/gaps/questions.md 中的开放问题是否有新论文可以回答

**Idea 生成（讨论模式）：**
当用户要求讨论创新方向时：
1. 读取 wiki/synthesis/shared-assumptions.md
2. 从 wiki/gaps/confirmed-gaps.md 选取 2-3 个方向
3. 提出假设，说明：前提条件 / 若成立的影响 / 已有的间接证据
4. 主动挑战自己：这个假设哪里最弱？有哪篇论文是反例？
5. 结论写入 wiki/gaps/hypotheses.md，标注状态为 draft

## Frontmatter 约定
confidence: high（有直接实验支持）/ medium（间接证据）/ low（推测）
status（论文）: read / skimmed / queued
status（假设）: draft / testing / confirmed / rejected
```

## 三、Prompt（使用说明）

### 3.1 Ingest 提示词（处理新论文）

```text
处理论文：raw/papers/2401.xxxxx.md
先读一遍，然后告诉我：
1. 这篇论文的核心 claim 是什么？（一句话）
2. 它假设了什么在我的领域里大家都没有质疑过的东西？
3. 有没有和 wiki/ 里已有内容矛盾的地方？
讨论完之后，按 CLAUDE.md 的格式写入 wiki/，
重点把"Gap 线索"这一栏写得具体，不要客套。
```

### 3.2 领域全景讨论提示词

```text
现在我要和你讨论 [你的研究方向] 的现状。
请读取：
- wiki/overview.md
- wiki/synthesis/field-map.md
- wiki/synthesis/shared-assumptions.md

然后告诉我：
1. 按照 wiki 里记录的内容，这个领域目前主流的方法谱系是什么？
   用"问题 → 主流解法 → 代表论文"的格式整理
2. 所有这些方法共享什么隐含假设？
   哪个假设是最脆弱的，但很少有论文去质疑它？
3. 最近入库的 3 篇论文里有没有暗示某种范式转变？

回答结束后问我：要不要把这次讨论的结论写进 wiki/synthesis/？
```

### 3.3 Idea 生成提示词

```text
我们现在进入创新点讨论模式。
背景：读取 wiki/gaps/confirmed-gaps.md 和 wiki/gaps/questions.md
任务：
围绕 [你指定的一个具体方向/问题]，提出 3 个研究假设。

对每个假设，你必须：
① 说清楚它和哪些已有工作的区别（引用 wiki 里的具体论文）
② 说清楚最强的反对理由是什么，哪篇论文可能是反例
③ 如果这个假设成立，最小的可验证实验是什么？

你不需要讨好我。如果某个想法很普通，直接说。
如果有比我问的方向更有价值的空白，告诉我。
讨论后，把达成共识的假设写入 wiki/gaps/hypotheses.md，
```

### 3.4 Lint 提示词（每 1-2 周一次）
### 3.5 多模型辩论触发提示词（配合 shared research.md）

## 四、一个关键点：Query 的答案要写回 wiki

Karpathy 特别强调：好的答案可以作为新页面写回 wiki。一次对比分析、一个你发现的连接——这些很有价值，不应该消失在对话历史里。这样你的探索过程也在知识库里积累复利。

具体操作：每当你和 Claude 讨论出一个有价值的分析，在对话末尾加一句：  
标注 status: draft，记录今天的日期和讨论要点。

对 wiki/ 做一次健康检查。  
检查并生成报告：

1. 有哪些概念在 3 篇以上论文里出现但没有独立的 concepts/ 页面？
2. 哪些 hypotheses.md 里的 draft 假设，在新入库的论文里找到了证据或反例？
3. overview.md 和 field-map.md 里有没有被最近论文推翻的结论？
4. 找出任何两个论文页面之间存在的矛盾（不同实验结论、不同假设），显式标注

报告格式：

```markdown
## 需要创建的新概念页面
## 假设状态更新
## 需要修订的声明
## 检测到的矛盾
```

[写入 shared research.md 的内容，三端都读这个文件]

```markdown
---
## 当前讨论轮次：[日期]
## 议题：[具体问题，例如：是否应该挑战 X 假设]
## wiki 相关摘录（Claude Code 从 wiki/ 提取）：
[从 wiki/gaps/confirmed-gaps.md 和 wiki/concepts/ 相关页面粘贴关键段落]

## 上轮结论摘要：
[上次讨论写回的结论]

## 本轮任务：
- Claude：综合 wiki 内容，给出综合判断
- Gemini：联网搜索是否有 2025 年后的最新论文支持或反驳上述分析
- Codex：挑最弱的假设，找已有论文里的反例
请各自回答，然后我来汇总写回 wiki/synthesis/discussion-[date].md
---
```

把这次分析的核心结论（200字以内）写入 `wiki/synthesis/discussion-[今天日期].md`，并更新 `wiki/log.md`。

这样知识库会越来越“懂”你的研究领域，而不是每次都从零开始。

## 多模型协作讨论（shared research.md 三端共享上下文）

### 1）Claude 首轮主持 prompt

```text
你是这个 Research Wiki 的主维护者。
请按以下流程工作：
1. 读取当前项目中的 raw/ 与 wiki/；
2. 围绕我给出的议题，总结已有结论、相关页面和当前不确定点；
3. 识别本轮最值得验证的 2-3 个问题；
4. 生成一份完整的 shared_research.md 草稿；
5. 其中“给 Gemini 的任务”只能是联网验证；
6. “给 Codex 的任务”只能是挑漏洞、找反例、给最小实验；
7. 不要现在下最终结论，只负责把讨论上下文准备好。

要求：
- 依据 wiki 内容，不要空泛；
- 相关页面尽量具体到 paper / concept / gap / synthesis 页面；
- 用中文输出；
- 输出结果直接采用 shared_research.md 格式。

本轮议题：
[写你的问题]
```

### 2）Gemini CLI 用的 prompt

```text
请读取当前目录下的 shared_research.md。

你的任务只有一件事：联网验证。
请不要重复已有 wiki 常识，也不要做最终仲裁。

具体要求：
1. 围绕“当前议题”和“本轮要验证的问题”，搜索最近 2-3 年相关论文；
2. 判断是否已有论文直接支持或反驳当前假设；
3. 补充最新方法、数据集、实验结果、趋势变化；
4. 尽量给出论文标题、年份、核心结论；
5. 结果写入 shared_research.md 的 “Gemini Findings” 部分；
6. 不要改动其他部分。

输出重点：
- 最新论文
- 支持证据
- 反驳证据
- 新趋势 / 范式变化
- Gemini 小结
```

### 3）Codex CLI 用的 prompt

```text
请读取当前目录下的 shared_research.md。

你的任务只有一件事：挑刺和找反例。
请不要重复 Gemini 的联网综述，也不要做最终仲裁。

具体要求：
1. 找出当前假设或议题中最薄弱的一环；
2. 从已有论文、已有方法或常见失败模式中寻找潜在反例；
3. 指出推理链、实验设计或工程实现上的漏洞；
4. 给出一个最小可验证实验；
5. 如果这个问题本身不够新颖或很普通，请直接指出；
6. 结果写入 shared_research.md 的 “Codex Findings” 部分；
7. 不要改动其他部分。

输出重点：
- 最薄弱环节
- 可能反例
- 推理漏洞
- 最小验证实验
- Codex 小结
```

### 4）Claude 最终汇总 prompt

```text
请读取 shared_research.md，并完成最终综合判断。

任务：
1. 综合 Claude Pre-Read、Gemini Findings、Codex Findings；
2. 明确哪些是共识，哪些仍有分歧；
3. 判断当前最可信的结论是什么；
4. 判断这轮讨论是否值得写回 wiki；
5. 给出建议写回的位置；
6. 生成可直接写入 wiki 的摘要。

要求：
- 不要简单重复 Gemini 和 Codex 的内容；
- 要做仲裁、取舍和归纳；
- 如果 Gemini 和 Codex 冲突，要明确指出冲突点；
- 如果证据不足，要直接说不足，不要硬下结论；
- 用中文输出。
```
