import pytest
from pydantic import ValidationError
from litmind_analyzer.models import Claim, ParticipantInfo, PaperAnalysis


class TestPaperAnalysis:
    def test_empty_analysis(self):
        a = PaperAnalysis()
        assert a.paperId == ""
        assert a.researchQuestion == ""
        assert a.methods == []
        assert a.claims == []
        assert a.participants.sampleSize is None
        assert a.participants.groups == []
        assert a.keywords == []

    def test_claim_model(self):
        c = Claim(statement="X causes Y", evidenceSource="Results")
        assert c.statement == "X causes Y"
        assert c.evidenceSource == "Results"

    def test_claim_defaults(self):
        c = Claim()
        assert c.statement == ""
        assert c.evidenceSource == ""

    def test_participant_info(self):
        p = ParticipantInfo(sampleSize=24, groups=["Flat", "Normal"], population="Healthy males")
        assert p.sampleSize == 24
        assert len(p.groups) == 2

    def test_full_analysis_from_dict(self):
        data = {
            "paperId": "TEST123",
            "researchQuestion": "Does X affect Y?",
            "researchDomain": "Biomechanics",
            "studyDesign": "Cross-sectional",
            "participants": {"sampleSize": 20, "groups": ["Flat", "Normal"], "population": "Adults"},
            "methods": ["3D motion capture", "Force plate"],
            "statistics": ["t-test", "ANOVA"],
            "variables": ["Foot arch", "GRF"],
            "outcomes": ["Peak GRF"],
            "mainFindings": ["Flat feet have higher GRF"],
            "claims": [{"statement": "X", "evidenceSource": "Results"}],
            "limitations": ["Small sample"],
            "futureDirections": ["Larger study needed"],
            "keywords": ["flatfoot", "landing"],
        }
        a = PaperAnalysis(**data)
        assert a.paperId == "TEST123"
        assert a.participants.sampleSize == 20
        assert len(a.claims) == 1

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            PaperAnalysis(participants="invalid")
