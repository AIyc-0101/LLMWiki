# LLMWiki Codex Subagents: shared research workflow

## 简介

LLMWiki 使用 Codex CLI 与本地 custom prompt 启动 `shared/research.md` 多视角协作流程。该流程将原来的 Claude / Gemini / Codex 三端手动切换，最小改动替换为 Codex 主会话 + subagents：

- `Context Synthesizer`：读取 `wiki/`、`raw/`、`discovery/`，整理已有结论、相关页面与不确定点。
- `Evidence Verifier`：验证最新证据、支持/反驳论文与趋势变化；如果当前 Codex 环境不能联网，必须明确降级为项目内证据检查。
- `Red-team Reviewer`：挑漏洞、找边界反例、给出最小可验证实验。
- `Final Synthesis`：由 Codex 主会话汇总共识、分歧、可信判断与建议写回草稿。

该工作流新增一个命令：

- `shared research`：读取本地 prompt 与项目内 `shared/research.md`，启动 Codex subagents 多视角讨论。默认只生成报告与写回草稿，不直接修改 `wiki/`；需要用户确认后再写回。

---

## 版本一：macOS

### 给 Codex 的安装提示词

```text
请在 macOS 上为当前 LLMWiki 项目安装并配置 Codex shared subagents workflow。

要求：
1. 确认 Node.js 已安装；如未安装，提示我使用 brew install node。
2. 确认 Codex CLI 已安装；如未安装，提示我运行 npm install -g @openai/codex。
3. 创建本地 prompt 目录 ~/.codex/prompts/。
4. 创建 prompt 文件：
   - ~/.codex/prompts/shared_subagents.md
5. 写入 shared-subagents.md：
   - 读取当前项目的 shared/research.md。
   - 如果“当前议题”仍是占位符，先要求我补充议题。
   - 使用 Codex subagents 分别完成 Context Synthesizer、Evidence Verifier、Red-team Reviewer 三个任务。
   - Evidence Verifier 必须先声明是否能联网；不能联网时只基于 discovery/、raw/、wiki/ 做项目内证据检查。
   - 三个 subagent 只返回分析，不直接改文件。
   - Codex 主会话汇总 Final Synthesis，输出共识、分歧、可信判断、最小验证实验、建议写回位置和写回草稿。
   - 默认不要写回 wiki；只有我明确确认后，才写入 wiki/synthesis/discussion-YYYY-MM-DD.md 并更新 wiki/log.md。
6. 修改 ~/.zshrc，添加 shared() 函数：
   - shared research：当参数为 research 时，读取 ~/.codex/prompts/shared_subagents.md，并调用 Codex。
7. 修改前先检查 ~/.zshrc 中是否已有同名函数，避免重复添加；如已存在，请更新对应函数。
8. 完成后告诉我需要运行 source ~/.zshrc。

安装完成后，以下命令应可用：

shared research
```

---

## 版本二：Windows PowerShell

### 给 Codex 的安装提示词

```text
请在 Windows PowerShell 上为当前 LLMWiki 项目安装并配置 Codex shared subagents workflow。

要求：
1. 确认 Node.js 已安装；如未安装，提示我安装官方 Windows Node.js 安装包。
2. 确认 Codex CLI 已安装；如未安装，提示我运行 npm install -g @openai/codex。
3. 创建本地 prompt 目录 %USERPROFILE%\.codex\prompts\。
4. 创建 prompt 文件：
   - %USERPROFILE%\.codex\prompts\shared_subagents.md
5. 写入 shared-subagents.md：
   - 读取当前项目的 shared/research.md。
   - 如果“当前议题”仍是占位符，先要求我补充议题。
   - 使用 Codex subagents 分别完成 Context Synthesizer、Evidence Verifier、Red-team Reviewer 三个任务。
   - Evidence Verifier 必须先声明是否能联网；不能联网时只基于 discovery/、raw/、wiki/ 做项目内证据检查。
   - 三个 subagent 只返回分析，不直接改文件。
   - Codex 主会话汇总 Final Synthesis，输出共识、分歧、可信判断、最小验证实验、建议写回位置和写回草稿。
   - 默认不要写回 wiki；只有我明确确认后，才写入 wiki/synthesis/discussion-YYYY-MM-DD.md 并更新 wiki/log.md。
6. 修改 PowerShell Profile，也就是 $PROFILE，添加 shared function：
   - shared research：当参数为 research 时，读取 %USERPROFILE%\.codex\prompts\shared_subagents.md，并调用 Codex。
7. 修改前先检查 $PROFILE 中是否已有同名 function，避免重复添加；如已存在，请更新对应 function。
8. 完成后告诉我需要重启 PowerShell，或运行 . $PROFILE。

安装完成后，以下命令应可用：

shared research
```
