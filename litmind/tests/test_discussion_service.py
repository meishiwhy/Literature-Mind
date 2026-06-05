"""Tests for DiscussionGeneratorService"""

from litmind_discussion.service import DiscussionGeneratorService
from litmind_discussion.models import DiscussionInput, DiscussionResult


class MockEvidenceService:
    def find_evidence(self, query, top_k=10):
        from litmind_evidence.models import EvidenceResult
        return EvidenceResult(query=query)


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated section content with [P1] citation."


class TestDiscussionGenerator:
    def setup_method(self):
        self.service = DiscussionGeneratorService(
            evidence_service=MockEvidenceService(),
            llm_provider=MockProvider(),
        )

    def test_generate_empty(self):
        inp = DiscussionInput(studyTopic="", results=[])
        result = self.service.generate_discussion(inp, use_cache=False)
        assert isinstance(result, DiscussionResult)

    def test_generate_simple(self):
        inp = DiscussionInput(studyTopic="Test", results=["R1", "R2"])
        result = self.service.generate_discussion(inp, use_cache=False)
        assert isinstance(result, DiscussionResult)
        assert isinstance(result.discussionDraft, str)

    def test_generate_outline(self):
        inp = DiscussionInput(studyTopic="Test", results=["R1"])
        outline = self.service.generate_outline(inp)
        assert isinstance(outline, dict)

    def test_collect_evidence(self):
        inp = DiscussionInput(studyTopic="Test", results=["R1"])
        ev = self.service.collect_evidence(inp)
        assert hasattr(ev, "supporting")
