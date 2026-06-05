import pytest
from litmind_discussion.composer import DiscussionComposer
from litmind_discussion.models import DiscussionInput, DiscussionResult, CollectedEvidence
from litmind_evidence.models import EvidenceItem


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated section content. [P1] citation."


class TestDiscussionComposer:
    def setup_method(self):
        self.composer = DiscussionComposer(llm_provider=MockProvider())

    def test_generate_outline(self):
        inp = DiscussionInput(studyTopic="Test", results=["R1", "R2"])
        outline = self.composer.generate_outline(inp)
        assert isinstance(outline, dict)
        sections = ["main_finding", "supporting", "contradictory", "mechanisms", "implications", "limitations", "future"]
        for s in sections:
            assert s in outline

    def test_compose_empty_input(self):
        inp = DiscussionInput(studyTopic="", results=[])
        ev = CollectedEvidence()
        result = self.composer.compose(inp, ev)
        assert isinstance(result, str)

    def test_compose_with_evidence(self):
        inp = DiscussionInput(studyTopic="Test Topic", results=["Result A"])
        ev = CollectedEvidence()
        ev.all_items = [EvidenceItem(paperId="P1", title="Paper 1", claim="Claim 1")]
        ev.supporting = [EvidenceItem(paperId="P1", title="Paper 1", claim="Claim 1")]
        result = self.composer.compose(inp, ev)
        assert isinstance(result, str)
        assert len(result) > 0
