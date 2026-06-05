"""EvidenceFinderService — 证据检索与归纳统一入口"""

from __future__ import annotations

from typing import Any, Optional

from litmind_knowledge.service import KnowledgeBase

from .aggregator import EvidenceAggregator
from .cache import QueryCache
from .classifier import ClaimClassifier, LLMClaimClassifier, PatternClaimClassifier
from .config import CACHE_TTL_SECONDS, DEFAULT_TOP_K
from .evaluator import EvidenceStrengthEvaluator
from .models import EvidenceItem, EvidenceResult
from .retriever import ClaimRetriever


class EvidenceFinderService:
    """Evidence Finder 统一服务入口

    使用方式:
        from litmind_evidence import EvidenceFinderService
        service = EvidenceFinderService(kb=kb, llm_provider=provider)
        result = service.find_evidence("Flatfoot increases MTP ROM")
    """

    def __init__(
        self,
        kb: KnowledgeBase,
        llm_provider: Optional[Any] = None,
        model: str = "",
        cache_ttl: int = CACHE_TTL_SECONDS,
    ):
        self._retriever = ClaimRetriever(kb)
        self._aggregator = EvidenceAggregator()
        self._evaluator = EvidenceStrengthEvaluator()
        self._cache = QueryCache(ttl=cache_ttl)

        self._llm_provider = llm_provider
        self._model = model

        # 分类器
        if llm_provider:
            self._classifier: ClaimClassifier = LLMClaimClassifier(llm_provider)
        else:
            self._classifier: ClaimClassifier = PatternClaimClassifier()

        # 模式分类器作为备选
        self._pattern_classifier = PatternClaimClassifier()

    def find_evidence(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        use_cache: bool = True,
    ) -> EvidenceResult:
        """执行完整的证据检索与分析

        流程:
        1. 检查缓存
        2. ClaimRetriever 检索 KB
        3. ClaimClassifier 分类方向
        4. EvidenceAggregator 分组
        5. EvidenceStrengthEvaluator 评估强度
        6. 写入缓存并返回
        """
        if use_cache:
            cached = self._cache.get(query)
            if cached is not None:
                return cached

        # 1. 检索
        raw_claims = self._retriever.retrieve_claims(query, top_k=top_k)

        if not raw_claims:
            result = EvidenceResult(query=query)
            self._evaluator.evaluate(result)
            if use_cache:
                self._cache.set(query, result)
            return result

        # 2. 分类
        classified = self._classifier.classify_batch(query, raw_claims)

        # 3. 构建 EvidenceItem
        items = []
        for raw, cls in zip(raw_claims, classified):
            item = EvidenceItem(
                paperId=raw.get("paperId", ""),
                title=raw.get("title", ""),
                year=raw.get("year"),
                doi=raw.get("doi", ""),
                claim=raw.get("statement", ""),
                similarity=raw.get("similarity", 0.0),
                direction=cls.direction,
            )
            items.append(item)

        # 4. 聚合
        result = self._aggregator.aggregate(query, items)

        # 5. 评估强度
        self._evaluator.evaluate(result)

        if use_cache:
            self._cache.set(query, result)

        return result

    def get_supporting_papers(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[EvidenceItem]:
        """仅获取支持证据的快捷方法"""
        result = self.find_evidence(query, top_k)
        return result.support

    def get_opposing_papers(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[EvidenceItem]:
        """仅获取反对证据的快捷方法"""
        result = self.find_evidence(query, top_k)
        return result.oppose

    def evaluate_evidence_strength(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> tuple[str, float]:
        """快速获取证据强度和置信度"""
        result = self.find_evidence(query, top_k)
        return result.evidenceStrength, result.confidence

    def clear_cache(self) -> None:
        """清空查询缓存"""
        self._cache.clear()
