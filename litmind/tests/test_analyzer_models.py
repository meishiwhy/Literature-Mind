import pytest
from pydantic import ValidationError
from litmind_analyzer.models import Claim, ParticipantInfo, PaperAnalysis, NumericalFinding, DeepExtraction


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


class TestNumericalFinding:
    def test_defaults(self):
        n = NumericalFinding()
        assert n.condition == ""
        assert n.metric == ""
        assert n.value is None
        assert n.unit == ""
        assert n.statistics == ""

    def test_full(self):
        n = NumericalFinding(
            condition="Flatfoot + CS shoe",
            metric="Ankle eversion ROM",
            value=12.3,
            unit="deg",
            statistics="p=0.003",
            context="greater than NS shoe",
        )
        assert n.value == 12.3
        assert n.unit == "deg"

    def test_partial(self):
        n = NumericalFinding(metric="Peak GRF", value=3.2)
        assert n.metric == "Peak GRF"
        assert n.unit == ""  # 默认


class TestDeepExtraction:
    def test_defaults(self):
        d = DeepExtraction()
        assert d.numericalFindings == []
        assert d.experimentalProtocols == []

    def test_with_data(self):
        d = DeepExtraction(
            numericalFindings=[
                NumericalFinding(condition="A", metric="B", value=1.0),
            ],
            experimentalProtocols=["Drop: 45cm", "Rate: 1000Hz"],
        )
        assert len(d.numericalFindings) == 1
        assert len(d.experimentalProtocols) == 2


class TestPaperAnalysisDeepExtraction:
    def test_deep_extraction_default_none(self):
        a = PaperAnalysis()
        assert a.deepExtraction is None

    def test_deep_extraction_with_data(self):
        a = PaperAnalysis(
            paperId="D001",
            deepExtraction=DeepExtraction(
                numericalFindings=[
                    NumericalFinding(metric="GRF", value=3.2, unit="BW"),
                ],
            ),
        )
        assert a.deepExtraction is not None
        assert len(a.deepExtraction.numericalFindings) == 1
        assert a.deepExtraction.numericalFindings[0].value == 3.2
