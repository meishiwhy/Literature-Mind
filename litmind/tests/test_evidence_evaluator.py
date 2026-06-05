"""Tests for EvidenceStrengthEvaluator"""

import pytest
from litmind_evidence.evaluator import EvidenceStrengthEvaluator
from litmind_evidence.models import EvidenceItem, EvidenceResult


class TestEvidenceStrengthEvaluator:
    def setup_method(self):
        self.eval = EvidenceStrengthEvaluator()

    def test_insufficient_evidence(self):
        result = EvidenceResult(query="test")
        self.eval.evaluate(result)
        assert result.evidenceStrength == "Insufficient Evidence"
        assert result.confidence == 0.0

    def test_strongly_supported(self):
        result = EvidenceResult(
            query="test",
            support=[EvidenceItem(paperId=f"P{i}", similarity=0.8, direction="support") for i in range(3)],
            supportingPapers=3,
            totalPapers=3,
        )
        self.eval.evaluate(result)
        assert result.evidenceStrength == "Strongly Supported"
        assert result.confidence > 0.5

    def test_mixed_evidence(self):
        result = EvidenceResult(
            query="test",
            support=[EvidenceItem(paperId="P1", similarity=0.8, direction="support")],
            oppose=[EvidenceItem(paperId="P2", similarity=0.8, direction="oppose")],
            supportingPapers=1, opposingPapers=1, totalPapers=2,
        )
        self.eval.evaluate(result)
        assert result.evidenceStrength == "Mixed Evidence"

    def test_weakly_supported(self):
        result = EvidenceResult(
            query="test",
            support=[EvidenceItem(paperId="P1", similarity=0.6, direction="support")],
            supportingPapers=1, totalPapers=1,
        )
        self.eval.evaluate(result)
        assert "Weakly" in result.evidenceStrength

    def test_confidence_range(self):
        """置信度应在 0-1 之间"""
        result = EvidenceResult(
            query="test",
            support=[EvidenceItem(paperId=f"P{i}", similarity=0.7, direction="support") for i in range(5)],
            supportingPapers=5, totalPapers=5,
        )
        self.eval.evaluate(result)
        assert 0.0 <= result.confidence <= 1.0
