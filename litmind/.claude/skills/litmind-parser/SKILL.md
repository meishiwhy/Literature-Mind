---
name: litmind-parser
description: LitMind Paper Parser — 从 PDF 读取全文、清洗噪声、识别标准章节，输出结构化 PaperContent
---

# LitMind Paper Parser

从 PDF 提取全文 → **提取表格** → 自动清洗（页眉/页脚/页码/重复）→ 识别标准章节（Abstract/Introduction/Methods/Results/Discussion/Conclusion/References）→ 输出结构化 PaperContent。

**不做 AI 分析。** 只负责 PDF 解析和文本结构化。

## 工作流程

### Step 1: 读取 PDF
支持多引擎（pymupdf / pdfplumber / PyPDF2），自动选择可用的。

### Step 2: 提取表格（v0.2.0+）
使用 pymupdf 的 `find_tables()` 自动检测和提取 PDF 中的表格，转为 Markdown 格式。
- 表格数据作为结构化 `ExtractedTable` 对象存储在 `tables` 字段
- Markdown 表格文本拼接到 `fullText` 末尾供 LLM 分析
- 仅 pymupdf 引擎支持，无 pymupdf 时静默跳过
- cleaner 不再删除 `Table N` / `Figure N` 行，保留表格上下文

### Step 3: 清洗文本
- 移除页码（纯数字页、Page N、-N-、第N页）
- 移除跨页重复的页眉/页脚
- 移除 DOI、版权、致谢等噪声
- 去除相邻重复段落

### Step 4: 识别章节
中英文双模式匹配，识别：
- Abstract / 摘要
- Introduction / 引言
- Methods / 方法
- Results / 结果
- Discussion / 讨论
- Conclusion / 结论
- References / 参考文献

### Step 5: 输出
统一 `PaperContent` JSON 格式（含 `tables` 字段）。

## 输出格式

```json
{
  "paperKey": "KP33THHS",
  "sourcePath": "C:/.../paper.pdf",
  "fullText": "清洗后的全文...\n\n--- Extracted Tables ---\n\n[Table 1]\n| Header1 | Header2 |\n| --- | --- |\n| data1 | data2 |",
  "sections": {
    "abstract": "...",
    "introduction": "...",
    "methods": "...",
    "results": "...",
    "discussion": "...",
    "conclusion": "...",
    "references": "..."
  },
  "tables": [
    {
      "pageNum": 1,
      "header": ["Header1", "Header2"],
      "rows": [["data1", "data2"]],
      "markdown": "| Header1 | Header2 |\n| --- | --- |\n| data1 | data2 |"
    }
  ],
  "pageCount": 8,
  "charCount": 45231,
  "parseSuccess": true
}
```

## 调用方式

```
/litmind-parser [pdf_path]
```

## 路径

Python 包: `litmind/src/litmind_parser/`
