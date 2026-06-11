"""Tests for unified litmind config"""

import os


class TestUnifiedConfig:
    def test_config_imports(self):
        """统一配置可以被各模块导入"""
        from litmind.config import (
            KB_EMBEDDING_MODEL, KB_DEFAULT_TOP_K,
            LLM_MODEL, LLM_PROVIDER,
            CACHE_TTL_SECONDS,
        )
        assert KB_EMBEDDING_MODEL == "BAAI/bge-small-zh-v1.5"
        assert KB_DEFAULT_TOP_K == 10
        assert LLM_MODEL == "claude-sonnet-4-20250514"
        assert LLM_PROVIDER == "anthropic"
        assert CACHE_TTL_SECONDS == 300

    def test_env_override(self, monkeypatch):
        """环境变量可覆写配置"""
        monkeypatch.setenv("LITMIND_KB_EMBEDDING_MODEL", "custom-model")
        monkeypatch.setenv("LITMIND_CACHE_TTL_SECONDS", "999")

        # 重新导入以触发 env 读取
        import importlib
        import litmind.config
        importlib.reload(litmind.config)

        assert litmind.config.KB_EMBEDDING_MODEL == "custom-model"
        assert litmind.config.CACHE_TTL_SECONDS == 999

    def test_env_override_int(self, monkeypatch):
        """整型环境变量正确解析"""
        monkeypatch.setenv("LITMIND_KB_DEFAULT_TOP_K", "50")
        monkeypatch.setenv("LITMIND_REVIEW_MAX_PAPERS", "100")

        import importlib
        import litmind.config
        importlib.reload(litmind.config)

        assert litmind.config.KB_DEFAULT_TOP_K == 50
        assert litmind.config.REVIEW_MAX_PAPERS == 100

    def test_env_override_float(self, monkeypatch):
        """浮点型环境变量正确解析"""
        monkeypatch.setenv("LITMIND_EV_HIGH_SIMILARITY", "0.9")
        monkeypatch.setenv("LITMIND_EV_CONFIDENCE_WEIGHT_COUNT", "0.5")

        import importlib
        import litmind.config
        importlib.reload(litmind.config)

        assert litmind.config.EV_HIGH_SIMILARITY == 0.9
        assert litmind.config.EV_CONFIDENCE_WEIGHT_COUNT == 0.5

    def test_evidence_config_inherits(self):
        """evidence config.py 正确继承统一配置"""
        from litmind_evidence.config import (
            DEFAULT_TOP_K, CLASSIFIER_MODEL, CACHE_TTL_SECONDS,
        )
        assert DEFAULT_TOP_K == 20  # evidence 的默认值
        assert CLASSIFIER_MODEL == "claude-sonnet-4-20250514"
        assert CACHE_TTL_SECONDS == 300

    def test_knowledge_config_inherits(self):
        """knowledge config.py 正确继承统一配置"""
        from litmind_knowledge.config import EMBEDDING_MODEL, DEFAULT_TOP_K
        assert EMBEDDING_MODEL == "BAAI/bge-small-zh-v1.5"
        assert DEFAULT_TOP_K == 10

    def test_discussion_config_inherits(self):
        """discussion config.py 正确继承统一配置"""
        from litmind_discussion.config import COMPOSER_MODEL, EVIDENCE_TOP_K
        assert COMPOSER_MODEL == "claude-sonnet-4-20250514"
        assert EVIDENCE_TOP_K == 10

    def test_review_config_inherits(self):
        """review config.py 正确继承统一配置"""
        from litmind_review.config import (
            REVIEW_MAX_PAPERS, REVIEW_MIN_THEMES, REVIEW_MAX_THEMES,
        )
        assert REVIEW_MAX_PAPERS == 50
        assert REVIEW_MIN_THEMES == 3
        assert REVIEW_MAX_THEMES == 7

    def test_chat_config_inherits(self):
        """chat config.py 正确继承统一配置"""
        from litmind_chat.config import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL, DEFAULT_TOP_K
        assert DEFAULT_LLM_PROVIDER == "anthropic"
        assert DEFAULT_LLM_MODEL == "claude-sonnet-4-20250514"
        assert DEFAULT_TOP_K == 10
