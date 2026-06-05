"""端到端测试：Zotero export → Parser → Analyzer (mock LLM)"""

import json
from pathlib import Path
from litmind_analyzer import PaperAnalysis, analyze_paper
from litmind_analyzer.provider import LLMProvider

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class MockProvider(LLMProvider):
    def analyze(self, system_prompt, user_prompt):
        return {
            "paperId": "",
            "researchQuestion": "Does landing height affect biomechanics in flat vs normal feet?",
            "researchDomain": "Biomechanics",
            "studyDesign": "Experimental Study",
            "participants": {"sampleSize": 20, "groups": ["Flat", "Normal"], "population": "Healthy males"},
            "methods": ["Vicon motion capture", "AMTI force plates", "Surface EMG"],
            "statistics": ["Repeated measures ANOVA", "Independent t-test", "Kolmogorov-Smirnov"],
            "variables": ["Foot arch type", "Landing height", "GRF", "Joint angle", "Muscle activation"],
            "outcomes": ["Peak GRF", "Peak joint angle", "Mean EMG amplitude"],
            "mainFindings": [
                "Flat feet group had greater peak GRF at all landing heights",
                "Hip joint angle showed compensatory strategy in flat feet",
                "AH and GA muscle activation was lower in flat feet group",
            ],
            "claims": [
                {"statement": "Flat feet increase GRF during drop landing", "evidenceSource": "Results"},
                {"statement": "Hip joint compensates for flat foot during landing", "evidenceSource": "Discussion"},
            ],
            "limitations": ["Small sample size (n=20)", "Only male subjects"],
            "futureDirections": ["Larger sample with various motor tasks"],
            "keywords": ["flatfoot", "landing", "GRF", "EMG", "biomechanics"],
        }


def test_end_to_end_mock():
    """使用真实 fixture + mock LLM 走通全流程"""
    fixture = FIXTURE_DIR / "chang2012_parsed.json"
    assert fixture.exists(), f"Fixture not found: {fixture}"

    with open(fixture, encoding="utf-8") as f:
        paper = json.load(f)

    provider = MockProvider()
    result = analyze_paper(paper, provider)

    assert isinstance(result, PaperAnalysis)
    assert result.paperId == paper.get("paperKey", "")
    assert result.researchDomain == "Biomechanics"
    assert result.studyDesign == "Experimental Study"
    assert result.participants.sampleSize == 20
    assert len(result.methods) >= 2
    assert len(result.mainFindings) >= 2
    assert len(result.claims) >= 1
    assert len(result.keywords) >= 3

    # 验证关键词对应
    assert "flatfoot" in [k.lower() for k in result.keywords] or \
           "flat feet" in [k.lower() for k in result.keywords]
