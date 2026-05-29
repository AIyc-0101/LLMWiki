# LLMWiki Codex Prompts: macOS

## 简介

LLMWiki 使用 Codex CLI 与本地 custom prompts 建立论文整理工作流。核心流程是将 `raw/papers/*.md` 中的论文整理为 `wiki/papers/*.md`，并在整理过程中提取核心 claim、默认假设、与现有 wiki 的冲突，以及可继续研究的具体 `Gap 线索`。

该工作流包含三个命令：

- `ingest "xxx.md"`：处理单篇论文。
- `check raw`：扫描 `raw/papers/` 与 `wiki/papers/`，生成 `ingest.txt`。
- `queue`：读取 `ingest.txt`，按顺序批量执行 ingest，并在每篇成功后删除对应任务行。

## 给 Codex 的安装提示词

```text
请在 macOS 上为当前 LLMWiki 项目安装并配置 Codex custom prompts workflow。

要求：
1. 确认 Node.js 已安装；如未安装，提示我使用 brew install node。
2. 确认 Codex CLI 已安装；如未安装，提示我运行 npm install -g @openai/codex。
3. 创建本地 prompt 目录 ~/.codex/prompts/。
4. 创建三个 prompt 文件：
   - ~/.codex/prompts/ingest.md
   - ~/.codex/prompts/check-raw.md
   - ~/.codex/prompts/queue.txt
5. 根据当前仓库根目录的 custom-prompts.md，提取并写入三个 prompt：
   - ingest.md：单篇论文 ingest workflow。
   - check-raw.md：扫描 raw/papers/ 与 wiki/papers/ 并生成 ingest.txt 的 workflow。
   - queue.txt：读取 ingest.txt 并顺序执行队列的 workflow。
6. 修改 ~/.zshrc，添加以下函数：
   - ingest()：读取 ~/.codex/prompts/ingest.md，并把参数作为 raw/papers/$1 传给 Codex。
   - check()：当参数为 raw 时读取 ~/.codex/prompts/check-raw.md 并调用 Codex。
   - queue()：读取 ~/.codex/prompts/queue.txt 并调用 Codex。
7. 修改前先检查 ~/.zshrc 中是否已有同名函数，避免重复添加；如已存在，请更新对应函数。
8. 完成后告诉我需要运行 source ~/.zshrc。

安装完成后，以下命令应可用：

check raw
queue
ingest "xxx.md"
```
