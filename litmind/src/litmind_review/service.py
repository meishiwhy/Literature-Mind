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

    def generate_review(self, inp: ReviewInput, use_cache: bool = True) -> ReviewResult:
        if use_cache:
            cached = self._cache.get(inp.topic)
            if cached is not None:
                return cached

        papers = self._retrieve_papers(inp.topic, inp.max_papers)
        trend_data = self._trend.analyze(papers)
        themes = self._discovery.discover(papers)
        consensuses = self._consensus.analyze(themes)
        controversies = self._controversy.analyze(themes)
        gaps = self._gaps.analyze(themes, consensuses, trend_data)
        outline = self._outline.generate(
            inp.topic,
            [t.name for t in themes],
            [c.statement for c in consensuses],
            [c.statement for c in controversies],
            [g.description for g in gaps],
        )
        draft = self._composer.compose(
            inp, themes, consensuses, controversies, gaps, trend_data, outline,
        )

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
