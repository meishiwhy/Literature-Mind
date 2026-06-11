"""DiscussionGeneratorService -- 统一入口"""
from __future__ import annotations

from litmind_evidence import EvidenceFinderService

from .cache import DiscussionCache
from .citation import CitationManager
from .collector import EvidenceCollector
from .composer import DiscussionComposer
from .config import CACHE_TTL_SECONDS
from .models import DiscussionInput, DiscussionResult, DiscussionCitation


class DiscussionGeneratorService:
    def __init__(
        self,
        evidence_service: EvidenceFinderService,
        llm_provider,
        model: str = "",
        cache_ttl: int = CACHE_TTL_SECONDS,
    ):
        self._collector = EvidenceCollector(evidence_service)
        self._composer = DiscussionComposer(llm_provider, model=model)
        self._cache = DiscussionCache(ttl=cache_ttl)

    def generate_discussion(
        self, inp: DiscussionInput, top_k: int = 10, use_cache: bool = True,
    ) -> DiscussionResult:
        if use_cache:
            cache_key = f"{inp.studyTopic}:{':'.join(inp.results)}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        from .parser import ResultParser
        parsed = ResultParser().parse(inp.results)
        evidence = self._collector.collect(parsed, top_k=top_k)
        outline = self._composer.generate_outline(inp)
        draft = self._composer.compose(inp, evidence)

        citation_mgr = CitationManager()
        known_ids = {item.paperId for item in evidence.all_items if item.paperId}

        # 引用过滤：删除 Draft 中不在知识库的虚构 paperId 引用
        draft = citation_mgr.filter_known(draft, known_ids)

        raw_ids = citation_mgr.extract_from_text(draft)
        for pid in raw_ids:
            if pid in known_ids:
                citation_mgr.add(DiscussionCitation(paperId=pid, section="draft"))

        result = DiscussionResult(
            discussionOutline=outline,
            discussionDraft=draft,
            supportingPapers=evidence.supporting,
            opposingPapers=evidence.opposing,
            citations=citation_mgr.to_citation_list(known_ids),
        )

        if use_cache:
            self._cache.set(cache_key, result)
        return result

    def generate_outline(self, inp: DiscussionInput) -> dict[str, str]:
        return self._composer.generate_outline(inp)

    def collect_evidence(self, inp: DiscussionInput, top_k: int = 10):
        from .parser import ResultParser
        parsed = ResultParser().parse(inp.results)
        return self._collector.collect(parsed, top_k=top_k)

    def clear_cache(self) -> None:
        self._cache.clear()
