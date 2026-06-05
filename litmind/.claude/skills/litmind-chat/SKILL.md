---
name: litmind-chat
description: LitMind Research Chat — 面向科研知识库的自然语言问答系统
---

# LitMind Research Chat

基于 Knowledge Base 的科研智能问答系统。用户通过自然语言提问，系统自动检索知识库，返回带出处、可追溯的答案。

## 工作流程

问题 → QueryClassifier → ContextBuilder (KB检索) → AnswerGenerator (LLM) → 带引用答案

## 调用方式

```bash
# 命令行提问
litmind-chat ask "Does flatfoot increase forefoot motion?"

# 交互式模式
litmind-chat interactive

# JSON 格式输出
litmind-chat ask "SPM1D 相关研究" --json-output

# 仅检索不生成
litmind-chat search "哪些文献研究 foot arch"
```

## 环境变量

- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — LLM 提供者
- `LITMIND_DB_PATH` — SQLite 路径
- `LITMIND_CHROMA_PATH` — ChromaDB 路径
