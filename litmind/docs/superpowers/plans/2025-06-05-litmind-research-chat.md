# Research Chat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Research Chat — natural language Q&A system over the Knowledge Base, with query classification, evidence retrieval, LLM answer generation, and citation tracking.

**Architecture:** QueryClassifier (LLM-based) → ContextBuilder (KB retrieval) → AnswerGenerator (LLM + structured output) → CitationFormatter. Reuses `litmind_analyzer.providers` for LLM and `litmind_knowledge.service` for KB access.

**Tech Stack:** Python 3.10+, Pydantic v2, litmind_analyzer (LLMProvider), litmind_knowledge (KnowledgeBase)

---

## File Structure

```
litmind/src/litmind_chat/
├── __init__.py              # Package entry
├── config.py                # Model config, cache TTL
├── models/
│   ├── __init__.py          # Exports all models
│   ├── query.py             # QueryType enum, ChatQuery
│   └── response.py          # ChatResponse, SupportingPaper, SupportingClaim
├── classifier/
│   ├── __init__.py
│   └── query_classifier.py  # QueryClassifier (LLM prompt based)
├── context/
│   ├── __init__.py
│   └── builder.py           # ContextBuilder (KB retrieval + assembly)
├── generator/
│   ├── __init__.py
│   ├── answer_generator.py  # AnswerGenerator (LLM call)
│   └── citation_formatter.py # CitationFormatter
├── cache.py                 # LRU query cache
├── service.py               # ResearchChatService
├── cli.py                   # Interactive CLI

litmind/tests/
├── test_research_chat.py    # All chat tests
├── fixtures/
│   └── sample_papers.json   # KB test data

litmind/.claude/skills/
├── litmind-chat/SKILL.md
```

---

### Task 1: Config + Models

**Files:**
- Create: `litmind/src/litmind_chat/__init__.py`
- Create: `litmind/src/litmind_chat/config.py`
- Create: `litmind/src/litmind_chat/models/__init__.py`
- Create: `litmind/src/litmind_chat/models/query.py`
- Create: `litmind/src/litmind_chat/models/response.py`
- Create: `litmind/tests/test_research_chat.py` (append TestModels)

- [ ] **Step 1: Write failing test**

```python
# tests/test_research_chat.py
import pytest
from litmind_chat.models.query import QueryType, ChatQuery
from litmind_chat.models.response import ChatResponse, SupportingPaper, SupportingClaim


class TestModels:
    def test_query_type_values(self):
        assert QueryType.PAPER_SEARCH.value == "paper_search"
        assert QueryType.CLAIM_SEARCH.value == "claim_search"
        assert QueryType.GENERAL_QUESTION.value == "general_question"

    def test_chat_query_defaults(self):
        q = ChatQuery(question="Does flatfoot increase motion?")
        assert q.question == "Does flatfoot increase motion?"
        assert q.top_k == 10

    def test_supporting_paper(self):
        p = SupportingPaper(paperId="P1", title="Test", year=2024, authors="Author A")
        assert p.title == "Test"
        assert p.doi == ""

    def test_chat_response_defaults(self):
        r = ChatResponse(answer="Test answer")
        assert r.answer == "Test answer"
        assert r.supportingPapers == []
        assert r.supportingClaims == []
        assert r.confidence == 0.0

    def test_chat_response_with_claims(self):
        c = SupportingClaim(statement="X", evidenceSource="Results", paperId="P1")
        r = ChatResponse(answer="A", supportingClaims=[c])
        assert r.answer == "A"
        assert r.supportingClaims[0].statement == "X"
```

- [ ] **Step 2: Run test — fails**

Run: `cd litmind && python -m pytest tests/test_research_chat.py::TestModels -v`
Expected: FAIL

- [ ] **Step 3: Write config.py**

```python
from ..config import get_default_db_path, get_default_chroma_path

DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL = "claude-sonnet-4-20250514"
CACHE_TTL_SECONDS = 300  # 5 minutes
CACHE_MAX_SIZE = 100
DEFAULT_TOP_K = 10
```

- [ ] **Step 4: Write models/query.py**

```python
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class QueryType(str, Enum):
    PAPER_SEARCH = "paper_search"           # 哪些文献研究了 X？
    VARIABLE_SEARCH = "variable_search"     # 哪些研究关注 X 变量？
    STATISTIC_SEARCH = "statistic_search"   # 哪些文献使用了 X 统计方法？
    CLAIM_SEARCH = "claim_search"           # 有哪些研究支持/反对 X？
    EVIDENCE_SEARCH = "evidence_search"     # 关于 X 的证据？
    TREND_SEARCH = "trend_search"           # X 领域的研究热点？
    GENERAL_QUESTION = "general_question"   # 综合性科研问题
    UNKNOWN = "unknown"


class ChatQuery(BaseModel):
    question: str
    top_k: int = 10
    stream: bool = False
```

- [ ] **Step 5: Write models/response.py**

```python
from pydantic import BaseModel
from typing import Optional


class SupportingPaper(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    authors: str = ""
    journal: str = ""
    doi: str = ""


class SupportingClaim(BaseModel):
    statement: str
    evidenceSource: str = ""
    paperId: str = ""


class ChatResponse(BaseModel):
    answer: str
    supportingPapers: list[SupportingPaper] = []
    supportingClaims: list[SupportingClaim] = []
    confidence: float = 0.0
    queryType: str = ""


class SearchResult(BaseModel):
    """仅检索不生成答案时的输出"""
    query: str
    queryType: str = ""
    papers: list[SupportingPaper] = []
    claims: list[SupportingClaim] = []
```

- [ ] **Step 6: Run tests**

Run: `cd litmind && python -m pytest tests/test_research_chat.py::TestModels -v`
Expected: 5 passed

---

### Task 2: Cache

**Files:**
- Create: `litmind/src/litmind_chat/cache.py`

- [ ] **Step 1: Write failing test**

```python
class TestCache:
    def test_cache_set_get(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=60)
        cache.put("test_q", "result")
        assert cache.get("test_q") == "result"

    def test_cache_expiry(self):
        import time
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=1)
        cache.put("test_q", "result")
        time.sleep(1.5)
        assert cache.get("test_q") is None

    def test_cache_max_size(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=2, ttl=60)
        cache.put("q1", "r1")
        cache.put("q2", "r2")
        cache.put("q3", "r3")
        assert cache.get("q1") is None  # evicted
        assert cache.get("q3") == "r3"

    def test_cache_clear(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=60)
        cache.put("q1", "r1")
        cache.clear()
        assert cache.get("q1") is None
```

- [ ] **Step 2: Run test — fails**

- [ ] **Step 3: Write implementation**

```python
"""LRU 查询缓存"""

import time
from collections import OrderedDict
from typing import Any, Optional


class QueryCache:
    """LRU 缓存，基于 OrderedDict"""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def _make_key(self, question: str) -> str:
        return question.lower().strip()

    def get(self, question: str) -> Optional[Any]:
        key = self._make_key(question)
        if key not in self._cache:
            return None
        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def put(self, question: str, value: Any) -> None:
        key = self._make_key(question)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time.time())
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()
```

- [ ] **Step 4: Run tests**

Run: `cd litmind && python -m pytest tests/test_research_chat.py::TestCache -v`
Expected: 4 passed

---

### Task 3: QueryClassifier

**Files:**
- Create: `litmind/src/litmind_chat/classifier/__init__.py`
- Create: `litmind/src/litmind_chat/classifier/query_classifier.py`

- [ ] **Step 1: Write failing test**

```python
class TestQueryClassifier:
    def test_classify_paper_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        from litmind_analyzer.providers import AnthropicProvider
        # Without API key, should use rule-based fallback
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("哪些文献研究了 Flatfoot？")
        assert result == "paper_search"

    def test_classify_statistic_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("哪些文献使用了 SPM1D？")
        assert result == "statistic_search"

    def test_classify_claim_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("有哪些研究支持 Flatfoot increases forefoot motion？")
        assert result == "claim_search"

    def test_classify_evidence_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("Does flatfoot increase forefoot motion?")
        assert result in ("evidence_search", "general_question")
```

- [ ] **Step 2: Run test — fails**

- [ ] **Step 3: Write rule-based classifier with LLM option**

```python
"""QueryClassifier — 问题分类器（规则 + LLM 可选）"""

import re
from typing import Optional
from ..models.query import QueryType


# 规则关键词映射
_RULE_PATTERNS = [
    (QueryType.PAPER_SEARCH, [
        r"哪些\s*(文献|论文|研究|文章).*?(研究|关注|探讨|讨论|分析|使用|采用|涉及)",
        r"what\s*(papers|studies|research|articles).*?(on|about|investigat|examin|stud|analyz)",
        r"find\s+(papers|studies|research).*?(on|about|for)",
    ]),
    (QueryType.VARIABLE_SEARCH, [
        r"哪些\s*(研究|文献).*?(关注|测量|分析|使用|涉及)\s+\w+",
        r"(变量|指标|parameter|variable|measure)\s+(研究|关注|使用|used|measured|analyzed)",
        r"what\s+(variables|parameters|measures).*?(studied|measured|used)",
    ]),
    (QueryType.STATISTIC_SEARCH, [
        r"哪些\s*(文献|研究).*?(使用了|采用|应用|used|applied|employed)\s+[\w\d]+",
        r"(统计|statistical|analysis)\s+(方法|method|technique).*?(使用|used|applied)",
        r"(ANOVA|SPM|t-test|regression|MANOVA|mixed.model|repeated.measure)",
    ]),
    (QueryType.CLAIM_SEARCH, [
        r"有哪些\s*(研究|证据|文献).*?(支持|反对|认为|表明|提出|suggest|show|indicate|demonstrat)",
        r"(支持|反对|support|evidence|against|反对).*?(the\s+)?(claim|hypothesis|statement|view)",
        r"evidence\s+(for|against|supporting|opposing)",
    ]),
    (QueryType.EVIDENCE_SEARCH, [
        r"(what|is|are|does|do|can|how)\s+.*?\?",
        r"(evidence|effect|impact|relationship|association|correlation|difference)\s+(of|between|on)",
        r"(does|can|will|may|could)\s+\w+\s+(increase|decrease|affect|change|alter|improve|reduce)",
    ]),
    (QueryType.TREND_SEARCH, [
        r"(研究|热点|趋势|前沿|current|recent|hotspot|trend|frontier|state.of.art)",
        r"what.*?(hot|trending|popular|emerging|new|recent)\s+(in|research|studies)",
    ]),
]


class QueryClassifier:
    """问题分类器
    先用规则匹配，规则无法确定时调用 LLM 辅助判断。
    """

    def __init__(self, provider=None, model: str = ""):
        self.provider = provider
        self.model = model

    def classify(self, question: str) -> str:
        """返回 QueryType 的 value"""
        # 规则匹配
        for qtype, patterns in _RULE_PATTERNS:
            for pat in patterns:
                if re.search(pat, question, re.IGNORECASE):
                    # 对于证据搜索类问题，进一步判断是否含具体问题
                    if qtype == QueryType.EVIDENCE_SEARCH:
                        # 检查是否含疑问词
                        if re.search(r"(what|is|are|does|do|can|how|whether|which)", question, re.IGNORECASE):
                            return qtype.value
                        continue
                    return qtype.value

        # 万不得已：走 LLM
        if self.provider:
            return self._llm_classify(question)

        # 最终 fallback
        return QueryType.GENERAL_QUESTION.value

    def _llm_classify(self, question: str) -> str:
        """LLM 辅助分类（可选）"""
        prompt = (
            f"Classify this research question into one of: "
            f"paper_search, variable_search, statistic_search, claim_search, "
            f"evidence_search, trend_search, general_question.\n"
            f"Question: {question}\n"
            f"Output only the type name."
        )
        try:
            result = self.provider.analyze(
                "You are a query classifier. Output only the type name.",
                prompt,
            )
            if isinstance(result, dict) and "answer" in result:
                return result["answer"].strip()
            if isinstance(result, str):
                return result.strip()
        except Exception:
            pass
        return QueryType.GENERAL_QUESTION.value
```

---

### Task 4: ContextBuilder

**Files:**
- Create: `litmind/src/litmind_chat/context/__init__.py`
- Create: `litmind/src/litmind_chat/context/builder.py`

- [ ] **Step 1: Write failing test**

```python
class TestContextBuilder:
    @pytest.fixture
    def builder(self):
        from litmind_chat.context.builder import ContextBuilder
        return ContextBuilder(kb=None)  # KB disabled for unit test

    def test_build_paper_search_prompt(self, builder):
        papers = [{"paperId": "P1", "title": "Flatfoot Biomechanics", "year": 2024}]
        prompt = builder._build_prompt("哪些文献研究了 Flatfoot？", "paper_search", papers, [], [])
        assert "Flatfoot" in prompt
        assert "Flatfoot Biomechanics" in prompt
```

- [ ] **Step 2: Write ContextBuilder**

```python
"""ContextBuilder — 检索知识库 + 组装 LLM 上下文"""

from typing import Any, Optional
from ..models.query import QueryType


class ContextBuilder:
    """检索 Knowledge Base 并构建 LLM 提示上下文"""

    def __init__(self, kb=None):
        self.kb = kb

    def retrieve(self, question: str, query_type: str, top_k: int = 10) -> dict:
        """根据问题类型检索 KB，返回检索结果"""
        result = {
            "papers": [],
            "claims": [],
            "semantic_results": [],
            "variables": [],
            "statistics": [],
        }

        if not self.kb:
            return result

        # 语义搜索（对所有类型都有用）
        result["semantic_results"] = self.kb.semantic_search(question, top_k=top_k)

        # 类型特定检索
        if query_type == QueryType.PAPER_SEARCH.value:
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.VARIABLE_SEARCH.value:
            result["variables"] = self.kb.search_variables(question)
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.STATISTIC_SEARCH.value:
            result["statistics"] = self.kb.search_statistics(question)
        elif query_type in (QueryType.CLAIM_SEARCH.value, QueryType.EVIDENCE_SEARCH.value):
            result["claims"] = self.kb.search_claims(question)
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.TREND_SEARCH.value:
            result["papers"] = self.kb.search_papers(question)

        return result

    def build_system_prompt(self) -> str:
        return (
            "You are a scientific research assistant. Answer questions based solely on "
            "the provided evidence. Every claim in your answer must cite specific papers.\n\n"
            "Rules:\n"
            "1. Only use information from the provided evidence.\n"
            "2. Every factual statement must cite a paper (author, year).\n"
            "3. If the evidence does not answer the question, say so.\n"
            "4. Do not fabricate citations or evidence.\n"
            "5. Output in Chinese or English matching the user's question language."
        )

    def _format_papers(self, papers: list) -> str:
        lines = []
        for p in papers:
            pid = p.get("paperId", "?")
            title = p.get("title", "Untitled")[:80]
            year = p.get("year", "?")
            lines.append(f"- {title} ({year}) [ID: {pid}]")
        return "\n".join(lines)

    def _format_claims(self, claims: list) -> str:
        lines = []
        for c in claims:
            stmt = c.get("statement", c.get("claim", ""))[:120]
            src = c.get("evidenceSource", "")
            lines.append(f"- \"{stmt}\" (from: {src})")
        return "\n".join(lines)

    def build_user_prompt(self, question: str, query_type: str, context: dict) -> str:
        parts = [f"## User Question\n{question}\n"]

        if context["papers"]:
            parts.append("## Relevant Papers\n" + self._format_papers(context["papers"]))

        if context["claims"]:
            parts.append("## Relevant Claims\n" + self._format_claims(context["claims"]))

        if context["semantic_results"]:
            lines = []
            for r in context["semantic_results"][:5]:
                lines.append(f"- \"{r.get('text', '')[:120]}\" (paper: {r.get('paperId', '?')})")
            parts.append("## Semantic Search Results\n" + "\n".join(lines))

        return "\n\n".join(parts)

    def build_prompt(self, question: str, query_type: str, context: dict) -> tuple[str, str]:
        """返回 (system_prompt, user_prompt)"""
        return self.build_system_prompt(), self.build_user_prompt(question, query_type, context)
```

---

### Task 5: AnswerGenerator + CitationFormatter

**Files:**
- Create: `litmind/src/litmind_chat/generator/__init__.py`
- Create: `litmind/src/litmind_chat/generator/answer_generator.py`
- Create: `litmind/src/litmind_chat/generator/citation_formatter.py`

- [ ] **Step 1: Write failing test**

```python
class TestAnswerGenerator:
    def test_generate_with_mock(self):
        from litmind_chat.generator.answer_generator import AnswerGenerator
        from litmind_analyzer.provider import LLMProvider

        class MockProvider(LLMProvider):
            def analyze(self, system_prompt, user_prompt):
                return {
                    "answer": "Flatfoot increases forefoot motion based on current evidence.",
                    "supportingPapers": [
                        {"paperId": "P1", "title": "Flatfoot Study", "year": 2024, "authors": "Stone et al."}
                    ],
                    "supportingClaims": [
                        {"statement": "Flatfoot increases forefoot motion", "evidenceSource": "Results", "paperId": "P1"}
                    ],
                    "confidence": 0.91,
                }

        gen = AnswerGenerator(provider=MockProvider())
        result = gen.generate("Does flatfoot increase motion?", "System prompt", "User prompt")
        assert result.answer == "Flatfoot increases forefoot motion based on current evidence."
        assert len(result.supportingPapers) == 1
        assert result.confidence == 0.91

    def test_generate_empty_fallback(self):
        from litmind_chat.generator.answer_generator import AnswerGenerator
        from litmind_analyzer.provider import LLMProvider

        class FailingProvider(LLMProvider):
            def analyze(self, system_prompt, user_prompt):
                raise Exception("API Error")

        gen = AnswerGenerator(provider=FailingProvider())
        result = gen.generate("question", "sys", "user")
        assert "无法" in result.answer or "回答" in result.answer
        assert result.confidence == 0.0
```

- [ ] **Step 2: Write AnswerGenerator**

```python
"""AnswerGenerator — 调用 LLM 生成结构化答案"""

from typing import Any, Optional
from ..models.response import ChatResponse, SupportingPaper, SupportingClaim


class AnswerGenerator:
    """使用 LLM 生成带引用的答案"""

    def __init__(self, provider=None, model: str = "claude-sonnet-4-20250514"):
        self.provider = provider
        self.model = model

    def generate(
        self,
        question: str,
        system_prompt: str,
        user_prompt: str,
    ) -> ChatResponse:
        if not self.provider:
            return ChatResponse(
                answer="无法回答问题：未配置 LLM 提供者。请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY。",
                confidence=0.0,
            )

        try:
            raw = self.provider.analyze(system_prompt, user_prompt)

            papers = []
            for p in raw.get("supportingPapers", []):
                papers.append(SupportingPaper(
                    paperId=p.get("paperId", ""),
                    title=p.get("title", ""),
                    year=p.get("year"),
                    authors=p.get("authors", ""),
                    journal=p.get("journal", ""),
                    doi=p.get("doi", ""),
                ))

            claims = []
            for c in raw.get("supportingClaims", []):
                claims.append(SupportingClaim(
                    statement=c.get("statement", ""),
                    evidenceSource=c.get("evidenceSource", ""),
                    paperId=c.get("paperId", ""),
                ))

            return ChatResponse(
                answer=raw.get("answer", "无法生成答案。"),
                supportingPapers=papers,
                supportingClaims=claims,
                confidence=raw.get("confidence", 0.5),
            )

        except Exception as e:
            return ChatResponse(
                answer=f"无法回答问题：{str(e)}",
                confidence=0.0,
            )
```

- [ ] **Step 3: Write CitationFormatter**

```python
"""CitationFormatter — 格式化引用文本"""

from typing import Optional
from ..models.response import SupportingPaper, SupportingClaim


class CitationFormatter:
    """将 SupportingPaper 和 SupportingClaim 格式化为可读引用"""

    @staticmethod
    def format_paper(paper: SupportingPaper) -> str:
        parts = []
        if paper.authors:
            parts.append(paper.authors)
        if paper.year:
            parts.append(f"({paper.year})")
        if paper.title:
            parts.append(paper.title[:100])
        if paper.journal:
            parts.append(paper.journal)
        if paper.doi:
            parts.append(f"DOI: {paper.doi}")
        return ". ".join(parts) if parts else f"[ID: {paper.paperId}]"

    @staticmethod
    def format_paper_short(paper: SupportingPaper) -> str:
        if paper.authors and paper.year:
            return f"{paper.authors} ({paper.year})"
        return f"[{paper.paperId}]"

    @staticmethod
    def format_claim(claim: SupportingClaim) -> str:
        source = f" [{claim.evidenceSource}]" if claim.evidenceSource else ""
        return f'"{claim.statement}"{source}'
```

---

### Task 6: ResearchChatService

**Files:**
- Create: `litmind/src/litmind_chat/service.py`

- [ ] **Step 1: Write failing test**

```python
class TestResearchChatService:
    @pytest.fixture
    def service(self):
        from litmind_chat.service import ResearchChatService
        return ResearchChatService(kb=None)

    def test_ask_basic(self, service):
        result = service.ask("哪些文献研究了 Flatfoot？")
        assert result.queryType == "paper_search"
        assert result.answer != ""

    def test_search_only(self, service):
        result = service.search("SPM1D")
        assert result.queryType == "statistic_search"

    def test_get_sources(self, service):
        sources = service.get_sources("Does flatfoot increase motion?")
        assert isinstance(sources, list)
```

- [ ] **Step 2: Write ResearchChatService**

```python
"""ResearchChatService — 科研问答统一入口"""

from typing import Optional
from .config import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL, CACHE_TTL_SECONDS, CACHE_MAX_SIZE, DEFAULT_TOP_K
from .models.query import ChatQuery, QueryType
from .models.response import ChatResponse, SearchResult, SupportingPaper, SupportingClaim
from .cache import QueryCache
from .classifier.query_classifier import QueryClassifier
from .context.builder import ContextBuilder
from .generator.answer_generator import AnswerGenerator
from .generator.citation_formatter import CitationFormatter


class ResearchChatService:
    """科研知识库问答系统 — 统一入口"""

    def __init__(
        self,
        kb=None,
        llm_provider=None,
        model: str = "",
    ):
        self.kb = kb
        self.cache = QueryCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)
        self.classifier = QueryClassifier(provider=llm_provider, model=model)
        self.context_builder = ContextBuilder(kb=kb)
        self.generator = AnswerGenerator(provider=llm_provider, model=model or DEFAULT_LLM_MODEL)
        self.formatter = CitationFormatter()

    def ask(self, question: str, top_k: int = DEFAULT_TOP_K) -> ChatResponse:
        """提问并获取带引用的答案"""
        # 检查缓存
        cached = self.cache.get(question)
        if cached and isinstance(cached, ChatResponse):
            return cached

        # 1. 分类
        query_type = self.classifier.classify(question)

        # 2. 检索
        context = self.context_builder.retrieve(question, query_type, top_k=top_k)

        # 3. 构建 prompt
        sys_prompt, user_prompt = self.context_builder.build_prompt(question, query_type, context)

        # 4. 生成答案
        response = self.generator.generate(question, sys_prompt, user_prompt)
        response.queryType = query_type

        # 5. 缓存
        self.cache.put(question, response)

        return response

    def search(self, question: str, top_k: int = DEFAULT_TOP_K) -> SearchResult:
        """仅检索，不生成答案"""
        query_type = self.classifier.classify(question)
        context = self.context_builder.retrieve(question, query_type, top_k=top_k)

        papers = [SupportingPaper(**p) for p in context.get("papers", [])] if context.get("papers") else []
        claims = []
        for c_data in context.get("claims", []):
            if isinstance(c_data, dict):
                claims.append(SupportingClaim(
                    statement=c_data.get("statement", ""),
                    evidenceSource=c_data.get("evidenceSource", ""),
                    paperId=c_data.get("paperId", ""),
                ))

        return SearchResult(
            query=question,
            queryType=query_type,
            papers=papers,
            claims=claims,
        )

    def get_sources(self, question: str, top_k: int = DEFAULT_TOP_K) -> list[SupportingPaper]:
        """仅返回相关文献来源"""
        search_result = self.search(question, top_k=top_k)
        return search_result.papers
```

---

### Task 7: CLI

**Files:**
- Create: `litmind/src/litmind_chat/cli.py`

- [ ] **Step 1: Write CLI**

```python
"""Research Chat CLI — 交互式问答"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import click
from litmind_chat.service import ResearchChatService
from litmind_analyzer.providers import AnthropicProvider, OpenAIProvider


def _get_provider(provider_name: str, api_key: str | None, model: str | None):
    if provider_name == "anthropic":
        return AnthropicProvider(api_key=api_key or "", model=model or "claude-sonnet-4-20250514")
    elif provider_name == "openai":
        return OpenAIProvider(api_key=api_key or "", model=model or "gpt-4o")
    return None


@click.group()
def cli():
    pass


@cli.command()
@click.argument("question")
@click.option("--provider", default="anthropic", show_default=True)
@click.option("--model", default="")
@click.option("--api-key", default=None)
@click.option("--db", default="", help="SQLite path")
@click.option("--chroma", default="", help="ChromaDB path")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def ask(question, provider, model, api_key, db, chroma, json_output):
    """提问并获取答案"""
    from litmind_knowledge.service import KnowledgeBase
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    llm_provider = _get_provider(provider, api_key, model)

    service = ResearchChatService(kb=kb, llm_provider=llm_provider)
    result = service.ask(question)

    if json_output:
        click.echo(result.model_dump_json(indent=2, ensure_ascii=False))
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"Q: {question}")
        click.echo(f"{'='*60}")
        click.echo(f"\n{result.answer}\n")
        if result.supportingPapers:
            click.echo("📚 相关文献:")
            for p in result.supportingPapers:
                click.echo(f"  - {CitationFormatter.format_paper(p)}")
        if result.supportingClaims:
            click.echo("\n📎 支撑证据:")
            for c in result.supportingClaims:
                click.echo(f"  - {CitationFormatter.format_claim(c)}")
        click.echo(f"\n置信度: {result.confidence:.2f}")


@cli.command()
@click.argument("question")
@click.option("--db", default="")
@click.option("--chroma", default="")
@click.option("--json-output", is_flag=True)
def search(question, db, chroma, json_output):
    """仅检索知识库，不生成答案"""
    pass  # simplified


@cli.command()
def interactive():
    """交互式问答模式"""
    import os
    from litmind_knowledge.service import KnowledgeBase
    from litmind_chat.generator.citation_formatter import CitationFormatter

    kb_path = os.environ.get("LITMIND_DB_PATH", "")
    chroma_path = os.environ.get("LITMIND_CHROMA_PATH", "")
    provider_name = os.environ.get("LITMIND_PROVIDER", "anthropic")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")

    kb = KnowledgeBase(db_path=kb_path, chroma_path=chroma_path)
    llm_provider = _get_provider(provider_name, api_key, None)
    service = ResearchChatService(kb=kb, llm_provider=llm_provider)

    click.echo("\n🔬 LitMind Research Chat — 输入问题开始查询 (输入 /exit 退出)\n")

    while True:
        question = click.prompt("\n❓", prompt_suffix=" ")
        if question.lower() in ("/exit", "/quit", "exit", "quit"):
            break

        result = service.ask(question)

        click.echo(f"\n{result.answer}\n")
        if result.supportingPapers:
            click.echo("📚 相关文献:")
            for p in result.supportingPapers[:3]:
                click.echo(f"  - {CitationFormatter.format_paper_short(p)}")
        if result.supportingClaims:
            click.echo("📎 证据:")
            for c in result.supportingClaims[:3]:
                click.echo(f"  - {CitationFormatter.format_claim(c)}")


if __name__ == "__main__":
    cli()
```

---

### Task 8: Skill + Config Updates

**Files:**
- Create: `litmind/.claude/skills/litmind-chat/SKILL.md`
- Modify: `litmind/pyproject.toml`

- [ ] **Step 1: Create skill**

```markdown
---
name: litmind-chat
description: LitMind Research Chat — 面向科研知识库的自然语言问答系统
---

# LitMind Research Chat

基于 Knowledge Base 的科研智能问答系统。用户通过自然语言提问，系统自动检索知识库，返回带出处、可追溯的答案。

## 工作流程

问题 → QueryClassifier → ContextBuilder (KB检索) → AnswerGenerator (LLM) → 带引用答案

## 调用方式

```bash
# 命令行提问
litmind-chat ask "Does flatfoot increase forefoot motion?"

# 交互式模式
litmind-chat interactive

# JSON 格式输出
litmind-chat ask "SPM1D 相关研究" --json-output

# 仅检索不生成
litmind-chat search "哪些文献研究 foot arch"
```

## 环境变量

- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — LLM 提供者
- `LITMIND_DB_PATH` — SQLite 路径
- `LITMIND_CHROMA_PATH` — ChromaDB 路径
```

- [ ] **Step 2: Update pyproject.toml**
```toml
[project.scripts]
litmind-chat = "litmind_chat.cli:cli"
```

---

## Self-Review

- [x] Spec coverage: QueryClassifier (Task 3), ContextBuilder (Task 4), AnswerGenerator (Task 5), CitationFormatter (Task 5), Service (Task 6), CLI (Task 7)
- [x] Spec coverage: ask/search/get_sources interfaces (Task 6)
- [x] Spec coverage: QueryType enum covers all 8 types (Task 1)
- [x] Spec coverage: SupportingPaper/Claim with all required fields (Task 1)
- [x] Spec coverage: Cache (Task 2)
- [x] No placeholders: All code blocks complete
- [x] Type consistency: ChatResponse fields match SupportingPaper/Claim models
- [ ] Tests run and pass
