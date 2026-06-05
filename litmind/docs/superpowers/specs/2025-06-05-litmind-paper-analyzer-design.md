# LitMind Paper Analyzer — Design Spec

Date: 2025-06-05
Status: Draft
Module: 3/?

## Overview

Paper Analyzer 是 LitMind 的第三模块。它接收模块二（Paper Parser）输出的 `PaperContent`，通过大语言模型提取结构化科研知识，输出统一的 `PaperAnalysis` 模型。

**核心定位：** 论文知识提取工具，而非摘要生成器。输出用于后续的 Knowledge Base、Research Chat、Evidence Finder、Discussion Generator。

**跨平台目标：** 核心为纯 Python pip 包，Claude Code / Codex / VS Code / Gemini CLI 均可使用。

---

## 1. Data Model: PaperAnalysis

Pydantic `BaseModel`，所有字段必须存在，缺失返回 `null` 或 `[]`。

```python
class Claim(BaseModel):
    statement: str = ""
    evidenceSource: str = ""

class ParticipantInfo(BaseModel):
    sampleSize: Optional[int] = None
    groups: list[str] = []
    population: str = ""

class PaperAnalysis(BaseModel):
    paperId: str = ""
    researchQuestion: str = ""
    researchDomain: str = ""
    studyDesign: str = ""
    participants: ParticipantInfo = ParticipantInfo()
    methods: list[str] = []
    statistics: list[str] = []
    variables: list[str] = []
    outcomes: list[str] = []
    mainFindings: list[str] = []
    claims: list[Claim] = []
    limitations: list[str] = []
    futureDirections: list[str] = []
    keywords: list[str] = []
```

### 字段说明

| 字段 | 类型 | 来源策略 |
|---|---|---|
| `paperId` | str | 从 PaperContent.paperKey 传入 |
| `researchQuestion` | str | 从 Introduction 末尾提取 |
| `researchDomain` | str | 从全文判断（Biomechanics / Medicine / CS...） |
| `studyDesign` | str | 从 Methods 提取（RCT / Cross-sectional / Cohort...） |
| `participants` | ParticipantInfo | 从 Methods 提取样本量、分组、人群描述 |
| `methods` | list[str] | 每个元素一条方法（设备/任务/协议） |
| `statistics` | list[str] | 每个元素一种统计方法（t-test / ANOVA / SPM...） |
| `variables` | list[str] | 自变量/因变量/控制变量 |
| `outcomes` | list[str] | 主要结果指标 |
| `mainFindings` | list[str] | 每条一个独立发现 |
| `claims` | list[Claim] | 每条含 statement + evidenceSource |
| `limitations` | list[str] | 从 Discussion/Conclusion 提取 |
| `futureDirections` | list[str] | 从 Conclusion 末尾提取 |
| `keywords` | list[str] | LLM 自动生成 |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ src/litmind_analyzer/                                        │
│                                                             │
│  models.py        PaperAnalysis Pydantic 模型                │
│  provider.py      LLMProvider 抽象基类                       │
│  providers/                                                   │
│    anthropic.py   Claude structured output 实现               │
│    openai.py      OpenAI function calling 实现                │
│  analyzer.py      主流程：prompt → LLM → 验证 → 输出        │
│  validator.py     Schema 验证 + 字段完整性检查               │
├─────────────────────────────────────────────────────────────┤
│ scripts/analyze.py   CLI 入口                                 │
├─────────────────────────────────────────────────────────────┤
│ .claude/skills/litmind-analyzer/SKILL.md   Claude Code skill │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
PaperContent JSON
    │
    ▼
_build_prompt(paper)
    │  拼接：System Prompt + 各章节文本
    │  Token 超长时优先截断：other > references > conclusion
    ▼
provider.analyze(prompt, model=...)
    │  Claude: structured output (tool use)
    │  OpenAI: function calling
    ▼
Pydantic model_validate()
    │  验证类型、补全缺失字段
    ▼
PaperAnalysis JSON (已校验)
```

### LLM Provider 接口

```python
class LLMProvider(ABC):
    @abstractmethod
    def analyze(
        self,
        paper: PaperContent,
        model: str = "",
    ) -> dict:
        """返回可转为 PaperAnalysis 的 dict"""
        ...
```

---

## 3. Prompt 设计

### System Prompt

```
You are a research paper analyzer. Extract structured scientific knowledge from
the paper content below.

Rules:
1. Output ONLY valid JSON matching the PaperAnalysis schema.
2. Do NOT add any explanatory text, markdown formatting, or natural language summary.
3. Every field must be present. Use null for missing single values, [] for missing lists.
4. Only extract information explicitly stated in the paper. Do not infer or fabricate.
5. For claims: each claim must be directly supported by text in the paper.
```

### User Prompt 结构

```
Research Question: <从 Introduction 或全文推断>

--- Abstract ---
<text>

--- Introduction ---
<text>

--- Methods ---
<text>

--- Results ---
<text>

--- Discussion ---
<text>

--- Conclusion ---
<text>
```

### 输出 Schema 约束

通过 LLM 的 structured output 机制传递 Pydantic schema。Anthropic 用 `tool_use` + `anthropic_structured_outputs`，OpenAI 用 `function_call` + `response_format`。

---

## 4. CLI Interface

```bash
# 分析单篇
litmind-analyze parsed_paper.json -o analysis.json

# 指定 provider
litmind-analyze paper.json --provider openai --model gpt-4o

# 指定 API key（覆盖环境变量）
litmind-analyze paper.json --api-key sk-...

# 批量分析
litmind-analyze batch ./parsed/ -o ./analyses/
```

### 配置文件 (可选)

`litmind_config.json` or env vars:

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "api_key": "${ANTHROPIC_API_KEY}"
}
```

---

## 5. Error Handling

| 场景 | 行为 |
|---|---|
| API 调用失败 | 自动重试 1 次，失败后记录到 `parseErrors` |
| Pydantic 验证失败 | 保留原始 LLM输出 到 `_raw_output` 字段 |
| Token 超出限制 | 按优先级截断章节：other > references > conclusion > introduction |
| 空内容 | 返回所有字段为默认值的 PaperAnalysis |

---

## 6. Cross-Platform Distribution

| 平台 | 使用方式 |
|---|---|
| Claude Code | `/litmind-analyzer paper.json` (skill) |
| Codex / Cursor | 内置 skill 支持 |
| VS Code | 终端运行 `litmind-analyze` |
| 任何 Python 环境 | `from litmind_analyzer import analyze_paper` |

所有平台的 skill 都是 CLI 的薄包装层。

---

## 7. Files to Create

```
litmind/src/litmind_analyzer/
├── __init__.py
├── models.py               # PaperAnalysis Pydantic
├── provider.py             # LLMProvider ABC
├── providers/
│   ├── __init__.py
│   ├── anthropic.py        # Claude implementation
│   └── openai.py           # OpenAI implementation
├── analyzer.py             # analyze_paper() main entry
├── validator.py            # Post-validation helpers
├── prompts.py              # System prompt templates

litmind/scripts/
├── analyze.py              # CLI entry

litmind/.claude/skills/
├── litmind-analyzer/SKILL.md

litmind/pyproject.toml      # 添加 litmind-analyzer 入口点
```

---

## 8. Non-Goals

- 不做 PDF 解析（那是模块二的工作）
- 不做文献去重/相似度计算
- 不做图表提取
- 不做引用关系分析
- 不生成自然语言摘要（只生成结构化数据）
