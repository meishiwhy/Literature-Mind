"""ControversyAnalyzer — 研究争议识别"""
from __future__ import annotations
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
