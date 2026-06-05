import pytest
from litmind_review.trend import TrendAnalyzer


class TestTrendAnalyzer:
    def setup_method(self):
        self.analyzer = TrendAnalyzer()

    def test_analyze_empty(self):
        result = self.analyzer.analyze([])
        assert result["top_variables"] == []
        assert result["top_statistics"] == []
        assert result["year_distribution"] == {}

    def test_analyze_with_papers(self):
        papers = [
            {"variables": ["GRF", "MTP ROM"], "statistics": ["ANOVA"], "studyDesign": "Cross-sectional", "year": 2020},
            {"variables": ["GRF"], "statistics": ["t-test"], "studyDesign": "Experimental", "year": 2021},
            {"variables": ["MTP ROM", "EMG"], "statistics": ["ANOVA"], "studyDesign": "Cross-sectional", "year": 2021},
        ]
        result = self.analyzer.analyze(papers)
        assert len(result["top_variables"]) > 0
        assert ("GRF", 2) in result["top_variables"] or ("GRF", 2) in result["top_variables"]
        assert ("ANOVA", 2) in result["top_statistics"] or ("ANOVA", 2) in result["top_statistics"]

    def test_year_distribution(self):
        papers = [{"year": 2020}, {"year": 2021}, {"year": 2021}, {}]
        result = TrendAnalyzer().analyze(papers)
        assert 2021 in result["year_distribution"]
        assert result["year_distribution"][2021] == 2
