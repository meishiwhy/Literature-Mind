---
name: litmind-analyzer
description: LitMind Paper Analyzer — 将论文全文转为结构化科研知识 (PaperAnalysis)
---

# LitMind Paper Analyzer

将 Paper Parser 输出的 PaperContent（论文全文）通过 LLM 分析，提取为结构化 PaperAnalysis。

**不做自由文本摘要。** 重点是知识提取：研究问题、方法、变量、统计、发现、声明、局限、未来方向。

## 工作流程

### Step 1: 输入
接收 PaperContent JSON（来自 `/litmind-parser` 的输出）。

### Step 2: 分析
调 LLM 提取结构化知识。支持：
- Anthropic Claude (default)
- OpenAI GPT-4o

### Step 3: 验证
Pydantic schema 验证 + 字段完整性补全。

### Step 4: 输出
统一 PaperAnalysis JSON。

## 输出格式

```json
{
  "paperId": "KP33THHS",
  "researchQuestion": "Does landing height affect GRF?",
  "studyDesign": "Experimental Study",
  "participants": {
    "sampleSize": 20,
    "groups": ["Flat", "Normal"],
    "population": "Healthy males"
  },
  "methods": ["3D motion capture", "Force plate", "EMG"],
  "statistics": ["Repeated measures ANOVA"],
  "mainFindings": ["Flat feet had greater peak GRF"],
  "claims": [
    {"statement": "Flat feet increase GRF", "evidenceSource": "Results"}
  ]
}
```

## 调用方式

```bash
# CLI
litmind-analyze paper_parsed.json -o analysis.json

# 指定 provider
litmind-analyze paper.json --provider openai --model gpt-4o

# 批量
litmind-analyze batch ./parsed/ -o ./analyses/
```

## 环境变量

- `ANTHROPIC_API_KEY` — Claude provider
- `OPENAI_API_KEY` — OpenAI provider
