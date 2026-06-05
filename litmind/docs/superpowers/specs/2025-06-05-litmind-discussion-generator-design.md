# LitMind Discussion Generator — Design Spec

Date: 2025-06-05
Status: Draft
Module: 7/?

## Overview

Discussion Generator 接收用户的研究结果（studyTopic + results），自动通过 Knowledge Base 和 Evidence Finder 检索相关文献证据，生成具有科学依据、可追溯引用的 Discussion 草稿。

**核心原则：** 所有论述必须有 Knowledge Base 中的文献来源。禁止生成虚假引用。

**依赖模块：** litmind-knowledge (Part 4), litmind-chat (Part 5), litmind-evidence (Part 6)

---

## 1. Data Flow

```
用户输入: DiscussionInput { studyTopic, results }
    │
    ▼
ResultParser ─── 解析每条结果，提取核心变量
    │
    ▼
EvidenceCollector ─── 遍历 results，为每条调用:
    │   evidence_service.find_evidence(result_i)
    │   → 合并所有证据到 mapped_evidence: { result_index: EvidenceResult }
    │
    ▼
DiscussionComposer ─── 逐步生成 7 个 Section:
    │   1. Main Finding Interpretation
    │   2. Supporting Evidence
    │   3. Contradictory Evidence
    │   4. Potential Mechanisms
    │   5. Practical Implications
    │   6. Study Limitations
    │   7. Future Directions
    │   (每个 Section 生成时传入上一步的上下文 + 相关证据)
    │
    ▼
CitationManager ─── 后处理：
    │   - 提取 LLM 输出中的 [paperId] 标记
    │   - 去重、校验 paperId 存在性
    │   - 生成结构化 citation 列表
    │
    ▼
DiscussionResult
```

---

## 2. Data Models

```python
# src/litmind_discussion/models.py

class DiscussionInput(BaseModel):
    studyTopic: str
    results: list[str]

class DiscussionCitation(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    authors: str = ""
    doi: str = ""
    claim: str = ""
    section: str = ""

class DiscussionResult(BaseModel):
    discussionOutline: dict[str, str] = {}    # { section_title: summary }
    discussionDraft: str = ""
    supportingPapers: list[EvidenceItem] = []
    opposingPapers: list[EvidenceItem] = []
    citations: list[DiscussionCitation] = []
```

---

## 3. Service Architecture

### 3.1 ResultParser

```
ResultParser.parse(results) → list[ParsedResult]
```

ParsedResult 包含:
- `original: str` — 原始结果文本
- `variables: list[str]` — 提取的核心变量
- `direction: str` — 方向 (increase/decrease/no_difference)

### 3.2 EvidenceCollector

```
EvidenceCollector.collect(parsed_results) → CollectedEvidence
```

CollectedEvidence:
- `by_result: dict[int, EvidenceResult]` — 每条结果对应的证据
- `supporting: list[EvidenceItem]` — 所有支持证据（去重）
- `opposing: list[EvidenceItem]` — 所有反对证据（去重）
- `all_papers: list[EvidenceItem]` — 全部

### 3.3 CitationManager

```
CitationManager.track(citations)  → 管理引用去重
CitationManager.post_process(draft_text)  → 提取标记，校验
```

### 3.4 DiscussionComposer

按 7 个 Section 逐步生成，每步传入:
- 前一步的输出文本
- 当前 Section 相关的证据
- system prompt + section-specific prompt

### 3.5 DiscussionGeneratorService

统一入口，编排全流程。

---

## 4. Prompt Strategy

### System Prompt

```
You are a scientific discussion writer. Your task is to write the Discussion
section of a research paper based on the study's results and retrieved
evidence from the literature.

Rules:
1. Every statement must be supported by evidence from the provided reference list.
2. Use [paperId] markers to cite sources within the text.
3. Clearly distinguish between: the study's own findings, literature evidence, and speculative interpretations.
4. Do NOT fabricate authors, DOIs, or citations. Only use references from the provided list.
5. Output plain text with [paperId] markers for citations.
```

### Section Prompts

每个 section 有独立的 prompt，传入相应的证据子集。

---

## 5. Citation Safety

| 机制 | 说明 |
|---|---|
| **paperId 白名单** | LLM 只能引用 prompt 中给出的 paperId |
| **后处理校验** | CitationManager 校验所有 paperId 是否存在于 KB |
| **去重** | 同一 paperId 在同一 section 中只出现一次 |
| **过滤** | 未通过校验的引用自动丢弃，不影响 draft 主文本 |

---

## 6. Files to Create

```
litmind/src/litmind_discussion/
├── __init__.py
├── models.py
├── config.py
├── parser.py
├── collector.py
├── citation.py
├── composer.py
├── service.py
├── cache.py
└── prompts.py

litmind/tests/
├── test_discussion_models.py
├── test_discussion_parser.py
├── test_discussion_collector.py
├── test_discussion_citation.py
├── test_discussion_composer.py
└── test_discussion_service.py

litmind/.claude/skills/litmind-discussion/SKILL.md
litmind/scripts/discussion.py
```

---

## 7. Non-Goals

- 不生成 Methods / Results / Conclusion 部分
- 不修改用户输入的研究结果
- 不做证据质量评分（由 Evidence Finder 完成）
- 不生成整篇论文
