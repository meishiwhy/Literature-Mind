import pytest
from litmind_review.discovery import ThemeDiscoveryEngine
from litmind_review.models import ReviewTheme


class MockProvider:
    def analyze(self, system_prompt, user_prompt):
        return {
            "themes": [
                {"name": "Foot Kinematics", "description": "Studies on foot movement", "paper_indices": [0, 1]},
                {"name": "MTP Function", "description": "MTP joint mechanics", "paper_indices": [2]},
            ]
        }


class TestThemeDiscovery:
    def setup_method(self):
        self.engine = ThemeDiscoveryEngine(llm_provider=MockProvider())

    def test_discover_empty(self):
        themes = self.engine.discover([])
        assert themes == []

    def test_discover_with_papers(self):
        papers = [
            {"title": "Flatfoot kinematics", "paperId": "P1", "variables": ["GRF"], "keywords": ["flatfoot"]},
            {"title": "Foot arch study", "paperId": "P2", "variables": ["MTP"], "keywords": ["arch"]},
            {"title": "MTP joint ROM", "paperId": "P3", "variables": ["ROM"], "keywords": ["mtp"]},
        ]
        themes = self.engine.discover(papers)
        assert len(themes) > 1
        assert all(isinstance(t, ReviewTheme) for t in themes)
        assert themes[0].paperIds == ["P1", "P2"]

    def test_no_llm_fallback(self):
        engine = ThemeDiscoveryEngine(llm_provider=None)
        themes = engine.discover([{"title": "Test"}])
        assert themes == []
