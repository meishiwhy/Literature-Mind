import pytest
from litmind_review.gaps import GapAnalyzer
from litmind_review.models import ResearchGap


class TestGapAnalyzer:
    def setup_method(self):
        self.analyzer = GapAnalyzer()

    def test_analyze_empty(self):
        gaps = self.analyzer.analyze([], [], {})
        assert isinstance(gaps, list)

    def test_analyze_low_count_themes(self):
        from litmind_review.models import ReviewTheme
        themes = [ReviewTheme(name="Rare Topic", paperCount=1)]
        gaps = self.analyzer.analyze(themes, [], {"year_distribution": {2020: 1}})
        assert len(gaps) >= 1
        assert "Rare" in gaps[0].description
