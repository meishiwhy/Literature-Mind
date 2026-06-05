import pytest
from litmind_review.consensus import ConsensusAnalyzer
from litmind_review.models import ResearchConsensus


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult, EvidenceItem
        return EvidenceResult(
            query=query,
            evidenceStrength="Strongly Supported",
            confidence=0.85,
            support=[EvidenceItem(paperId="P1", direction="support")],
        )


class TestConsensusAnalyzer:
    def test_analyze_empty(self):
        analyzer = ConsensusAnalyzer(evidence_service=MockEvidenceService())
        consensuses = analyzer.analyze([])
        assert consensuses == []

    def test_analyze_with_themes(self):
        from litmind_review.models import ReviewTheme
        analyzer = ConsensusAnalyzer(evidence_service=MockEvidenceService())
        themes = [ReviewTheme(name="Foot Kinematics", paperCount=3)]
        result = analyzer.analyze(themes)
        assert isinstance(result, list)
