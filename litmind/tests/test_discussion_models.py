import pytest
from litmind_discussion.models import (
    DiscussionInput, DiscussionResult, DiscussionCitation,
    ParsedResult, CollectedEvidence,
)


class TestDiscussionInput:
    def test_defaults(self):
        d = DiscussionInput(studyTopic="Test", results=["R1"])
        assert d.studyTopic == "Test"
        assert d.results == ["R1"]


class TestDiscussionCitation:
    def test_defaults(self):
        c = DiscussionCitation(paperId="P1")
        assert c.paperId == "P1"
        assert c.section == ""

    def test_full(self):
        c = DiscussionCitation(paperId="P1", title="T", year=2024, section="intro")
        assert c.year == 2024


class TestDiscussionResult:
    def test_defaults(self):
        r = DiscussionResult()
        assert r.discussionDraft == ""
        assert r.citations == []


class TestParsedResult:
    def test_minimal(self):
        p = ParsedResult(original="X increased Y")
        assert p.original == "X increased Y"
        assert p.variables == []


class TestCollectedEvidence:
    def test_defaults(self):
        c = CollectedEvidence()
        assert c.by_result == {}
        assert c.supporting == []
