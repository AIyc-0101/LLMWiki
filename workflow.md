# LLM Wiki 研究工作流（将第 4 步改为 ChatGPT 可视化层）

> 目标：按图搭建一条“发现论文 → 入库 → 主动编译 → 可视化讨论 → 多模型协作 → 回写迭代”的闭环流程。

## 0. 目录约定

```text
project/
  raw/                 # 原始资料（只增不改）
    papers/
    clips/
  wiki/                # 结构化知识库（可被持续改写）
    papers/
    concepts/
    gaps/
  shared/
    research.md        # 多模型共享上下文
```

---

## 1) 论文发现（arXiv + Semantic Scholar）

### 输入源
- **arXiv**：RSS、邮件订阅、API、arxiv-sanity-lite
- **Semantic Scholar**：TLDR 摘要、引用追踪、Alert
- 可选补充：Connected Papers（从种子论文扩展引用图）

### 产出
- 候选论文清单（含标题、链接、标签、优先级）

---

## 2) 入库到 `raw/`（只增不改）

### 推荐方式
- PDF→Markdown：MinerU / Marker
- 网页资料：Web Clipper（保存到 `raw/clips/`）

### 规则
- 不覆盖历史原文
- 统一命名：`YYYY-MM-DD_short-title.md`
- 保留公式（LaTeX）与图表（HTML/图片）

---

## 3) LLM Wiki 核心编译（主动写知识，不是被动检索）

从 `raw/` 读取，持续生成/更新 `wiki/`：

- 论文摘要（paper-level）
- 概念文章（跨论文综述）
- 反向链接（backlink）
- 研究空白（gaps）

### 建议执行循环
1. 扫描 `raw/` 新增文件
2. 生成结构化条目写入 `wiki/`
3. 跑 Lint（矛盾检测、缺引用检测、断链检测）
4. 将发现写入 `wiki/gaps/`

---

## 4) ChatGPT 可视化层（替代 Obsidian，可读不直接写库）

> 你提出的改动：将“Obsidian 可视化层”替换为“ChatGPT 可视化层”。

### 定位
- **读取** `wiki/`（和必要时 `raw/`）
- **不直接写入** 主知识库
- 输出可复制的图谱/逻辑结构，供第 5 步协作确认后再回写

### 在 ChatGPT 中可做的可视化产物
1. **关系图（文本图）**
   - 让 ChatGPT 输出 Mermaid：`graph TD` / `mindmap`
2. **研究路线图**
   - 时间线、优先级、依赖关系
3. **概念对照表**
   - 模型A vs 模型B、方法优缺点、适用场景
4. **证据链表格**
   - 结论 → 证据论文 → 置信度 → 争议点

### 推荐提示词模板

```text
你是我的 research 可视化助手。
请基于我提供的 wiki 内容：
1) 画一份 Mermaid 概念关系图；
2) 给出 3 条最值得推进的 research gap；
3) 输出“结论-证据-风险”三列表。
要求：
- 不编造引用；
- 每个结论都标注来源条目；
- 对冲突观点单独列“待验证”。
```

---

## 5) 多模型协作讨论（共享 `shared/research.md`）

角色建议：
- **Claude Code**：整合、对齐 wiki、给出仲裁版
- **Gemini CLI**：联网核验、补充最新论文
- **Codex CLI**：找漏洞、找反例、补边界条件

产出统一写到 `shared/research.md`，形成可审阅版本。

---

## 6) 输出与下一轮迭代

1. 人工确认 `shared/research.md`
2. 通过编译流程回写 `wiki/`（新增条目、更新 gaps）
3. 更新知识图谱
4. 触发下一轮论文发现与编译

---

## 最小可运行 SOP（每周）

1. 收集 5–10 篇新论文到 `raw/`
2. 运行第 3 步编译并更新 `wiki/`
3. 用 ChatGPT 生成关系图 + gap 优先级
4. 三模型协作辩论并沉淀到 `shared/research.md`
5. 回写并记录本周新增知识点与待验证项

这个版本等价于你图中的主流程，唯一结构性改动是：
**第 4 步由 Obsidian 可视化层改为 ChatGPT 可视化层。**
