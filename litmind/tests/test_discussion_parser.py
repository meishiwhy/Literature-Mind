# tests/test_discussion_parser.py
import pytest
from litmind_discussion.parser import ResultParser
from litmind_discussion.models import ParsedResult


class TestResultParser:
    def setup_method(self):
        self.parser = ResultParser()

    def test_parse_single(self):
        results = self.parser.parse(["High stiffness shoes increased MTP ROM"])
        assert len(results) == 1
        assert results[0].original == "High stiffness shoes increased MTP ROM"
        assert isinstance(results[0], ParsedResult)

    def test_parse_multiple(self):
        results = self.parser.parse([
            "High stiffness shoes increased MTP ROM",
            "No significant difference in ankle ROM",
        ])
        assert len(results) == 2

    def test_parse_empty(self):
        results = self.parser.parse([])
        assert results == []

    def test_variable_extraction(self):
        results = self.parser.parse(["Flatfoot increased forefoot motion"])
        assert len(results[0].variables) >= 1

    def test_direction_detection(self):
        results = self.parser.parse(["X increased Y"])
        assert results[0].direction in ("increase", "decrease", "no_difference", "")
