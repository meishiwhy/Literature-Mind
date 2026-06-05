"""Tests for Evidence Finder data models"""

import pytest
from litmind_evidence.models import EvidenceItem, EvidenceResult, ClassificationResult


class TestEvidenceItem:
    def test_defaults(self):
        item = EvidenceItem()
        assert item.paperId == ""
        assert item.title == ""
        assert item.year is None
        assert item.similarity == 0.0
        assert item.direction == ""

    def test_full_init(self):
        item = EvidenceItem(
            paperId="P1", title="Test", year=2024, doi="10.123",
            claim="X causes Y", similarity=0.95, direction="support"
        )
        assert item.paperId == "P1"
        assert item.year == 2024
        assert item.similarity == 0.95


class TestEvidenceResult:
    def test_defaults(self):
        r = EvidenceResult()
        assert r.query == ""
        assert r.support == []
        assert r.oppose == []
        assert r.evidenceStrength == ""
        assert r.confidence == 0.0

    def test_with_items(self):
        r = EvidenceResult(
            query="test",
            support=[EvidenceItem(paperId="P1", direction="support")],
            oppose=[EvidenceItem(paperId="P2", direction="oppose")],
            evidenceStrength="Strongly Supported",
            confidence=0.95,
            totalPapers=2, supportingPapers=1, opposingPapers=1,
        )
        assert len(r.support) == 1
        assert r.evidenceStrength == "Strongly Supported"


class TestClassificationResult:
    def test_defaults(self):
        c = ClassificationResult()
        assert c.direction == ""
        assert c.confidence == 0.0

    def test_full(self):
        c = ClassificationResult(paperId="P1", claim="X", direction="support", confidence=0.9)
        assert c.direction == "support"
        assert c.confidence == 0.9
