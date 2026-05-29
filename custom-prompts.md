# Codex Custom Prompts 工作流

## 背景

LLMWiki 使用 Codex CLI 与 custom prompts 构建本地 AI research workflow。该 workflow 面向论文摄入、gap mining 与结构化 wiki 生成。

核心目标：

- 将 `raw/papers/*.md` 中的论文内容整理为可检索、可比较、可持续扩展的 wiki 条目。
- 在整理过程中显式提取论文的核心 claim、隐含假设、与现有 wiki 内容的冲突点。
- 将每篇论文沉淀到 `wiki/papers/*.md`，并遵循 `CLAUDE.md` 定义的输出格式。

## 工作流总览

```text
PDF
↓
MinerU/Marker
↓
raw/papers/*.md
↓
check raw
↓
ingest.txt
↓
queue
↓
ingest
↓
wiki/papers/*.md
↓
structured research wiki
```

## 工作流：ingest

`ingest` 用于处理 `raw/papers/*.md` 中的单篇论文 Markdown 文件。

### 使用方式

```sh
ingest "xxx.md"
```

### 行为定义

执行 `ingest "xxx.md"` 后，Codex 应先完整阅读目标论文，再进入讨论阶段。不要直接写入 wiki。

讨论阶段需要先回答：

1. 这篇论文的核心 claim 是什么？用一句话概括。
2. 它假设了什么在本领域中大家通常没有质疑过的东西？
3. 是否存在与 `wiki/` 中已有内容矛盾、张力或互相修正的地方？

讨论完成后，再按 `CLAUDE.md` 中定义的格式写入 `wiki/`。写入时应重点处理 `Gap 线索` 栏：

- 具体指出论文暴露出的未解决问题。
- 说明该 gap 来自方法限制、数据限制、理论假设、实验设置还是应用场景。
- 避免泛泛表述，例如“值得进一步研究”。
- 优先写成可继续追问、可检索、可转化为研究问题的短句。

### Prompt 模板

```text
先完整阅读 raw/papers/{file}。

在写入 wiki/ 之前，先回答以下问题：

1. 这篇论文的核心 claim 是什么？用一句话概括。
2. 它假设了什么在我的领域里大家通常没有质疑过的东西？
3. 是否与 wiki/ 中已有内容存在矛盾、修正关系或理论张力？

讨论完以上问题后，再按 CLAUDE.md 定义的格式写入 wiki/。

重点处理 "Gap 线索" 栏：
- 写得具体；
- 标明 gap 的来源；
- 避免客套和泛泛表述；
- 让它能够用于后续生成研究问题。
```

## 工作流：check raw

`check raw` 用于检查 `raw/papers/` 中哪些论文尚未被整理进入 `wiki/papers/`，并自动生成可批量执行的 `ingest.txt`。

### 使用方式

```sh
check raw
```

### 执行流程

1. 扫描 `raw/papers/*.md`。
2. 扫描 `wiki/papers/*.md`。
3. 对 raw 文件与 wiki 文件进行模糊匹配。
4. 跳过已经处理过的论文。
5. 自动生成 `ingest.txt`。

### 输出格式

`ingest.txt` 中每一行是一条 ingest 命令：

```text
ingest "xxx.md"
```

### 模糊匹配规则

模糊匹配应尽量避免因为文件名格式差异导致重复摄入。

匹配规则：

- 忽略大小写。
- 忽略空格。
- 忽略连字符。
- 忽略中英文标点差异。
- 优先比较作者、年份、标题关键词。

推荐比较顺序：

1. 从 raw 文件名或正文中提取作者、年份、标题关键词。
2. 从 `wiki/papers/*.md` 的文件名或 frontmatter/标题中提取作者、年份、标题关键词。
3. 优先用年份与标题关键词判断是否同一篇论文。
4. 作者信息存在时，用作者作为加强信号。
5. 只有在匹配置信度较高时才跳过；不确定时保留在 `ingest.txt` 中。

### Prompt 模板

```text
扫描 raw/papers/*.md 和 wiki/papers/*.md。

找出 raw/papers/ 中尚未整理进入 wiki/papers/ 的论文。

使用模糊匹配：
- 忽略大小写；
- 忽略空格；
- 忽略连字符；
- 忽略中英文标点差异；
- 优先比较作者、年份、标题关键词。

跳过已经在 wiki/papers/ 中表示过的论文。

生成 ingest.txt，每篇未处理论文对应一行命令：

ingest "xxx.md"
```

## 工作流：queue

`queue` 用于批量消费项目根目录下的 `ingest.txt`，将其中的每一行 `ingest "xxx.md"` 视为一个待处理论文任务。

该工作流适合在 `check raw` 生成 `ingest.txt` 后执行。它会从第一行开始顺序处理论文，并在每篇论文成功完成后从 `ingest.txt` 中删除对应行。

### Prompt 文件

```text
prompts/queue.txt
```

### 使用方式

```sh
queue
```

### 输入格式

`ingest.txt` 必须位于当前项目根目录。每一行格式如下：

```text
ingest "xxx.md"
```

其中 `xxx.md` 对应 `raw/papers/xxx.md`。

### 执行规则

1. 读取当前项目根目录下的 `ingest.txt`。
2. 将每一行 `ingest "xxx.md"` 视为一个待处理任务。
3. 从第一篇开始顺序处理。
4. 对每篇论文执行标准 `ingest` workflow：
   - 阅读 `raw/papers/` 中对应论文。
   - 提取核心 claim。
   - 分析默认假设。
   - 检查与 `wiki/` 的冲突。
   - 寻找具体 `Gap`。
   - 按 `CLAUDE.md` 写入 `wiki`。
5. 每处理完一篇：
   - 从 `ingest.txt` 中删除对应行。
   - 保存 `ingest.txt`。
6. 如果处理失败：
   - 停止队列。
   - 报告失败论文。
   - 不继续后续任务。
7. 每完成一篇后汇报：
   - 当前论文。
   - 新增页面。
   - 更新页面。
   - 新增 Gap。
8. 持续执行直到 `ingest.txt` 为空。
9. `ingest.txt` 为空时报告：

```text
Queue completed.
```

### Prompt 模板

```text
请读取当前项目根目录下的 ingest.txt。

把其中每一行：

ingest "xxx.md"

视为一个待处理任务队列。

按照以下规则执行：

1. 从第一篇开始处理。
2. 对每篇论文执行标准 ingest workflow：
   - 阅读 raw/papers/ 对应论文
   - 提取核心 claim
   - 分析默认假设
   - 检查与 wiki 的冲突
   - 寻找具体 Gap
   - 按 CLAUDE.md 写入 wiki
3. 每处理完一篇：
   - 从 ingest.txt 中删除对应行
   - 保存文件
4. 如果处理失败：
   - 停止队列
   - 报告失败论文
   - 不继续后续任务
5. 每完成一篇后汇报：
   - 当前论文
   - 新增页面
   - 更新页面
   - 新增 Gap
6. 持续执行直到 ingest.txt 为空。
7. ingest.txt 为空时报告：
   "Queue completed."

开始执行队列。
```

## macOS 配置

### 1. 安装 Node.js

使用官方安装包或包管理器安装 Node.js：

```sh
brew install node
```

### 2. 安装 Codex CLI

```sh
npm install -g @openai/codex
```

### 3. 创建 Prompt 目录

```sh
mkdir -p ~/.codex/prompts
```

创建 prompt 文件：

```sh
touch ~/.codex/prompts/ingest.md
touch ~/.codex/prompts/check-raw.md
touch ~/.codex/prompts/queue.txt
```

将 `ingest` 的 prompt 模板写入 `~/.codex/prompts/ingest.md`，将 `check raw` 的 prompt 模板写入 `~/.codex/prompts/check-raw.md`，将 `queue` 的 prompt 模板写入 `~/.codex/prompts/queue.txt`。

### 4. 配置 Shell Functions

将以下内容加入 `~/.zshrc`：

```sh
ingest() {
  codex "$(cat ~/.codex/prompts/ingest.md)

Target file: raw/papers/$1"
}

check() {
  if [ "$1" = "raw" ]; then
    codex "$(cat ~/.codex/prompts/check-raw.md)"
  else
    echo "Usage: check raw"
  fi
}

queue() {
  codex "$(cat ~/.codex/prompts/queue.txt)"
}
```

重新加载 shell：

```sh
source ~/.zshrc
```

### 最小示例

```sh
check raw
queue
ingest "xxx.md"
```

## Windows 配置

### 1. 安装 Node.js

使用官方 Windows 安装包安装 Node.js。

验证安装：

```powershell
node --version
npm --version
```

### 2. 安装 Codex CLI

```powershell
npm install -g @openai/codex
```

### 3. 创建 Prompt 目录

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\prompts"
New-Item -ItemType File -Force "$env:USERPROFILE\.codex\prompts\ingest.md"
New-Item -ItemType File -Force "$env:USERPROFILE\.codex\prompts\check-raw.md"
New-Item -ItemType File -Force "$env:USERPROFILE\.codex\prompts\queue.txt"
```

将 `ingest` 的 prompt 模板写入 `%USERPROFILE%\.codex\prompts\ingest.md`，将 `check raw` 的 prompt 模板写入 `%USERPROFILE%\.codex\prompts\check-raw.md`，将 `queue` 的 prompt 模板写入 `%USERPROFILE%\.codex\prompts\queue.txt`。

### 4. 配置 PowerShell Functions

打开 PowerShell Profile：

```powershell
notepad $PROFILE
```

加入：

```powershell
function ingest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$File
    )

    $prompt = Get-Content "$env:USERPROFILE\.codex\prompts\ingest.md" -Raw
    codex "$prompt`n`nTarget file: raw/papers/$File"
}

function check {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Target
    )

    if ($Target -eq "raw") {
        $prompt = Get-Content "$env:USERPROFILE\.codex\prompts\check-raw.md" -Raw
        codex $prompt
    } else {
        Write-Host "Usage: check raw"
    }
}

function queue {
    $prompt = Get-Content "$env:USERPROFILE\.codex\prompts\queue.txt" -Raw
    codex $prompt
}
```

重启 PowerShell，或运行：

```powershell
. $PROFILE
```

### 最小示例

```powershell
check raw
queue
ingest "xxx.md"
```

## 使用示例

### macOS

```sh
check raw
queue
ingest "xxx.md"
```

### Windows

```powershell
check raw
queue
ingest "xxx.md"
```

## 备注

- `CLAUDE.md` 定义 wiki 输出格式；`ingest` 写入时应遵循该格式。
- `ingest.txt` 用于 batch ingestion，每行对应一篇尚未处理论文。
- `queue` 消费 `ingest.txt`，每成功处理一篇就删除对应任务行。
- custom prompts 是本地配置，通常保存在用户目录下的 `.codex/prompts/`。
- fuzzy matching 会忽略大小写、空格、连字符与中英文标点差异。
- `check raw` 只负责生成待处理列表，不应修改 `raw/papers/` 或 `wiki/papers/`。
- `ingest` 在讨论完成前不应写入 wiki。
- `queue` 在任一论文处理失败时必须停止，不应继续后续任务。
