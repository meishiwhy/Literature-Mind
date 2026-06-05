"""EvidenceStrengthEvaluator — 证据强度评估"""

from __future__ import annotations

import math

from .config import (
    CONFIDENCE_WEIGHT_CONSISTENCY,
    CONFIDENCE_WEIGHT_COUNT,
    CONFIDENCE_WEIGHT_SIMILARITY,
    HIGH_SIMILARITY,
    MODERATE_SUPPORT_RATIO,
    STRONG_SUPPORT_MIN,
)
from .models import EvidenceResult


class EvidenceStrengthEvaluator:
    """证据强度评估器

    综合评估支持/反对数量、一致性、语义相似度，给出证据强度等级和置信度。
    """

    def evaluate(self, result: EvidenceResult) -> EvidenceResult:
        """评估证据强度

        直接在 result 上设置 evidenceStrength 和 confidence。
        """
        if result.totalPapers == 0:
            result.evidenceStrength = "Insufficient Evidence"
            result.confidence = 0.0
            return result

        n_support = result.supportingPapers
        n_oppose = result.opposingPapers

        # 计算一致性比例
        if n_support + n_oppose > 0:
            consistency = n_support / (n_support + n_oppose)
        else:
            consistency = 0.5

        # 计算平均相似度
        all_items = result.support + result.oppose + result.neutral
        avg_similarity = (
            sum(item.similarity for item in all_items) / len(all_items)
            if all_items
            else 0.0
        )

        # 证据强度等级
        result.evidenceStrength = self._assign_strength(
            n_support, n_oppose, consistency, avg_similarity
        )

        # 置信度
        result.confidence = self._compute_confidence(
            n_support, n_oppose, consistency, avg_similarity
        )

        return result

    def _assign_strength(
        self,
        n_support: int,
        n_oppose: int,
        consistency: float,
        avg_similarity: float,
    ) -> str:
        strength = "Insufficient Evidence"

        if n_support >= STRONG_SUPPORT_MIN and n_oppose == 0:
            strength = "Strongly Supported"
        elif n_support >= STRONG_SUPPORT_MIN and consistency >= 0.66:
            strength = "Moderately Supported"
        elif n_support > 0 and n_support > n_oppose:
            strength = "Weakly Supported"
        elif n_support > 0 and n_oppose > 0:
            strength = "Mixed Evidence"
        elif n_support == 0 and n_oppose == 0:
            strength = "Insufficient Evidence"

        return strength

    def _compute_confidence(
        self,
        n_support: int,
        n_oppose: int,
        consistency: float,
        avg_similarity: float,
    ) -> float:
        total = n_support + n_oppose

        # 证据数量分（S 形曲线，少量证据时增长快）
        count_score = 1.0 - math.exp(-0.3 * total)

        # 一致性分
        consistency_score = consistency

        # 相似度分
        similarity_score = min(1.0, avg_similarity / HIGH_SIMILARITY)

        # 加权综合
        confidence = (
            CONFIDENCE_WEIGHT_COUNT * count_score
            + CONFIDENCE_WEIGHT_CONSISTENCY * consistency_score
            + CONFIDENCE_WEIGHT_SIMILARITY * similarity_score
        )

        return round(min(1.0, max(0.0, confidence)), 4)
