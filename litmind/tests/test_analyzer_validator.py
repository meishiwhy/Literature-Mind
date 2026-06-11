"""Tests for validator: field completeness and Pydantic repair"""

import pytest
from litmind_analyzer.validator import ensure_fields, validate_and_repair
from litmind_analyzer.models import PaperAnalysis


class TestEnsureFields:
    def test_fills_missing_optionals(self):
        result = ensure_fields({"paperId": "T1"})
        assert result["paperId"] == "T1"
        assert result["researchQuestion"] == ""
        assert result["methods"] == []
        assert result["participants"]["sampleSize"] is None

    def test_preserves_existing_values(self):
        data = {"paperId": "T1", "researchQuestion": "Does X?", "methods": ["test"]}
        result = ensure_fields(data)
        assert result["researchQuestion"] == "Does X?"
        assert result["methods"] == ["test"]

    def test_handles_none_values(self):
        result = ensure_fields({"paperId": None})
        assert result["paperId"] == ""

    def test_participants_default(self):
        result = ensure_fields({"paperId": "T1"})
        assert "participants" in result
        assert result["participants"]["sampleSize"] is None
        assert result["participants"]["groups"] == []

    def test_validate_and_repair_returns_paperanalysis(self):
        result = validate_and_repair({"paperId": "T1"})
        assert isinstance(result, PaperAnalysis)
        assert result.paperId == "T1"

    def test_deep_extraction_default_none(self):
        """deepExtraction 字段未提供时应为 None"""
        result = validate_and_repair({"paperId": "T1"})
        assert result.deepExtraction is None

    def test_deep_extraction_preserved(self):
        """deepExtraction 字段提供时应保留"""
        data = {
            "paperId": "T1",
            "deepExtraction": {
                "numericalFindings": [
                    {"condition": "A", "metric": "B", "value": 1.0, "unit": "m", "statistics": "", "context": ""},
                ],
                "experimentalProtocols": ["Protocol X"],
            },
        }
        result = validate_and_repair(data)
        assert result.deepExtraction is not None
        assert len(result.deepExtraction.numericalFindings) == 1
        assert result.deepExtraction.numericalFindings[0].value == 1.0
        assert len(result.deepExtraction.experimentalProtocols) == 1
