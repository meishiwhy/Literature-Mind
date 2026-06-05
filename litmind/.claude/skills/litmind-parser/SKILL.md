---
name: litmind-parser
description: LitMind Paper Parser — 从 PDF 读取全文、清洗噪声、识别标准章节，输出结构化 PaperContent
---

# LitMind Paper Parser

从 PDF 提取全文 → 自动清洗（页眉/页脚/页码/重复）→ 识别标准章节（Abstract/Introduction/Methods/Results/Discussion/Conclusion/References）→ 输出结构化 PaperContent。

**不做 AI 分析。** 只负责 PDF 解析和文本结构化。

## 工作流程

### Step 1: 读取 PDF
支持多引擎（pymupdf / pdfplumber / PyPDF2），自动选择可用的。

### Step 2: 清洗文本
- 移除页码（纯数字页、Page N、-N-、第N页）
- 移除跨页重复的页眉/页脚
- 移除 DOI、版权、Figure/Table 标题等噪声
- 去除相邻重复段落

### Step 3: 识别章节
中英文双模式匹配，识别：
- Abstract / 摘要
- Introduction / 引言
- Methods / 方法
- Results / 结果
- Discussion / 讨论
- Conclusion / 结论
- References / 参考文献

### Step 4: 输出
统一 `PaperContent` JSON 格式。

## 输出格式

```json
{
  "paperKey": "KP33THHS",
  "sourcePath": "C:/.../paper.pdf",
  "fullText": "清洗后的全文...",
  "sections": {
    "abstract": "...",
    "introduction": "...",
    "methods": "...",
    "results": "...",
    "discussion": "...",
    "conclusion": "...",
    "references": "..."
  },
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
