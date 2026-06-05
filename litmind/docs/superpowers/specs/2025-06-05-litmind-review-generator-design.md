# LitMind Review Generator — Design Spec

Date: 2025-06-05
Status: Draft
Module: 8/?

## Overview

Review Generator 接收一个研究主题，自动通过 Knowledge Base 检索相关文献，分析研究趋势、主题聚类、共识与争议，生成结构化综述框架和带引用的综述草稿。

**核心原则：** 所有内容必须引用知识库中的真实文献。禁止虚构作者、年份、DOI、期刊。

**依赖模块：** litmind-knowledge (Part 4), litmind-chat (Part 5), litmind-evidence (Part 6), litmind-discussion (Part 7)

---

## 1. Data Flow

```
用户输入: "Flatfoot Biomechanics"
    │
    ▼
KB 检索 ─── semantic_search + search_claims + search_variables
    │ 返回 papers 列表 (含 title, year, variables, claims, keywords, researchDomain...)
    ▼
ThemeDiscoveryEngine ─── LLM 聚类 + 命名 → [Theme(name, paperCount, paperIds)]
    │
    ├─ TrendAnalyzer ─── 统计高频变量/方法/设计/年份分布
    ├─ ConsensusAnalyzer ─── 对每主题调 Evidence Finder → 共识性陈述
    ├─ ControversyAnalyzer ─── 找 support/oppose 并存 claims → 争议
    └─ GapAnalyzer ─── 分析低频方向 + LLM 推断 → 空白
    │
    ▼
OutlineGenerator ─── 组装 8 节框架
    │
    ▼
ReviewComposer ─── LLM 逐 Section 生成 (前节作为下节上下文)
    │
    ▼
ReviewResult { topic, paperCount, themes, consensus, controversies, gaps, outline, draft, citations }
```

---

## 2. Data Models

```python
class ReviewInput(BaseModel):
    topic: str
    max_papers: int = 50

class ReviewTheme(BaseModel):
    name: str
    paperCount: int = 0
    paperIds: list[str] = []
    description: str = ""

class ResearchConsensus(BaseModel):
    statement: str
    supportingPapers: int = 0
    paperIds: list[str] = []

class ResearchControversy(BaseModel):
    statement: str
    support: int = 0
    oppose: int = 0
    supportingPaperIds: list[str] = []
    opposingPaperIds: list[str] = []

class ResearchGap(BaseModel):
    description: str
    evidence: str = ""

class ReviewResult(BaseModel):
    topic: str
    paperCount: int = 0
    researchThemes: list[ReviewTheme] = []
    researchConsensus: list[ResearchConsensus] = []
    researchControversies: list[ResearchControversy] = []
    researchGaps: list[ResearchGap] = []
    reviewOutline: dict[str, list[str]] = {}
    reviewDraft: str = ""
    citations: list[DiscussionCitation] = []
```

---

## 3. Service Architecture

### 3.1 ThemeDiscoveryEngine

```
Input: papers list (每篇含 title, variables, keywords, researchDomain, claims)
Process: 调用 LLM 对 papers 做主题聚类
Output: list[ReviewTheme]
```

Prompt 策略：传入所有论文的 title + keywords + variables，要求 LLM 归类为 3-7 个主题并命名。

### 3.2 TrendAnalyzer

```
Input: papers list
Output: {
  top_variables: [(var, count)],
  top_statistics: [(stat, count)],
  top_designs: [(design, count)],
  year_distribution: { year: count }
}
```

### 3.3 ConsensusAnalyzer

对每个主题，用主题名调 `evidence_service.find_evidence()`。筛选出 `evidenceStrength` 为 "Strongly Supported" 或 "Moderately Supported" 的，作为共识性陈述。

### 3.4 ControversyAnalyzer

对每个主题，调 `evidence_service.find_evidence()`，找出 support 和 oppose 都 > 0 的 query，计算比例，返回争议项。

### 3.5 GapAnalyzer

分析：
- 低频研究方向（仅 1-2 篇论文的主题）
- 知识库中缺失的常见子领域（LLM 推断）
- 时间分布缺口（近年无新研究）

### 3.6 OutlineGenerator

基于以上全部结果，调用 LLM 生成 8 节综述框架，每节含 2-4 个子节。

### 3.7 ReviewComposer

基于 outline + 所有数据，LLM 逐 Section 生成全文。

Section 1: Introduction
Section 2: Current Research Landscape
Section 3: Major Research Themes
Section 4: Evidence Consensus
Section 5: Research Controversies
Section 6: Research Gaps
Section 7: Future Directions
Section 8: Conclusion

---

## 4. Citation Safety

复用 Discussion Generator 的 CitationManager 模式：
- 所有引用 paperId 必须在检索结果的白名单内
- post_process() 校验后丢弃未知引用

---

## 5. Files to Create

```
litmind/src/litmind_review/
├── __init__.py
├── models.py
├── config.py
├── cache.py
├── discovery.py
├── trend.py
├── consensus.py
├── controversy.py
├── gaps.py
├── outline.py
├── composer.py
├── service.py
└── prompts.py

litmind/tests/test_review_models.py
litmind/tests/test_review_discovery.py
litmind/tests/test_review_trend.py
litmind/tests/test_review_consensus.py
litmind/tests/test_review_controversy.py
litmind/tests/test_review_gaps.py
litmind/tests/test_review_outline.py
litmind/tests/test_review_composer.py
litmind/tests/test_review_service.py

litmind/.claude/skills/litmind-review/SKILL.md
litmind/scripts/review.py
```

---

## 6. Non-Goals

- 不执行 Meta-analysis 统计计算
- 不生成系统评价的 PRISMA 流程图
- 不生成参考文献格式化文件（RIS/ENW）
- 不对论文质量做偏倚风险评估
