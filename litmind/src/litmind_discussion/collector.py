"""EvidenceCollector — 遍历用户结果，收集证据"""

from __future__ import annotations

from litmind_evidence.models import EvidenceItem
from litmind_evidence.service import EvidenceFinderService

from .config import EVIDENCE_TOP_K
from .models import CollectedEvidence, ParsedResult


class EvidenceCollector:
    def __init__(self, evidence_service: EvidenceFinderService):
        self._evidence = evidence_service

    def collect(
        self,
        parsed_results: list[ParsedResult],
        top_k: int = EVIDENCE_TOP_K,
    ) -> CollectedEvidence:
        collected = CollectedEvidence()
        seen_ids: set[str] = set()

        for i, result in enumerate(parsed_results):
            ev_result = self._evidence.find_evidence(result.original, top_k=top_k)
            collected.by_result[i] = ev_result

            for item in ev_result.support + ev_result.oppose + ev_result.neutral:
                if item.paperId not in seen_ids:
                    seen_ids.add(item.paperId)
                    collected.all_items.append(item)
                    if item.direction == "support":
                        collected.supporting.append(item)
                    elif item.direction == "oppose":
                        collected.opposing.append(item)

        return collected

    def _format_evidence_context(
        self, items: list[EvidenceItem], max_items: int = 10
    ) -> str:
        lines = []
        for item in items[:max_items]:
            year_str = f" ({item.year})" if item.year else ""
            lines.append(f"[{item.paperId}] {item.title or 'Untitled'}{year_str}")
            if item.claim:
                lines.append(f"  Claim: {item.claim[:100]}")
        return "\n".join(lines)
