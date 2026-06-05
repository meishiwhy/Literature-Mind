"""基于关键词模式的快速分类器（备选/辅助）"""

from __future__ import annotations

import re
from typing import Any

from ..models import ClassificationResult
from .base import ClaimClassifier


# 支持性关键词
SUPPORT_PATTERNS = [
    re.compile(r"significantly greater", re.I),
    re.compile(r"significantly higher", re.I),
    re.compile(r"positive correlation", re.I),
    re.compile(r"consistent with", re.I),
    re.compile(r"support(?:s|ed|ing)? our", re.I),
    re.compile(r"demonstrat(?:e|es|ed)", re.I),
    re.compile(r"confirm(?:s|ed|ing)?", re.I),
    re.compile(r"increase(?:s|d)? in", re.I),
    re.compile(r"decrease(?:s|d)? in", re.I),
    re.compile(r"enhance(?:s|d)?", re.I),
    re.compile(r"reduce(?:s|d)?", re.I),
]

# 反对性关键词
OPPOSE_PATTERNS = [
    re.compile(r"no significant difference", re.I),
    re.compile(r"no effect", re.I),
    re.compile(r"did not (?:find|observe|show)", re.I),
    re.compile(r"no correlation", re.I),
    re.compile(r"not associated", re.I),
    re.compile(r"failed to", re.I),
    re.compile(r"contradict", re.I),
    re.compile(r"inconsistent with", re.I),
    re.compile(r"negatively correlated", re.I),
    re.compile(r"no evidence", re.I),
]

# 中性关键词
NEUTRAL_PATTERNS = [
    re.compile(r"method|methodology|protocol", re.I),
    re.compile(r"participant|subject|patient", re.I),
    re.compile(r"we used|we employed|we conducted", re.I),
    re.compile(r"was measured|were measured", re.I),
    re.compile(r"was calculated|were calculated", re.I),
    re.compile(r"further research|future work", re.I),
    re.compile(r"limitation", re.I),
]


class PatternClaimClassifier(ClaimClassifier):
    """快速模式匹配分类器

    注意: 准确率有限，主要用于兜底或辅助验证。
    核心分类逻辑应使用 LLMClaimClassifier。
    """

    def __init__(self, threshold: float = 0.6):
        self._threshold = threshold

    def classify_batch(
        self,
        query: str,
        claims: list[dict[str, Any]],
    ) -> list[ClassificationResult]:
        results = []
        for item in claims:
            result = self._classify_single(query, item)
            results.append(result)
        return results

    def _classify_single(
        self, query: str, item: dict[str, Any]
    ) -> ClassificationResult:
        statement = item.get("statement", "")
        pid = item.get("paperId", "")

        if not statement:
            return ClassificationResult(paperId=pid, direction="neutral", confidence=0.0)

        # 计算每类匹配数
        support_count = sum(1 for p in SUPPORT_PATTERNS if p.search(statement))
        oppose_count = sum(1 for p in OPPOSE_PATTERNS if p.search(statement))
        neutral_count = sum(1 for p in NEUTRAL_PATTERNS if p.search(statement))

        total = support_count + oppose_count + neutral_count
        if total == 0:
            return ClassificationResult(paperId=pid, direction="neutral", confidence=0.3)

        support_ratio = support_count / total
        oppose_ratio = oppose_count / total

        if support_ratio > self._threshold and support_count > oppose_count:
            return ClassificationResult(
                paperId=pid, direction="support", confidence=support_ratio
            )
        elif oppose_ratio > self._threshold and oppose_count > support_count:
            return ClassificationResult(
                paperId=pid, direction="oppose", confidence=oppose_ratio
            )
        else:
            return ClassificationResult(
                paperId=pid, direction="neutral", confidence=0.5
            )
