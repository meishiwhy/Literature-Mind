---
name: litmind-zotero
description: LitMind Zotero Connector — 从 Zotero 本地数据库导出全部文献（期刊/学位论文/会议论文等）+ 独立PDF附件为统一 PaperMetadata 模型
---

# LitMind Zotero Connector

你是一个 Zotero 数据连接器。从 Zotero 本地 SQLite 数据库读取**所有学术文献类型**（期刊论文、学位论文、会议论文、预印本等）以及**独立导入的 PDF 附件**，输出为统一的 PaperMetadata JSON 格式。

## 原则

- **只读** — 绝不修改 Zotero 数据库（`PRAGMA query_only = ON`）
- **全量导出** — 所有学术类型（非 note/attachment）均纳入；独立 PDF 附件从文件名提取元数据
- **不做 AI 分析** — 只做元数据同步

## 工作流程

### Step 1: 定位数据库
运行 `scripts/cli.py`，自动发现 `zotero.sqlite`（扫描 APPDATA、HOME 等常见路径，也支持 `--db` 手动指定）。

### Step 2a: 提取有元数据的文献
SQL 过滤 `itemTypeID NOT IN (1, 14)`，覆盖所有学术类型：
- journalArticle (5)
- thesis (7)
- conferencePaper (10)
- preprint、bookSection 等

提取字段：key, title, authors, year, doi, journal, volume, issue, pages, abstract, pdfPath, tags, collections, url。

### Step 2b: 提取独立 PDF 附件
SQL 查询 `itemTypeID = 14`（attachment）且无父条目（无关联元数据）的 PDF：
- 从文件名正则提取标题、年份
- 解析 Zotero 存储路径为真实文件路径
- 标记 `itemType = "standalone_pdf"`

### Step 3: 输出
统一 `PaperMetadata` 模型，每条文献一个 JSON 对象。

### Step 4: 报告
有元数据的文献数、独立 PDF 数、总导出数、有 PDF 数、有 DOI 数、有摘要数。

## 调用方式

```
/litmind-zotero
```

## 路径

Python 包: `litmind/src/litmind_zotero/`
