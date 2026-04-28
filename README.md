# LLMWiki项目使用说明
Semantic Scholar寻找文献使用说明见第三节、LLMWiki使用说明见第四节。

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
├── discovery/            ← 自动文献发现层（基于Semantic Scholar API实现），脚本写入，供人工筛选和后续 ingest
│   ├── inbox.csv         ← A/B 级候选论文入口，后续下载 PDF 或写入 wiki
│   │
│   └── semantic_scholar/ ← Semantic Scholar 发现工作区
│       ├── queries.txt                 ← 关键词搜索列表
│       ├── seed_papers.csv             ← 种子论文列表
│       ├── tracked_authors.csv         ← 追踪作者列表
│       ├── semantic_cache.sqlite       ← 跨周去重和论文缓存
│       ├── semantic_weekly_[run].csv   ← 每次运行生成的发现结果 CSV
│       └── semantic_weekly_[run].md    ← 每次运行生成的 Markdown 周报
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


## 三、Semantic Scholar 文献发现

新增脚本：`scripts/s2_discovery.py`，用于从 Semantic Scholar 批量发现与你研究方向相关的新论文，并把结果整理到本地 CSV、SQLite 缓存和 Markdown 周报中。

它支持 5 类发现来源：

- 关键词搜索
- 种子论文的被引论文追踪
- 种子论文的参考文献追踪
- 指定作者的新论文追踪
- 基于种子论文的推荐论文收集

### 1. 依赖与前置条件

脚本依赖：

```bash
pip install pandas requests pyyaml
```

你还需要一个 Semantic Scholar API Key（使用教育邮箱申请，免得获取），并在运行前设置环境变量 `S2_API_KEY`。

Linux / macOS:

```bash
export S2_API_KEY="your_api_key"
```

Windows PowerShell:

```powershell
$env:S2_API_KEY="your_api_key"
```

如果没有设置 `S2_API_KEY`，脚本会直接退出。

### 2. 相关文件

- `discovery/inbox.csv`
- `discovery/semantic_scholar/config.yaml`
- `discovery/semantic_scholar/queries.txt`
- `discovery/semantic_scholar/seed_papers.csv`
- `discovery/semantic_scholar/tracked_authors.csv`
- `discovery/semantic_scholar/semantic_cache.sqlite`
- `discovery/semantic_scholar/semantic_weekly.csv`
- `discovery/semantic_scholar/semantic_weekly.md`

脚本启动时会自动初始化这些目录和文件。不存在时会自动创建，不需要手动建目录。

### 3. 配置文件说明

配置文件路径：`discovery/semantic_scholar/config.yaml`

当前配置项包括：

- `semantic_scholar.base_url`：API 地址，默认即可。
- `semantic_scholar.request_interval_seconds`：请求间隔，避免触发限流。
- `semantic_scholar.max_retries`：失败后的最大重试次数。
- `semantic_scholar.timeout_seconds`：单次请求超时时间。
- `search.limit_per_query`：每个关键词最多取多少条结果。
- `search.min_year`：关键词搜索时保留的最小年份。
- `citation_tracking.max_citations_per_seed`：每篇种子论文最多追踪多少篇被引论文。
- `reference_tracking.max_references_per_seed`：每篇种子论文最多追踪多少篇参考文献。
- `recommendation.max_recommendations_per_seed`：每篇种子论文最多取多少篇推荐论文。
- `author_tracking.min_year`：作者追踪时保留的最小年份。
- `author_tracking.max_papers_per_author`：每个作者最多抓取多少篇论文。

### 4. 输入文件格式

#### 4.1 `queries.txt`

按行填写检索词，一行一个 query，例如：

```text
structured illumination microscopy
SIM reconstruction
multimodal large language model microscopy
scientific image understanding
```

脚本会对每一行分别调用 Semantic Scholar 搜索接口。

#### 4.2 `seed_papers.csv`

列头格式：

```csv
title,doi,arxiv_id,s2_paper_id,topic,priority,note
```

字段说明：

- `title`：论文标题，可用于补全匹配。
- `doi`：DOI，推荐填写。
- `arxiv_id`：arXiv 编号。
- `s2_paper_id`：Semantic Scholar 的 paperId。
- `topic`：该论文所属主题，便于后续筛选。
- `priority`：通常填 `A` 或 `B`。脚本会优先追踪 A/B 级种子。
- `note`：备注。

建议至少填写 `doi`、`arxiv_id`、`s2_paper_id` 中的一个，否则很难稳定追踪。

#### 4.3 `tracked_authors.csv`

列头格式：

```csv
name,s2_author_id,affiliation,topic,note
```

字段说明：

- `name`：作者姓名。
- `s2_author_id`：Semantic Scholar authorId。若为空，脚本会先按姓名搜索并自动补全。
- `affiliation`：作者单位，可选。
- `topic`：追踪主题，可选。
- `note`：备注。

### 5. 使用说明

脚本入口：

```bash
python scripts/s2_discovery.py <command>
```

支持的命令如下。

#### 5.1 `search`

```bash
python scripts/s2_discovery.py search
```

作用：

- 读取 `queries.txt`
- 对每个 query 执行论文搜索
- 根据 `search.min_year` 过滤较早论文
- 将结果写入本地缓存
- 将结果追加到周报 CSV
- 将 A/B 级论文写入 `discovery/inbox.csv`

适用场景：

- 你先想按关键词大范围拉一批新论文。

#### 5.2 `enrich-seeds`

```bash
python scripts/s2_discovery.py enrich-seeds
```

作用：

- 读取 `seed_papers.csv`
- 根据已有的 `s2_paper_id`、`doi` 或 `arxiv_id` 批量补全种子论文信息
- 回写 `seed_papers.csv`

适用场景：

- 你刚手工填完种子论文，想先把 `s2_paper_id` 和基础元数据补齐。

#### 5.3 `citations`

```bash
python scripts/s2_discovery.py citations
```

作用：

- 遍历种子论文
- 拉取引用这些种子论文的后续论文
- 写入缓存、周报和收件箱

适用场景：

- 你想知道最近谁在延续、应用或挑战你的核心种子论文。

#### 5.4 `references`

```bash
python scripts/s2_discovery.py references
```

作用：

- 遍历种子论文
- 拉取这些种子论文引用过的参考文献
- 写入缓存、周报和收件箱

适用场景：

- 你想向前追溯知识源头，补文献谱系。

#### 5.5 `authors`

```bash
python scripts/s2_discovery.py authors
```

作用：

- 读取 `tracked_authors.csv`
- 自动识别或使用现成的 `s2_author_id`
- 拉取这些作者近年的论文
- 写入缓存、周报和收件箱

适用场景：

- 你已经明确想长期跟踪几个课题组或作者。

#### 5.6 `recommend`

```bash
python scripts/s2_discovery.py recommend
```

作用：

- 基于种子论文调用 Semantic Scholar 推荐接口
- 收集推荐论文
- 写入缓存、周报和收件箱

适用场景：

- 你希望从相似论文中快速扩展阅读池。

#### 5.7 `weekly`

```bash
python scripts/s2_discovery.py weekly
```

作用：

- 先补全种子论文
- 再执行 `search`
- 再执行 `citations`
- 再执行 `references`
- 再执行 `authors`
- 再执行 `recommend`
- 最后统一生成本周 Markdown 周报

适用场景：

- 每周例行跑一次完整发现流程。

如果你只想执行一次完整任务，通常直接跑 `weekly` 即可。

### 6. 评分与筛选逻辑

脚本会为每篇论文打分，并标记为 `A`、`B`、`C`：

- `A`：高优先级，优先下载和精读
- `B`：中优先级，建议人工复核
- `C`：低优先级，保留记录但不进入收件箱

当前打分会综合考虑：

- 标题是否命中 SIM / microscopy super-resolution 等关键词
- 摘要是否包含 reconstruction、super-resolution、inverse problem、physics-informed 等信号
- 是否提到 multimodal、VLM、LLM、foundation model
- 是否为近两年论文
- 是否提供开放 PDF
- 引用数是否较高
- 是否来自 citation / recommendation 这类高价值来源
- 是否存在明显不相关倾向，例如纯临床诊断、纯生物实验、非重建类 survey

`A/B` 级论文会被追加到 `discovery/inbox.csv`，供你后续下载 PDF、送入解析链路或人工筛选。

### 7. 输出结果说明

#### 7.1 `discovery/inbox.csv`

这是后续处理入口，只保留 `A/B` 级论文。典型字段包括：

- `source`：来源，如 `semantic_search`、`semantic_citation`
- `topic`：所属主题
- `score`：数值评分
- `priority`：继承自种子或默认优先级
- `title`
- `year`
- `venue`
- `authors`
- `doi`
- `arxiv_id`
- `s2_paper_id`
- `url`
- `open_access_pdf`
- `abstract`
- `reason`：打分原因
- `discovered_at`
- `next_action`

#### 7.2 `semantic_weekly.csv`

保存本轮发现结果的明细，包含 `grade` 列，比 `inbox.csv` 更完整。

#### 7.3 `semantic_weekly.md`

自动生成 Markdown 周报，内容包括：

- 本周各来源新增数量
- A 级论文列表
- B 级论文列表
- 新的引用论文
- 推荐论文
- 作者更新
- 后续待办

#### 7.4 `semantic_cache.sqlite`

本地缓存库，用于去重和信息补全。脚本会优先根据以下标识判断是否已存在：

- `paperId`
- `doi`
- `arxiv_id`

这能减少重复写入和重复追踪。

### 8. 推荐使用流程

第一次使用，建议按下面顺序：

1. 配置 `S2_API_KEY`
2. 填写 `queries.txt`
3. 填写 `seed_papers.csv`
4. 填写 `tracked_authors.csv`
5. 运行 `python scripts/s2_discovery.py enrich-seeds`
6. 运行 `python scripts/s2_discovery.py weekly`
7. 查看 `discovery/inbox.csv` 和 `discovery/semantic_scholar/semantic_weekly.md`

如果你只是先测试关键词搜索，可以只运行：

```bash
python scripts/s2_discovery.py search
```

如果你已经维护了一批高质量种子论文，推荐直接每周运行：

```bash
python scripts/s2_discovery.py weekly
```

### 9. 一个最小示例

PowerShell 下：

```powershell
$env:S2_API_KEY="your_api_key"
python scripts/s2_discovery.py enrich-seeds
python scripts/s2_discovery.py weekly
```

bash 下：

```bash
export S2_API_KEY="your_api_key"
python scripts/s2_discovery.py enrich-seeds
python scripts/s2_discovery.py weekly
```

跑完后，优先检查：

- `discovery/inbox.csv`
- `discovery/semantic_scholar/semantic_weekly.md`

### 10. 常见问题

`1)` 为什么 `seed_papers.csv` 明明有标题，还是追踪不到？

因为真正稳定的主键是 `s2_paper_id`、`doi`、`arxiv_id`。只靠标题匹配，命中率和稳定性都一般。实践上至少填一个唯一标识。

`2)` 为什么 `inbox.csv` 里没有所有结果？

因为只有 `A/B` 级论文会进入 `inbox.csv`。全部结果会保存在 `semantic_weekly.csv`。

`3)` 为什么 `weekly` 比单独运行某个命令慢？

因为它串行执行整套发现流程，还会生成周报。

`4)` 可以只跑某一类发现吗？

可以，直接用对应子命令，例如 `search`、`citations`、`authors`。

## 四、Prompt（LLM Wiki使用说明）

### 0. PDF 转 Markdown 准备

在使用下面的 Ingest 提示词前，先将目标论文 PDF 转换为 Markdown，并把生成的 `.md` 文件放入 `raw/papers/`。

推荐使用 `marker` 做高准确度 PDF 转 Markdown：

```powershell
# Python < 3.10
pip install marker-pdf==0.2.15

# Python >= 3.10
pip install marker-pdf==0.2.17
```

使用流程：

1. 将 PDF 放入 `raw/pdfs/`。
2. 在 `raw/` 目录下运行：

```powershell
marker .\pdfs --output_dir .\papers
```

本项目也提供一个简易备用脚本：`scripts/pdf_to_md.py`。如果不使用 `marker`，可以将 PDF 放入 `raw/papers/`，然后在项目根目录运行：

```powershell
python scripts/pdf_to_md.py
```

转换完成后，确认目标论文对应的 `.md` 文件已经位于 `raw/papers/`，再进入后续 Ingest 流程。

### 1 Ingest 提示词（处理新论文）

```text
处理论文：raw/papers/2401.xxxxx.md
先读一遍，然后告诉我：
1. 这篇论文的核心 claim 是什么？（一句话）
2. 它假设了什么在我的领域里大家都没有质疑过的东西？
3. 有没有和 wiki/ 里已有内容矛盾的地方？
讨论完之后，按 CLAUDE.md 的格式写入 wiki/，
重点把"Gap 线索"这一栏写得具体，不要客套。
```

### 2 领域全景讨论提示词

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

### 3 Idea 生成提示词

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

### 4 Lint 提示词（每 1-2 周一次）

```text
我们现在进入 Research Wiki 健康检查模式。

请先读取并交叉检查：
- wiki/index.md
- wiki/overview.md
- wiki/synthesis/field-map.md
- wiki/synthesis/shared-assumptions.md
- wiki/gaps/confirmed-gaps.md
- wiki/gaps/questions.md
- wiki/gaps/hypotheses.md
- wiki/papers/ 下最近入库或最近更新的论文页面
- wiki/concepts/ 下已有概念页面
- discovery/inbox.csv 和最新的 discovery/semantic_scholar/semantic_weekly_[run].md（如存在）

任务：
1. 找出在 3 篇以上论文中反复出现、但还没有独立 wiki/concepts/ 页面的方法、假设、数据集、评价指标或问题类型。
   对每个候选概念说明：出现在哪些论文页面中、为什么值得单独建页、建议页面名是什么。

2. 检查 wiki/gaps/hypotheses.md 中 status: draft 的假设。
   判断最近入库论文是否提供了支持证据、反例、边界条件或需要改写的地方。
   不要直接把 draft 改成 confirmed/rejected，除非证据非常直接；优先给出“建议状态”和理由。

3. 检查 wiki/overview.md 和 wiki/synthesis/field-map.md。
   找出是否有被最近论文削弱、推翻、需要加限定条件，或已经过时的声明。
   每条都必须指出原声明位置、相关新证据、建议修订方向。

4. 找出论文页面之间、概念页面之间、或论文与 synthesis 页面之间的矛盾。
   矛盾可以是：实验结论不一致、隐含假设冲突、适用场景冲突、评价指标不可比、同一术语定义不同。
   不要强行调和；冲突观点单独列为“待验证”。

约束：
- 不要编造引用；只能基于已读取的 wiki/、discovery/ 内容。
- 每个判断都标注来源文件路径。
- 区分“直接证据”“间接证据”“推测”。
- 不要直接修改 wiki；先生成报告，等我确认后再写回。
- 如果信息不足，明确写“证据不足”，不要补全想象。

报告格式：

需要创建的新概念页面
| 建议页面 | 类型 | 出现位置 | 建页理由 | 优先级 |

假设状态更新
| 假设 | 当前状态 | 新证据/反例 | 建议状态 | 理由 |

需要修订的声明
| 文件 | 原声明 | 新证据 | 风险 | 建议修订 |

检测到的矛盾
| 冲突点 | 来源 A | 来源 B | 冲突类型 | 待验证问题 |

## 建议写回动作
- 建议新增的 concepts 页面：
- 建议更新的 gaps/hypotheses 条目：
- 建议更新的 synthesis/overview 或 field-map 条目：
- 暂不建议写回、需要继续查证的点：
```

### 5 多模型辩论触发提示词（配合 shared research.md 三端共享上下文，每 1-2 周一次）
（在LLM项目文件夹下打开Claudecode，完成1后关闭powershell。重新在LLM文件夹下打开Gemini Cli，完成2后关闭powershell，依次重复。）
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

### 6 可视化提示词
将wiki\synthesis\目录下的visualization-x.md文件中的mermaid信息复制到mermaid在线生成网站进行可视化。
```text
请读取 prompts/chatgpt_visualization_prompt.md，并按其中规则分析 wiki/ 下的内容。重点读取 wiki/index.md、wiki/overview.md、wiki/synthesis/field-map.md、wiki/synthesis/shared-assumptions.md、wiki/gaps/confirmed-gaps.md、wiki/gaps/questions.md、wiki/gaps/hypotheses.md。只输出 Mermaid 图、Top-3 research gaps、结论-证据-风险表，先给出拟写入内容和目标文件，等待我确认，不要直接写入。
```

## 五、一个关键点：Query 的答案要写回 wiki

Karpathy 特别强调：好的答案可以作为新页面写回 wiki。一次对比分析、一个你发现的连接——这些很有价值，不应该消失在对话历史里。这样你的探索过程也在知识库里积累复利。

具体操作：每当你和 Claude 讨论出一个有价值的分析，在对话末尾加一句：  
标注 status: draft，记录今天的日期和讨论要点。

对 wiki/ 做健康检查时，使用上面的 `3.4 Lint 提示词（每 1-2 周一次）`。先生成报告，不要直接写回；等人工确认后，再把需要保留的结论写入 `wiki/concepts/`、`wiki/gaps/` 或 `wiki/synthesis/`。
