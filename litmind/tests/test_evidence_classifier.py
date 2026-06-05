"""Tests for ClaimClassifier"""

import pytest
from litmind_evidence.classifier import PatternClaimClassifier, ClaimClassifier, ClassificationResult


class TestPatternClaimClassifier:
    def setup_method(self):
        self.classifier = PatternClaimClassifier(threshold=0.3)

    def test_support_pattern(self):
        claims = [{"paperId": "P1", "statement": "X was significantly greater than Y"}]
        results = self.classifier.classify_batch("test", claims)
        assert results[0].direction == "support"

    def test_oppose_pattern(self):
        claims = [{"paperId": "P1", "statement": "No significant difference was found between groups"}]
        results = self.classifier.classify_batch("test", claims)
        assert results[0].direction == "oppose"

    def test_neutral_pattern(self):
        claims = [{"paperId": "P1", "statement": "Participants were recruited from local clinics"}]
        results = self.classifier.classify_batch("test", claims)
        assert results[0].direction == "neutral"

    def test_empty_claims(self):
        results = self.classifier.classify_batch("test", [])
        assert results == []

    def test_empty_statement(self):
        claims = [{"paperId": "P1", "statement": ""}]
        results = self.classifier.classify_batch("test", claims)
        assert results[0].direction == "neutral"
