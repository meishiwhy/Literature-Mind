"""Tests for EvidenceCollector — 遍历用户结果，收集证据"""

import pytest
from litmind_discussion.collector import EvidenceCollector


class TestEvidenceCollector:
    def test_requires_service(self):
        with pytest.raises(TypeError):
            EvidenceCollector()
