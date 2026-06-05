import json
import pytest
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_analyze_with_mock_provider():
    """测试 pipeline 流程（mock LLM）"""
    from litmind_analyzer.analyzer import analyze_paper
    from litmind_analyzer.models import PaperAnalysis
    from litmind_analyzer.provider import LLMProvider

    class MockProvider(LLMProvider):
        def analyze(self, system_prompt, user_prompt):
            return {
                "paperId": "",
                "researchQuestion": "Does landing height affect GRF?",
                "researchDomain": "Biomechanics",
                "studyDesign": "Experimental Study",
                "participants": {"sampleSize": 20, "groups": ["Flat", "Normal"], "population": "Healthy males"},
                "methods": ["3D motion capture", "Force plate", "EMG"],
                "statistics": ["Repeated measures ANOVA", "Independent t-test"],
                "variables": ["Foot arch", "Landing height", "GRF", "Joint angles"],
                "outcomes": ["Peak GRF", "Peak joint angle", "Muscle activation"],
                "mainFindings": ["Flat feet had greater peak GRF at all heights"],
                "claims": [
                    {"statement": "Flat feet increase GRF during landing",
                     "evidenceSource": "Results"}
                ],
                "limitations": ["Small sample size"],
                "futureDirections": ["Larger studies needed"],
                "keywords": ["flatfoot", "landing", "GRF", "EMG"],
            }

    fixture = FIXTURE_DIR / "chang2012_parsed.json"
    with open(fixture, encoding="utf-8") as f:
        paper = json.load(f)

    provider = MockProvider()
    result = analyze_paper(paper, provider)

    assert isinstance(result, PaperAnalysis)
    assert result.researchQuestion == "Does landing height affect GRF?"
    assert len(result.methods) == 3
    assert result.participants.sampleSize == 20
    assert len(result.claims) == 1
    assert result.paperId == paper.get("paperKey", "")


def test_analyze_empty_sections():
    """空内容不应崩溃"""
    from litmind_analyzer.analyzer import analyze_paper
    from litmind_analyzer.models import PaperAnalysis
    from litmind_analyzer.provider import LLMProvider

    class MockProvider(LLMProvider):
        def analyze(self, system_prompt, user_prompt):
            return {"paperId": "", "researchQuestion": ""}

    paper = {"paperKey": "EMPTY", "sections": {}}
    result = analyze_paper(paper, MockProvider())
    assert isinstance(result, PaperAnalysis)
    assert result.paperId == "EMPTY"
