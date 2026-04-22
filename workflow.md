# LLMWiki 工作流程（图片版优化落地）

## 1. 目录结构设计

- `raw/`：原始输入层（append-only）
- `wiki/`：知识工作层（可持续编辑）
- `shared/research.md`：多模型协作上下文
- `CLAUDE.md`：全局 schema + 工作规范（最重要）

### wiki 分层
- `wiki/papers/`：论文页（每篇一个页面）
- `wiki/concepts/`：方法/理论页
- `wiki/entities/`：作者/数据集/系统/benchmark
- `wiki/comparisons/`：方法对比页
- `wiki/gaps/`：confirmed-gaps / hypotheses / questions
- `wiki/synthesis/`：field-map / shared-assumptions / discussion

## 2. Ingest（处理新论文）

1. 将论文放入 `raw/papers/`
2. 运行 `scripts/compile_wiki.py` 生成论文草稿
3. 按 `CLAUDE.md` 模板补全：问题设定、方法核心、实验结论、局限与 gap
4. 同步更新 `wiki/concepts/` 与 `wiki/index.md`
5. 追加更新 `wiki/log.md`

## 3. Query（领域问答）

1. 先从 `wiki/index.md` 定位相关页面
2. 回答后，不只给即时结论
3. 将核心结论（200 字内）写回 `wiki/synthesis/discussion-YYYY-MM-DD.md`
4. 如形成稳定对比，写入 `wiki/comparisons/`

## 4. Idea（研究假设生成）

1. 读取 `wiki/gaps/confirmed-gaps.md` + `wiki/gaps/questions.md`
2. 结合最新论文与反例，提出可检验假设
3. 写入 `wiki/gaps/hypotheses.md` 并标注状态：`draft/testing/confirmed/rejected`

## 5. Lint（1-2 周一次健康检查）

检查并输出报告：
- 孤儿页面
- `hypotheses.md` 的 draft 是否已被验证/反驳
- `field-map.md` 是否缺失关键路径
- 同一主题是否存在冲突结论

## 6. 多模型辩论与沉淀

- 在 `shared/research.md` 写入辩题与背景
- Claude：综合 wiki 内容，输出主结论
- Gemini：联网核验最新论文与反例
- Codex：挑漏洞与边界反例
- 结果回写 `wiki/synthesis/discussion-YYYY-MM-DD.md`

## 7. 第四步可视化层（改为 ChatGPT）

使用 `prompts/chatgpt_visualization_prompt.md`：
- 读取 `wiki/` 内容
- 生成 Mermaid 概念图 / gap 优先级 / 证据链表格
- 可视化输出不直接改写 wiki，由人工审阅后回写
