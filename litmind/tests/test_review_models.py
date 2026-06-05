import pytest
from litmind_review.models import (
    ReviewInput, ReviewTheme, ResearchConsensus,
    ResearchControversy, ResearchGap, ReviewResult,
)
from litmind_discussion.models import DiscussionCitation


class TestReviewInput:
    def test_defaults(self):
        r = ReviewInput(topic="Flatfoot Biomechanics")
        assert r.topic == "Flatfoot Biomechanics"
        assert r.max_papers == 50


class TestReviewTheme:
    def test_minimal(self):
        t = ReviewTheme(name="Foot Kinematics", paperCount=5)
        assert t.name == "Foot Kinematics"
        assert t.paperIds == []


class TestResearchConsensus:
    def test_defaults(self):
        c = ResearchConsensus(statement="X is associated with Y")
        assert c.supportingPapers == 0


class TestResearchControversy:
    def test_defaults(self):
        c = ResearchControversy(statement="X improves Y")
        assert c.support == 0
        assert c.oppose == 0


class TestResearchGap:
    def test_minimal(self):
        g = ResearchGap(description="Few longitudinal studies")
        assert g.description == "Few longitudinal studies"


class TestReviewResult:
    def test_defaults(self):
        r = ReviewResult(topic="Test")
        assert r.paperCount == 0
        assert r.researchThemes == []
        assert r.reviewDraft == ""

    def test_with_all_fields(self):
        r = ReviewResult(
            topic="Test",
            paperCount=10,
            researchThemes=[ReviewTheme(name="T1", paperCount=5)],
            researchConsensus=[ResearchConsensus(statement="S1", supportingPapers=3)],
            reviewOutline={"Intro": ["Background", "Purpose"]},
            reviewDraft="Draft text...",
            citations=[DiscussionCitation(paperId="P1", section="draft")],
        )
        assert r.paperCount == 10
        assert len(r.researchThemes) == 1
        assert len(r.citations) == 1
