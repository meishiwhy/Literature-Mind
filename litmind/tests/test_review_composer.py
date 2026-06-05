import pytest
from litmind_review.composer import ReviewComposer
from litmind_review.models import ReviewInput, ReviewTheme, ResearchConsensus, ResearchControversy, ResearchGap


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return "Generated section text with [P1] citation."


class TestReviewComposer:
    def setup_method(self):
        self.composer = ReviewComposer(llm_provider=MockProvider())

    def test_compose_basic(self):
        inp = ReviewInput(topic="Flatfoot Biomechanics", max_papers=10)
        result = self.composer.compose(
            inp=inp,
            themes=[ReviewTheme(name="Kinematics", paperCount=3)],
            consensus=[],
            controversies=[],
            gaps=[],
            trend_data={},
            outline={"Introduction": []},
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_compose_empty(self):
        inp = ReviewInput(topic="", max_papers=0)
        result = self.composer.compose(inp, [], [], [], [], {}, {})
        assert isinstance(result, str)
