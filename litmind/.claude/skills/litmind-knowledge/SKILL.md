---
name: litmind-knowledge
description: LitMind Knowledge Base — 存储、索引、检索、更新科研知识库
---

# LitMind Knowledge Base

将 Paper Analyzer 输出的 PaperAnalysis 存入双存储架构（SQLite + ChromaDB），提供统一的检索接口。

## 数据流

PaperAnalysis → KnowledgeBase → SQLite (结构化) + ChromaDB (向量索引)
                                    ↕
                              get_paper() 自动恢复 deepExtraction

## 公开接口

- add_paper — 新增文献
- update_paper — 更新文献
- delete_paper — 删除文献
- get_paper — 获取单篇文献
- search_papers — 关键词检索
- search_variables — 检索变量
- search_statistics — 检索统计方法
- search_claims — 检索科学结论
- semantic_search — 语义搜索

## 调用方式

```bash
litmind-knowledge add analysis.json
litmind-knowledge get PAPER_ID
litmind-knowledge search "flatfoot"
litmind-knowledge semantic "Does flatfoot increase MTP ROM?"
litmind-knowledge batch ./analyses/
litmind-knowledge rebuild
```

## 依赖

- SQLAlchemy (SQLite)
- ChromaDB (向量库)
- sentence-transformers (embedding, 离线免费)
