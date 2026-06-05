"""EvidenceAggregator — 按方向分组、聚合证据"""

from __future__ import annotations

from typing import Any

from .models import EvidenceItem, EvidenceResult


class EvidenceAggregator:
    """聚合器：将分类后的 evidence 按 support/oppose/neutral 分组"""

    def aggregate(
        self,
        query: str,
        items: list[EvidenceItem],
    ) -> EvidenceResult:
        """聚合证据

        Args:
            query: 用户查询
            items: 已分类的 evidence 列表（每个 item 含 direction）

        Returns:
            分组后的 EvidenceResult
        """
        result = EvidenceResult(query=query)

        for item in items:
            if item.direction == "support":
                result.support.append(item)
            elif item.direction == "oppose":
                result.oppose.append(item)
            else:
                result.neutral.append(item)

        result.totalPapers = len(items)
        result.supportingPapers = len(result.support)
        result.opposingPapers = len(result.oppose)

        return result

    def merge(self, results: list[EvidenceResult]) -> EvidenceResult:
        """合并多个 EvidenceResult"""
        if not results:
            return EvidenceResult()

        merged = EvidenceResult(query=results[0].query)

        for r in results:
            merged.support.extend(r.support)
            merged.oppose.extend(r.oppose)
            merged.neutral.extend(r.neutral)

        merged.totalPapers = len(merged.support) + len(merged.oppose) + len(merged.neutral)
        merged.supportingPapers = len(merged.support)
        merged.opposingPapers = len(merged.oppose)

        return merged
