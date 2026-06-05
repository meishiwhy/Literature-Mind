import pytest
from litmind_review.controversy import ControversyAnalyzer


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult, EvidenceItem
        return EvidenceResult(
            query=query,
            support=[EvidenceItem(paperId="P1", direction="support")],
            oppose=[EvidenceItem(paperId="P2", direction="oppose")],
        )


class TestControversyAnalyzer:
    def test_analyze_empty(self):
        analyzer = ControversyAnalyzer(evidence_service=MockEvidenceService())
        result = analyzer.analyze([])
        assert result == []

    def test_analyze_with_themes(self):
        from litmind_review.models import ReviewTheme
        analyzer = ControversyAnalyzer(evidence_service=MockEvidenceService())
        result = analyzer.analyze([ReviewTheme(name="Footwear", paperCount=3)])
        assert isinstance(result, list)
