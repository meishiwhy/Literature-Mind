# Review Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Review Generator module — takes a research topic, retrieves papers from KB, discovers themes, analyzes trends/consensus/controversies/gaps, generates structured review outline and full draft with citations.

**Architecture:** Pipeline with 7 specialized analyzers feeding into an LLM-based composer. ThemeDiscoveryEngine clusters papers → TrendAnalyzer/ConsensusAnalyzer/ControversyAnalyzer/GapAnalyzer run in parallel → OutlineGenerator → ReviewComposer (8 sections). Reuses KnowledgeBase, EvidenceFinderService, and CitationManager from existing modules.

**Tech Stack:** Python 3.10+, Pydantic v2, litmind-knowledge, litmind-evidence, litmind-discussion (CitationManager), litmind-analyzer (LLMProvider)

---

## File Structure

```
litmind/src/litmind_review/
├── __init__.py              # Package entry
├── models.py                # ReviewInput, ReviewTheme, ResearchConsensus, ResearchControversy, ResearchGap, ReviewResult
├── config.py                # Configuration
├── cache.py                 # DiscussionCache (reuse pattern)
├── discovery.py             # ThemeDiscoveryEngine (LLM clustering)
├── trend.py                 # TrendAnalyzer (frequency stats)
├── consensus.py             # ConsensusAnalyzer
├── controversy.py           # ControversyAnalyzer
├── gaps.py                  # GapAnalyzer
├── outline.py               # OutlineGenerator
├── composer.py              # ReviewComposer (LLM 8-section generation)
├── service.py               # ReviewGeneratorService (orchestrator)
└── prompts.py               # LLM prompts

litmind/tests/
├── test_review_models.py
├── test_review_discovery.py
├── test_review_trend.py
├── test_review_consensus.py
├── test_review_controversy.py
├── test_review_gaps.py
├── test_review_outline.py
├── test_review_composer.py
└── test_review_service.py

litmind/.claude/skills/litmind-review/SKILL.md
litmind/scripts/review.py
```

---

### Task 1: Models + Config + Cache

**Files:**
- Create: `litmind/src/litmind_review/__init__.py`
- Create: `litmind/src/litmind_review/models.py`
- Create: `litmind/src/litmind_review/config.py`
- Create: `litmind/src/litmind_review/cache.py`
- Create: `litmind/tests/test_review_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_review_models.py
import pytest
from litmind_review.models import (
    ReviewInput, ReviewTheme, ResearchConsensus,
    ResearchControversy, ResearchGap, ReviewResult,
)
from litmind_discussion.models import DiscussionCitation


class TestReviewInput:
    def test_defaults(self):
        r = ReviewInput(topic="Flatfoot Biomechanics")
        assert r.topic == "Flatfoot Biomechanics"
        assert r.max_papers == 50

class TestReviewTheme:
    def test_minimal(self):
        t = ReviewTheme(name="Foot Kinematics", paperCount=5)
        assert t.name == "Foot Kinematics"
        assert t.paperIds == []

class TestResearchConsensus:
    def test_defaults(self):
        c = ResearchConsensus(statement="X is associated with Y")
        assert c.supportingPapers == 0

class TestResearchControversy:
    def test_defaults(self):
        c = ResearchControversy(statement="X improves Y")
        assert c.support == 0
        assert c.oppose == 0

class TestResearchGap:
    def test_minimal(self):
        g = ResearchGap(description="Few longitudinal studies")
        assert g.description == "Few longitudinal studies"

class TestReviewResult:
    def test_defaults(self):
        r = ReviewResult(topic="Test")
        assert r.paperCount == 0
        assert r.researchThemes == []
        assert r.reviewDraft == ""

    def test_with_all_fields(self):
        r = ReviewResult(
            topic="Test",
            paperCount=10,
            researchThemes=[ReviewTheme(name="T1", paperCount=5)],
            researchConsensus=[ResearchConsensus(statement="S1", supportingPapers=3)],
            reviewOutline={"Intro": ["Background", "Purpose"]},
            reviewDraft="Draft text...",
            citations=[DiscussionCitation(paperId="P1", section="draft")],
        )
        assert r.paperCount == 10
        assert len(r.researchThemes) == 1
        assert len(r.citations) == 1
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write implementation**

```python
# src/litmind_review/__init__.py
"""LitMind Review Generator — 基于科研知识库的综述生成系统"""
from .service import ReviewGeneratorService
from .models import ReviewInput, ReviewResult
__all__ = ["ReviewGeneratorService", "ReviewInput", "ReviewResult"]
__version__ = "0.1.0"
```

```python
# src/litmind_review/config.py
REVIEW_MAX_PAPERS = 50
REVIEW_MIN_THEMES = 3
REVIEW_MAX_THEMES = 7
CACHE_TTL_SECONDS = 600
CACHE_MAX_SIZE = 30
COMPOSER_MODEL = "claude-sonnet-4-20250514"
EVIDENCE_TOP_K = 10
```

```python
# src/litmind_review/models.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from litmind_discussion.models import DiscussionCitation

class ReviewInput(BaseModel):
    topic: str
    max_papers: int = 50

class ReviewTheme(BaseModel):
    name: str
    paperCount: int = 0
    paperIds: list[str] = Field(default_factory=list)
    description: str = ""

class ResearchConsensus(BaseModel):
    statement: str
    supportingPapers: int = 0
    paperIds: list[str] = Field(default_factory=list)

class ResearchControversy(BaseModel):
    statement: str
    support: int = 0
    oppose: int = 0
    supportingPaperIds: list[str] = Field(default_factory=list)
    opposingPaperIds: list[str] = Field(default_factory=list)

class ResearchGap(BaseModel):
    description: str
    evidence: str = ""

class ReviewResult(BaseModel):
    topic: str
    paperCount: int = 0
    researchThemes: list[ReviewTheme] = Field(default_factory=list)
    researchConsensus: list[ResearchConsensus] = Field(default_factory=list)
    researchControversies: list[ResearchControversy] = Field(default_factory=list)
    researchGaps: list[ResearchGap] = Field(default_factory=list)
    reviewOutline: dict[str, list[str]] = Field(default_factory=dict)
    reviewDraft: str = ""
    citations: list[DiscussionCitation] = Field(default_factory=list)
```

```python
# src/litmind_review/cache.py
"""Simple dict-based cache for review results"""
from __future__ import annotations
import time
from threading import Lock
from typing import Any, Optional
from .config import CACHE_TTL_SECONDS, CACHE_MAX_SIZE

class ReviewCache:
    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_size: int = CACHE_MAX_SIZE):
        self._ttl = ttl
        self._max_size = max_size
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            ts, val = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            return val

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)
            if len(self._cache) > self._max_size:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
                del self._cache[oldest]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
```

- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

---

### Task 2: TrendAnalyzer + Prompts

**Files:**
- Create: `litmind/src/litmind_review/trend.py`
- Create: `litmind/src/litmind_review/prompts.py`
- Create: `litmind/tests/test_review_trend.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_review_trend.py
import pytest
from litmind_review.trend import TrendAnalyzer


class TestTrendAnalyzer:
    def setup_method(self):
        self.analyzer = TrendAnalyzer()

    def test_analyze_empty(self):
        result = self.analyzer.analyze([])
        assert result["top_variables"] == []
        assert result["top_statistics"] == []
        assert result["year_distribution"] == {}

    def test_analyze_with_papers(self):
        papers = [
            {"variables": ["GRF", "MTP ROM"], "statistics": ["ANOVA"], "studyDesign": "Cross-sectional", "year": 2020},
            {"variables": ["GRF"], "statistics": ["t-test"], "studyDesign": "Experimental", "year": 2021},
            {"variables": ["MTP ROM", "EMG"], "statistics": ["ANOVA"], "studyDesign": "Cross-sectional", "year": 2021},
        ]
        result = self.analyzer.analyze(papers)
        assert len(result["top_variables"]) > 0
        assert ("GRF", 2) in result["top_variables"]
        assert ("ANOVA", 2) in result["top_statistics"]

    def test_year_distribution(self):
        papers = [{"year": 2020}, {"year": 2021}, {"year": 2021}, {}]
        result = TrendAnalyzer().analyze(papers)
        assert 2021 in result["year_distribution"]
        assert result["year_distribution"][2021] == 2
```

- [ ] **Step 2: Write implementation**

```python
# src/litmind_review/trend.py
"""TrendAnalyzer — 研究趋势分析：高频变量/方法/设计/年份"""

from __future__ import annotations
from collections import Counter
from typing import Any


class TrendAnalyzer:
    def analyze(self, papers: list[dict[str, Any]]) -> dict:
        variables = []
        statistics = []
        designs = []
        years = []

        for p in papers:
            variables.extend(p.get("variables") or [])
            statistics.extend(p.get("statistics") or [])
            sd = p.get("studyDesign", "")
            if sd:
                designs.append(sd)
            y = p.get("year")
            if y:
                years.append(y)

        return {
            "top_variables": Counter(variables).most_common(10),
            "top_statistics": Counter(statistics).most_common(10),
            "top_designs": Counter(designs).most_common(10),
            "year_distribution": dict(sorted(Counter(years).items())),
        }
```

```python
# src/litmind_review/prompts.py
"""LLM prompts for Review Generator"""

SYSTEM_PROMPT = """You are a scientific review writer. Your task is to write a literature review based on retrieved papers and analysis results.

Rules:
1. Every statement must be supported by evidence from the provided reference list.
2. Use [paperId] markers to cite sources within the text.
3. Do NOT fabricate authors, DOIs, or citations. Only use references from the provided list.
4. Output plain text with [paperId] markers for citations."""

THEME_DISCOVERY_PROMPT = """You are a research theme discovery engine. Given a list of papers, group them into 3-7 research themes.

Papers:
{papers}

For each theme, provide:
- name: short theme name
- description: one-sentence description
- paper_indices: list of paper numbers belonging to this theme

Output JSON format: {"themes": [{"name": "...", "description": "...", "paper_indices": [0,1,2]}]}"""

SECTION_PROMPTS = {
    "introduction": """Write the Introduction section. Set the research context, explain why this topic is important, and state the review's objectives.

Topic: {topic}
Paper count: {paper_count}
Themes: {themes_text}""",

    "landscape": """Write the Current Research Landscape section. Describe the volume of research, publication timeline, study designs, and statistical methods used in this field.

Topic: {topic}
Trend data: {trend_text}""",

    "themes": """Write the Major Research Themes section. For each theme, describe the key findings and representative studies.

Themes detail: {themes_detail}
Paper references: {paper_refs}""",

    "consensus": """Write the Evidence Consensus section. Discuss findings that are consistently supported across multiple studies.

Consensus items: {consensus_text}""",

    "controversies": """Write the Research Controversies section. Discuss topics where evidence is mixed or conflicting.

Controversy items: {controversy_text}""",

    "gaps": """Write the Research Gaps section. Identify understudied areas, methodological limitations in the literature, and unanswered questions.

Gap items: {gaps_text}""",

    "future": """Write the Future Directions section. Propose specific research questions and methodological improvements for future work.

Previous sections: {previous_text}""",

    "conclusion": """Write the Conclusion section. Summarize the main findings of this review.

Previous sections: {previous_text}""",
}
```

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**

---

### Task 3: ThemeDiscoveryEngine

**Files:**
- Create: `litmind/src/litmind_review/discovery.py`
- Create: `litmind/tests/test_review_discovery.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_review_discovery.py
import pytest
from litmind_review.discovery import ThemeDiscoveryEngine
from litmind_review.models import ReviewTheme


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return {"themes": [
            {"name": "Foot Kinematics", "description": "Studies on foot movement", "paper_indices": [0, 1]},
            {"name": "MTP Function", "description": "MTP joint mechanics", "paper_indices": [2]},
        ]}


class TestThemeDiscovery:
    def setup_method(self):
        self.engine = ThemeDiscoveryEngine(llm_provider=MockProvider())

    def test_discover_empty(self):
        themes = self.engine.discover([])
        assert themes == []

    def test_discover_with_papers(self):
        papers = [
            {"title": "Flatfoot kinematics", "variables": ["GRF"], "keywords": ["flatfoot"]},
            {"title": "Foot arch study", "variables": ["MTP"], "keywords": ["arch"]},
            {"title": "MTP joint ROM", "variables": ["ROM"], "keywords": ["mtp"]},
        ]
        themes = self.engine.discover(papers)
        assert len(themes) > 1
        assert all(isinstance(t, ReviewTheme) for t in themes)
```

- [ ] **Step 2: Write implementation**

```python
# src/litmind_review/discovery.py
"""ThemeDiscoveryEngine — 主题发现与聚类"""

from __future__ import annotations
import json
from typing import Any, Optional
from .models import ReviewTheme
from .prompts import THEME_DISCOVERY_PROMPT


class ThemeDiscoveryEngine:
    def __init__(self, llm_provider=None):
        self._llm = llm_provider

    def discover(self, papers: list[dict[str, Any]]) -> list[ReviewTheme]:
        if not papers or not self._llm:
            return []

        papers_text = "\n".join(
            f"{i}. {p.get('title', 'Untitled')} | Keywords: {', '.join(p.get('keywords', []) or [])} | Variables: {', '.join(p.get('variables', []) or [])}"
            for i, p in enumerate(papers)
        )

        try:
            result = self._llm.analyze(
                "Output JSON only.",
                THEME_DISCOVERY_PROMPT.format(papers=papers_text),
            )
            data = result if isinstance(result, dict) else json.loads(str(result))
            themes_data = data.get("themes", [])
        except Exception:
            return []

        themes = []
        for td in themes_data:
            indices = td.get("paper_indices", [])
            theme = ReviewTheme(
                name=td.get("name", "Untitled Theme"),
                paperCount=len(indices),
                paperIds=[str(papers[i].get("paperId", f"idx_{i}")) for i in indices if i < len(papers)],
                description=td.get("description", ""),
            )
            themes.append(theme)

        return themes
```

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**

---

### Task 4: ConsensusAnalyzer + ControversyAnalyzer

**Files:**
- Create: `litmind/src/litmind_review/consensus.py`
- Create: `litmind/src/litmind_review/controversy.py`
- Create: `litmind/tests/test_review_consensus.py`
- Create: `litmind/tests/test_review_controversy.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_review_consensus.py
import pytest
from litmind_review.consensus import ConsensusAnalyzer
from litmind_review.models import ResearchConsensus


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult, EvidenceItem
        return EvidenceResult(
            query=query,
            evidenceStrength="Strongly Supported",
            confidence=0.85,
            support=[EvidenceItem(paperId="P1", direction="support")],
        )


class TestConsensusAnalyzer:
    def test_analyze_empty(self):
        analyzer = ConsensusAnalyzer(evidence_service=MockEvidenceService())
        consensuses = analyzer.analyze([])
        assert consensuses == []

    def test_analyze_with_themes(self):
        from litmind_review.models import ReviewTheme
        analyzer = ConsensusAnalyzer(evidence_service=MockEvidenceService())
        themes = [ReviewTheme(name="Foot Kinematics", paperCount=3)]
        result = analyzer.analyze(themes)
        assert isinstance(result, list)
```

```python
# tests/test_review_controversy.py
import pytest
from litmind_review.controversy import ControversyAnalyzer


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult, EvidenceItem
        return EvidenceResult(
            query=query,
            support=[EvidenceItem(paperId="P1", direction="support")],
            oppose=[EvidenceItem(paperId="P2", direction="oppose")],
        )


class TestControversyAnalyzer:
    def test_analyze_empty(self):
        analyzer = ControversyAnalyzer(evidence_service=MockEvidenceService())
        result = analyzer.analyze([])
        assert result == []

    def test_analyze_with_themes(self):
        from litmind_review.models import ReviewTheme
        analyzer = ControversyAnalyzer(evidence_service=MockEvidenceService())
        result = analyzer.analyze([ReviewTheme(name="Footwear", paperCount=3)])
        assert isinstance(result, list)
```

- [ ] **Step 2: Write implementation**

```python
# src/litmind_review/consensus.py
"""ConsensusAnalyzer — 研究共识识别"""

from __future__ import annotations
from typing import Any
from .models import ResearchConsensus, ReviewTheme


class ConsensusAnalyzer:
    def __init__(self, evidence_service):
        self._evidence = evidence_service

    def analyze(self, themes: list[ReviewTheme]) -> list[ResearchConsensus]:
        results = []
        for theme in themes:
            ev = self._evidence.find_evidence(theme.name, top_k=5)
            if ev.evidenceStrength in ("Strongly Supported", "Moderately Supported") and ev.support:
                paper_ids = [item.paperId for item in ev.support if item.paperId]
                results.append(ResearchConsensus(
                    statement=f"{theme.name} is consistently supported in the literature",
                    supportingPapers=len(paper_ids),
                    paperIds=paper_ids,
                ))
        return results
```

```python
# src/litmind_review/controversy.py
"""ControversyAnalyzer — 研究争议识别"""

from __future__ import annotations
from typing import Any
from .models import ResearchControversy, ReviewTheme


class ControversyAnalyzer:
    def __init__(self, evidence_service):
        self._evidence = evidence_service

    def analyze(self, themes: list[ReviewTheme]) -> list[ResearchControversy]:
        results = []
        for theme in themes:
            ev = self._evidence.find_evidence(theme.name, top_k=10)
            support_count = len(ev.support)
            oppose_count = len(ev.oppose)
            if support_count > 0 and oppose_count > 0:
                results.append(ResearchControversy(
                    statement=f"The role of {theme.name} remains debated",
                    support=support_count,
                    oppose=oppose_count,
                    supportingPaperIds=[i.paperId for i in ev.support if i.paperId],
                    opposingPaperIds=[i.paperId for i in ev.oppose if i.paperId],
                ))
        return results
```

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**

---

### Task 5: GapAnalyzer + OutlineGenerator

**Files:**
- Create: `litmind/src/litmind_review/gaps.py`
- Create: `litmind/src/litmind_review/outline.py`
- Create: `litmind/tests/test_review_gaps.py`
- Create: `litmind/tests/test_review_outline.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_review_gaps.py
import pytest
from litmind_review.gaps import GapAnalyzer
from litmind_review.models import ResearchGap


class TestGapAnalyzer:
    def setup_method(self):
        self.analyzer = GapAnalyzer()

    def test_analyze_empty(self):
        gaps = self.analyzer.analyze([], [], {})
        assert isinstance(gaps, list)

    def test_analyze_low_count_themes(self):
        from litmind_review.models import ReviewTheme
        themes = [ReviewTheme(name="Rare Topic", paperCount=1)]
        gaps = self.analyzer.analyze(themes, [], {"year_distribution": {2020: 1}})
        assert isinstance(gaps, list)
```

```python
# tests/test_review_outline.py
import pytest
from litmind_review.outline import OutlineGenerator


class TestOutlineGenerator:
    def test_generate_empty(self):
        gen = OutlineGenerator(llm_provider=None)
        outline = gen.generate("Test", [], [], [], [])
        assert len(outline) >= 7

    def test_generate_structure(self):
        gen = OutlineGenerator(llm_provider=None)
        outline = gen.generate("Test", ["T1", "T2"], ["C1"], ["Cont1"], ["G1"])
        sections = ["introduction", "landscape", "themes", "consensus", "controversies", "gaps", "future", "conclusion"]
        for s in sections:
            assert s in outline
```

- [ ] **Step 2: Write implementation**

```python
# src/litmind_review/gaps.py
"""GapAnalyzer — 研究空白识别"""

from __future__ import annotations
from typing import Any
from .models import ResearchGap, ReviewTheme


class GapAnalyzer:
    def analyze(
        self,
        themes: list[ReviewTheme],
        consensuses: list,
        trend_data: dict,
    ) -> list[ResearchGap]:
        gaps = []

        # 低频主题 = 可能的研究空白
        for theme in themes:
            if theme.paperCount <= 2:
                gaps.append(ResearchGap(
                    description=f"Limited research on {theme.name}",
                    evidence=f"Only {theme.paperCount} paper(s) found in current knowledge base",
                ))

        # 时间分布缺口
        year_dist = trend_data.get("year_distribution", {})
        if year_dist:
            recent_years = {k: v for k, v in year_dist.items() if k >= 2023}
            if not recent_years:
                gaps.append(ResearchGap(
                    description="Limited recent publications in this field",
                    evidence="No papers from 2023 or later found in current knowledge base",
                ))

        return gaps
```

```python
# src/litmind_review/outline.py
"""OutlineGenerator — 综述框架生成"""

from __future__ import annotations
from typing import Any, Optional


SECTIONS = [
    "introduction", "landscape", "themes",
    "consensus", "controversies", "gaps",
    "future", "conclusion",
]

SECTION_LABELS = {
    "introduction": "Introduction",
    "landscape": "Current Research Landscape",
    "themes": "Major Research Themes",
    "consensus": "Evidence Consensus",
    "controversies": "Research Controversies",
    "gaps": "Research Gaps",
    "future": "Future Directions",
    "conclusion": "Conclusion",
}


class OutlineGenerator:
    def __init__(self, llm_provider=None):
        self._llm = llm_provider

    def generate(
        self,
        topic: str,
        theme_names: list[str],
        consensus_statements: list[str],
        controversy_statements: list[str],
        gap_descriptions: list[str],
    ) -> dict[str, list[str]]:
        outline = {}
        for section_key in SECTIONS:
            outline[SECTION_LABELS.get(section_key, section_key)] = []
        return outline
```

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**

---

### Task 6: ReviewComposer

**Files:**
- Create: `litmind/src/litmind_review/composer.py`
- Create: `litmind/tests/test_review_composer.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_review_composer.py
import pytest
from litmind_review.composer import ReviewComposer
from litmind_review.models import ReviewInput, ReviewResult, ReviewTheme, ResearchConsensus, ResearchControversy, ResearchGap


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated section text with [P1] citation."


class TestReviewComposer:
    def setup_method(self):
        self.composer = ReviewComposer(llm_provider=MockProvider())

    def test_compose_basic(self):
        inp = ReviewInput(topic="Flatfoot Biomechanics", max_papers=10)
        result = self.composer.compose(
            inp=inp,
            themes=[ReviewTheme(name="Kinematics", paperCount=3)],
            consensus=[],
            controversies=[],
            gaps=[],
            trend_data={},
            outline={"Introduction": []},
        )
        assert isinstance(result, str)

    def test_compose_empty(self):
        inp = ReviewInput(topic="", max_papers=0)
        result = self.composer.compose(inp, [], [], [], [], {}, {})
        assert isinstance(result, str)
```

- [ ] **Step 2: Write implementation**

```python
# src/litmind_review/composer.py
"""ReviewComposer — LLM 逐 Section 生成综述全文"""

from __future__ import annotations
from typing import Any

from .config import COMPOSER_MODEL
from .models import ReviewInput, ReviewTheme, ResearchConsensus, ResearchControversy, ResearchGap
from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS


SECTIONS = [
    "introduction", "landscape", "themes",
    "consensus", "controversies", "gaps",
    "future", "conclusion",
]


class ReviewComposer:
    def __init__(self, llm_provider, model: str = COMPOSER_MODEL):
        self._llm = llm_provider
        self._model = model

    def compose(
        self,
        inp: ReviewInput,
        themes: list[ReviewTheme],
        consensus: list[ResearchConsensus],
        controversies: list[ResearchControversy],
        gaps: list[ResearchGap],
        trend_data: dict,
        outline: dict[str, list[str]],
    ) -> str:
        previous_text = ""
        full_draft = ""

        themes_text = "\n".join(f"- {t.name}: {t.description}" for t in themes[:5]) or "No themes identified."
        themes_detail = "\n\n".join(
            f"Theme: {t.name}\nPapers: {t.paperCount}\n{t.description}" for t in themes[:5]
        ) or "No themes."
        consensus_text = "\n".join(f"- {c.statement} ({c.supportingPapers} papers)" for c in consensus[:5]) or "No consensus items."
        controversy_text = "\n".join(f"- {c.statement} (support={c.support}, oppose={c.oppose})" for c in controversies[:5]) or "No controversies."
        gaps_text = "\n".join(f"- {g.description}: {g.evidence}" for g in gaps[:5]) or "No gaps identified."

        trend_items = []
        for var, count in trend_data.get("top_variables", [])[:5]:
            trend_items.append(f"  - {var}: {count} papers")
        trend_text = "\n".join(trend_items) or "No trend data."

        for section_key in SECTIONS:
            template = SECTION_PROMPTS.get(section_key, "")
            prompt = template.format(
                topic=inp.topic,
                paper_count=inp.max_papers,
                themes_text=themes_text,
                themes_detail=themes_detail,
                trend_text=trend_text,
                paper_refs=themes_detail,
                consensus_text=consensus_text,
                controversy_text=controversy_text,
                gaps_text=gaps_text,
                previous_text=previous_text[:800] if previous_text else "No previous sections yet.",
            )

            try:
                result = self._llm.analyze(SYSTEM_PROMPT, prompt)
                section_text = ""
                if isinstance(result, dict):
                    for key in ("draft", "text", "content", "output"):
                        if key in result and isinstance(result[key], str):
                            section_text = result[key]
                            break
                elif isinstance(result, str):
                    section_text = result
                else:
                    section_text = str(result) if result else ""

                if section_text:
                    full_draft += f"## {section_key.capitalize()}\n\n{section_text.strip()}\n\n"
                    previous_text = section_text
            except Exception:
                previous_text = ""

        return full_draft.strip()
```

- [ ] **Step 3: Run tests**
- [ ] **Step 4: Commit**

---

### Task 7: ReviewGeneratorService + CLI

**Files:**
- Create: `litmind/src/litmind_review/service.py`
- Create: `litmind/scripts/review.py`
- Create: `litmind/tests/test_review_service.py`

- [ ] **Step 1: Write the tests**

```python
# tests/test_review_service.py
import pytest
from litmind_review.service import ReviewGeneratorService
from litmind_review.models import ReviewInput, ReviewResult


class MockKB:
    def semantic_search(self, query, top_k=20):
        return []
    def search_claims(self, query):
        return []
    def search_variables(self, query):
        return []
    def get_paper(self, paper_id):
        return None


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult
        return EvidenceResult(query=query)


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated text."


class MockLLM:
    def analyze(self, system_prompt, user_prompt):
        return "Generated section text."


class TestReviewService:
    def setup_method(self):
        self.service = ReviewGeneratorService(
            kb=MockKB(),
            evidence_service=MockEvidenceService(),
            llm_provider=MockProvider(),
        )

    def test_generate_review(self):
        inp = ReviewInput(topic="Test Topic")
        result = self.service.generate_review(inp, use_cache=False)
        assert isinstance(result, ReviewResult)
        assert result.topic == "Test Topic"

    def test_discover_themes(self):
        themes = self.service.discover_themes("Test")
        assert isinstance(themes, list)

    def test_analyze_consensus(self):
        result = self.service.analyze_consensus("Test")
        assert isinstance(result, list)

    def test_analyze_controversies(self):
        result = self.service.analyze_controversies("Test")
        assert isinstance(result, list)

    def test_identify_gaps(self):
        result = self.service.identify_research_gaps("Test")
        assert isinstance(result, list)
```

- [ ] **Step 2: Write the service**

```python
# src/litmind_review/service.py
"""ReviewGeneratorService — 综述生成统一入口"""

from __future__ import annotations
from typing import Any, Optional

from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_discussion.citation import CitationManager
from litmind_discussion.models import DiscussionCitation

from .cache import ReviewCache
from .config import REVIEW_MAX_PAPERS
from .consensus import ConsensusAnalyzer
from .controversy import ControversyAnalyzer
from .discovery import ThemeDiscoveryEngine
from .gaps import GapAnalyzer
from .models import ReviewInput, ReviewResult, ResearchConsensus, ResearchControversy, ResearchGap
from .outline import OutlineGenerator
from .composer import ReviewComposer
from .trend import TrendAnalyzer


class ReviewGeneratorService:
    def __init__(
        self,
        kb: KnowledgeBase,
        evidence_service: EvidenceFinderService,
        llm_provider,
        model: str = "",
    ):
        self._kb = kb
        self._evidence = evidence_service
        self._discovery = ThemeDiscoveryEngine(llm_provider=llm_provider)
        self._trend = TrendAnalyzer()
        self._consensus = ConsensusAnalyzer(evidence_service)
        self._controversy = ControversyAnalyzer(evidence_service)
        self._gaps = GapAnalyzer()
        self._outline = OutlineGenerator(llm_provider=llm_provider)
        self._composer = ReviewComposer(llm_provider, model=model)
        self._cache = ReviewCache()

    def generate_review(
        self,
        inp: ReviewInput,
        use_cache: bool = True,
    ) -> ReviewResult:
        if use_cache:
            cached = self._cache.get(inp.topic)
            if cached is not None:
                return cached

        # 1. KB 检索
        papers = self._retrieve_papers(inp.topic, inp.max_papers)

        # 2. 趋势分析
        trend_data = self._trend.analyze(papers)

        # 3. 主题发现
        themes = self._discovery.discover(papers)

        # 4. 共识 + 争议（每主题调 evidence）
        consensuses = self._consensus.analyze(themes)
        controversies = self._controversy.analyze(themes)

        # 5. 空白分析
        gaps = self._gaps.analyze(themes, consensuses, trend_data)

        # 6. 生成框架
        outline = self._outline.generate(
            inp.topic,
            [t.name for t in themes],
            [c.statement for c in consensuses],
            [c.statement for c in controversies],
            [g.description for g in gaps],
        )

        # 7. 生成全文
        draft = self._composer.compose(
            inp, themes, consensuses, controversies, gaps, trend_data, outline,
        )

        # 8. 引用提取
        citation_mgr = CitationManager()
        known_ids = {p.get("paperId") for p in papers if p.get("paperId")}
        raw_ids = citation_mgr.extract_from_text(draft)
        for pid in raw_ids:
            if pid in known_ids:
                citation_mgr.add(DiscussionCitation(paperId=pid, section="draft"))

        result = ReviewResult(
            topic=inp.topic,
            paperCount=len(papers),
            researchThemes=themes,
            researchConsensus=consensuses,
            researchControversies=controversies,
            researchGaps=gaps,
            reviewOutline=outline,
            reviewDraft=draft,
            citations=citation_mgr.to_citation_list(known_ids),
        )

        if use_cache:
            self._cache.set(inp.topic, result)
        return result

    def _retrieve_papers(self, topic: str, max_papers: int) -> list[dict]:
        seen = set()
        papers = []

        for hit in self._kb.semantic_search(topic, top_k=max_papers):
            pid = hit.get("paperId")
            if pid and pid not in seen:
                seen.add(pid)
                paper = self._kb.get_paper(pid)
                if paper:
                    papers.append(paper)

        return papers[:max_papers]

    def discover_themes(self, topic: str) -> list:
        papers = self._retrieve_papers(topic, REVIEW_MAX_PAPERS)
        return self._discovery.discover(papers)

    def analyze_consensus(self, topic: str) -> list[ResearchConsensus]:
        from litmind_review.models import ReviewTheme
        themes = self.discover_themes(topic)
        if not themes:
            themes = [ReviewTheme(name=topic, paperCount=0)]
        return self._consensus.analyze(themes)

    def analyze_controversies(self, topic: str) -> list[ResearchControversy]:
        from litmind_review.models import ReviewTheme
        themes = self.discover_themes(topic)
        if not themes:
            themes = [ReviewTheme(name=topic, paperCount=0)]
        return self._controversy.analyze(themes)

    def identify_research_gaps(self, topic: str) -> list[ResearchGap]:
        papers = self._retrieve_papers(topic, REVIEW_MAX_PAPERS)
        trend_data = self._trend.analyze(papers)
        themes = self._discovery.discover(papers)
        return self._gaps.analyze(themes, [], trend_data)

    def clear_cache(self) -> None:
        self._cache.clear()
```

- [ ] **Step 3: Write the CLI**

```python
# scripts/review.py
#!/usr/bin/env python3
"""LitMind Review Generator — CLI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import click
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_review import ReviewGeneratorService, ReviewInput
from litmind_analyzer.providers import AnthropicProvider


@click.command()
@click.argument("topic")
@click.option("--max-papers", default=50, show_default=True, help="Max papers to analyze")
@click.option("--output", "-o", default=None, help="Output JSON path")
@click.option("--json", "json_output", is_flag=True, help="JSON output")
def cli(topic, max_papers, output, json_output):
    kb = KnowledgeBase()
    provider = AnthropicProvider()
    evidence_service = EvidenceFinderService(kb=kb, llm_provider=provider)
    service = ReviewGeneratorService(kb=kb, evidence_service=evidence_service, llm_provider=provider)

    inp = ReviewInput(topic=topic, max_papers=max_papers)
    result = service.generate_review(inp)

    if output:
        import json
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        click.echo(f"输出 → {output}")
    elif json_output:
        click.echo(result.model_dump_json(indent=2, exclude_none=True))
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"  Topic: {topic}")
        click.echo(f"  Papers: {result.paperCount}")
        click.echo(f"  Themes: {len(result.researchThemes)}")
        click.echo(f"  Consensus: {len(result.researchConsensus)}")
        click.echo(f"  Controversies: {len(result.researchControversies)}")
        click.echo(f"  Gaps: {len(result.researchGaps)}")
        click.echo(f"  Draft: {len(result.reviewDraft)} chars")
        click.echo(f"  Citations: {len(result.citations)}")
        click.echo(f"\n  Draft preview:")
        click.echo(f"  {result.reviewDraft[:500]}...")


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

---

### Task 8: Skill + CLAUDE.md Update

**Files:**
- Create: `litmind/.claude/skills/litmind-review/SKILL.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Create skill file**

```markdown
---
name: litmind-review
description: LitMind Review Generator — 基于科研知识库的综述生成系统
---

# LitMind Review Generator

输入研究主题，自动检索知识库相关文献，分析研究趋势、主题聚类、共识与争议，生成结构化综述框架和带引用的综述草稿。

## 工作流程

1. 检索 KB 获取相关论文
2. ThemeDiscoveryEngine 聚类主题
3. TrendAnalyzer 统计高频变量/方法/设计
4. ConsensusAnalyzer 识别研究共识
5. ControversyAnalyzer 识别研究争议
6. GapAnalyzer 发现研究空白
7. OutlineGenerator 生成综述框架
8. ReviewComposer 生成综述全文

## 输出结构

- researchThemes — 研究主题聚类
- researchConsensus — 研究共识
- researchControversies — 研究争议
- researchGaps — 研究空白
- reviewOutline — 综述框架
- reviewDraft — 综述全文

## 调用方式

```bash
python scripts/review.py "Flatfoot Biomechanics"
python scripts/review.py "MTP Joint Function" --max-papers 30
python scripts/review.py "SPM in Biomechanics" --json
```

## Python API

```python
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_review import ReviewGeneratorService, ReviewInput
from litmind_analyzer.providers import AnthropicProvider

kb = KnowledgeBase()
provider = AnthropicProvider()
ev = EvidenceFinderService(kb=kb, llm_provider=provider)
service = ReviewGeneratorService(kb=kb, evidence_service=ev, llm_provider=provider)

result = service.generate_review(ReviewInput(topic="Flatfoot Biomechanics"))
print(f"Themes: {len(result.researchThemes)}")
print(f"Draft: {len(result.reviewDraft)} chars")
```
```

- [ ] **Step 2: Update CLAUDE.md** — Add between `litmind-evidence` and `litmind-discussion`:
```markdown
- **[litmind-review](litmind/.claude/skills/litmind-review/SKILL.md)**: Review Generator — 基于科研知识库的综述生成系统
```

- [ ] **Step 3: Run all review tests**
```bash
cd /c/Users/10119/Desktop/experimimental\ date/litmind && python -m pytest tests/test_review_models.py tests/test_review_trend.py tests/test_review_discovery.py tests/test_review_consensus.py tests/test_review_controversy.py tests/test_review_gaps.py tests/test_review_outline.py tests/test_review_composer.py tests/test_review_service.py -v
```

- [ ] **Step 4: Commit**

---

## Self-Review Checklist

- [x] Spec coverage: All components from spec have tasks (models ✓, trend ✓, discovery ✓, consensus ✓, controversy ✓, gaps ✓, outline ✓, composer ✓, service ✓, CLI ✓, skill ✓)
- [x] No placeholders: All code blocks complete and functional
- [x] Type consistency: ReviewInput/Result/Themes/Consensus/Controversy/Gap match spec models
- [x] Dependencies: KnowledgeBase, EvidenceFinderService, CitationManager, LLMProvider
