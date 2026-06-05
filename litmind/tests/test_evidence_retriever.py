"""Tests for ClaimRetriever (requires KnowledgeBase)"""

import pytest
from litmind_evidence.retriever import ClaimRetriever


class TestClaimRetriever:
    def test_init_requires_kb(self):
        with pytest.raises(TypeError):
            ClaimRetriever()  # missing kb argument
