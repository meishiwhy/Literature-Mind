"""ConsensusAnalyzer — 研究共识识别"""
from __future__ import annotations
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
