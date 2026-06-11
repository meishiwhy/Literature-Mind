"""Tests for CitationManager — 引用追踪、去重、提取"""

import pytest
from litmind_discussion.citation import CitationManager
from litmind_discussion.models import DiscussionCitation


class TestCitationManager:
    def setup_method(self):
        self.mgr = CitationManager()

    def test_add_citation(self):
        c = DiscussionCitation(paperId="P1", section="main_finding")
        self.mgr.add(c)
        assert len(self.mgr.get_all()) == 1
        assert self.mgr.get_all()[0].paperId == "P1"

    def test_deduplication(self):
        self.mgr.add(DiscussionCitation(paperId="P1", section="a"))
        self.mgr.add(DiscussionCitation(paperId="P1", section="b"))
        assert len(self.mgr.get_all()) == 2
        self.mgr.add(DiscussionCitation(paperId="P1", section="a"))
        assert len(self.mgr.get_all()) == 2

    def test_extract_citations(self):
        text = "This finding [P1] is consistent with prior work [P2]."
        extracted = self.mgr.extract_from_text(text)
        assert len(extracted) == 2
        assert "P1" in extracted
        assert "P2" in extracted

    def test_filter_known_removes_unknown(self):
        """不在 known_ids 中的 [paperId] 引用应被移除"""
        text = "Study [P1] shows [P99] results."
        filtered = self.mgr.filter_known(text, {"P1"})
        assert "[P1]" in filtered
        assert "[P99]" not in filtered  # P99 不在白名单中

    def test_filter_known_empty_text(self):
        assert self.mgr.filter_known("", {"P1"}) == ""

    def test_filter_known_all_known(self):
        text = "Both [P1] and [P2] are valid."
        filtered = self.mgr.filter_known(text, {"P1", "P2"})
        assert filtered == text

    def test_to_citation_list_filters_unknown(self):
        self.mgr.add(DiscussionCitation(paperId="P1", section="draft"))
        self.mgr.add(DiscussionCitation(paperId="P2", section="draft"))
        result = self.mgr.to_citation_list({"P1"})
        assert len(result) == 1
        assert result[0].paperId == "P1"

    def test_get_by_section(self):
        self.mgr.add(DiscussionCitation(paperId="P1", section="intro"))
        self.mgr.add(DiscussionCitation(paperId="P2", section="methods"))
        self.mgr.add(DiscussionCitation(paperId="P3", section="intro"))
        results = self.mgr.get_by_section("intro")
        assert len(results) == 2
        assert results[0].paperId == "P1"
        assert results[1].paperId == "P3"

    def test_add_batch(self):
        citations = [
            DiscussionCitation(paperId="P1", section="a"),
            DiscussionCitation(paperId="P2", section="b"),
        ]
        self.mgr.add_batch(citations)
        assert len(self.mgr.get_all()) == 2
