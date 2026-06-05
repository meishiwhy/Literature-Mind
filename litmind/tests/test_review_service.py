"""Tests for ReviewGeneratorService"""
import pytest
from litmind_review.service import ReviewGeneratorService
from litmind_review.models import ReviewInput, ReviewResult


class MockKB:
    def semantic_search(self, query, top_k=20):
        return []
    def search_claims(self, query):
        return []
    def search_variables(self, query):
        return []
    def get_paper(self, paper_id):
        return None


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult
        return EvidenceResult(query=query)


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated text."


class TestReviewService:
    def setup_method(self):
        self.service = ReviewGeneratorService(
            kb=MockKB(),
            evidence_service=MockEvidenceService(),
            llm_provider=MockProvider(),
        )

    def test_generate_review(self):
        inp = ReviewInput(topic="Test Topic")
        result = self.service.generate_review(inp, use_cache=False)
        assert isinstance(result, ReviewResult)
        assert result.topic == "Test Topic"

    def test_discover_themes(self):
        themes = self.service.discover_themes("Test")
        assert isinstance(themes, list)

    def test_analyze_consensus(self):
        result = self.service.analyze_consensus("Test")
        assert isinstance(result, list)

    def test_analyze_controversies(self):
        result = self.service.analyze_controversies("Test")
        assert isinstance(result, list)

    def test_identify_gaps(self):
        result = self.service.identify_research_gaps("Test")
        assert isinstance(result, list)
