"""Tests for EvidenceAggregator"""

import pytest
from litmind_evidence.aggregator import EvidenceAggregator
from litmind_evidence.models import EvidenceItem


class TestEvidenceAggregator:
    def setup_method(self):
        self.agg = EvidenceAggregator()

    def test_aggregate_empty(self):
        result = self.agg.aggregate("test query", [])
        assert result.query == "test query"
        assert result.totalPapers == 0
        assert result.support == []
        assert result.oppose == []

    def test_aggregate_support_only(self):
        items = [
            EvidenceItem(paperId="P1", direction="support"),
            EvidenceItem(paperId="P2", direction="support"),
        ]
        result = self.agg.aggregate("q", items)
        assert result.supportingPapers == 2
        assert result.opposingPapers == 0
        assert len(result.support) == 2

    def test_aggregate_mixed(self):
        items = [
            EvidenceItem(paperId="P1", direction="support"),
            EvidenceItem(paperId="P2", direction="oppose"),
            EvidenceItem(paperId="P3", direction="neutral"),
        ]
        result = self.agg.aggregate("q", items)
        assert result.supportingPapers == 1
        assert result.opposingPapers == 1
        assert len(result.neutral) == 1
        assert result.totalPapers == 3

    def test_merge(self):
        r1 = self.agg.aggregate("q", [EvidenceItem(paperId="P1", direction="support")])
        r2 = self.agg.aggregate("q", [EvidenceItem(paperId="P2", direction="oppose")])
        merged = self.agg.merge([r1, r2])
        assert merged.supportingPapers == 1
        assert merged.opposingPapers == 1
        assert merged.totalPapers == 2
