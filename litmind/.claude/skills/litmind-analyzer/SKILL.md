---
name: litmind-analyzer
description: LitMind Paper Analyzer — 将论文全文转为结构化科研知识 (PaperAnalysis)
---

# LitMind Paper Analyzer

将 Paper Parser 输出的 PaperContent（论文全文）通过 LLM 分析，提取为结构化 PaperAnalysis。

**不做自由文本摘要。** 重点是知识提取：研究问题、方法、变量、统计、发现、声明、局限、未来方向、深度数值提取。

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
统一 PaperAnalysis JSON（含可选的 deepExtraction 深度提取数据）。

## 深度提取 (DeepExtraction) v0.4.0+

除摘要级知识外，analyzer 还会从 Results/Methods 中提取**细粒度数值数据**：

- **numericalFindings**: 含条件、指标、数值、单位、统计量的结构化数据
  - 例: `{"condition": "Flatfoot + CS shoe", "metric": "Ankle eversion ROM", "value": 12.3, "unit": "deg", "statistics": "p=0.003"}`
- **experimentalProtocols**: 实验参数，如 `"Drop height: 45cm"`, `"Sampling rate: 1000Hz"`
- 此为 **optional 字段**，LLM 无法提取时留空，不影响原流程
- 深度提取数据存入独立 ChromaDB collection，M5 问答时可检索到具体数值

## 输出格式

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
- `LITMIND_LOG_LEVEL` — 日志级别 (DEBUG/INFO/WARNING/ERROR, 默认 WARNING)
