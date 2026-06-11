"""
LitMind 统一配置入口

所有配置项可从环境变量覆写。优先级：
    环境变量 > 默认值

命名规范：LITMIND_<SECTION>_<KEY>
例如：LITMIND_KB_EMBEDDING_MODEL, LITMIND_EV_CACHE_TTL
"""

import os
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(f"LITMIND_{key}", default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(f"LITMIND_{key}", str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(f"LITMIND_{key}", str(default)))
    except (ValueError, TypeError):
        return default


# ── 路径 ────────────────────────────────────────────────

LITMIND_HOME = Path(_env("HOME", str(Path.home() / ".litmind")))

# ── Knowledge Base ──────────────────────────────────────

KB_DB_PATH = _env("KB_DB_PATH", str(LITMIND_HOME / "knowledge.db"))
KB_CHROMA_PATH = _env("KB_CHROMA_PATH", str(LITMIND_HOME / "chroma_db"))
KB_EMBEDDING_MODEL = _env("KB_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
KB_DEFAULT_TOP_K = _env_int("KB_DEFAULT_TOP_K", 10)

# ── Evidence Finder ─────────────────────────────────────

EV_DEFAULT_TOP_K = _env_int("EV_DEFAULT_TOP_K", 20)
EV_SEMANTIC_TOP_K = _env_int("EV_SEMANTIC_TOP_K", 15)
EV_LIKE_TOP_K = _env_int("EV_LIKE_TOP_K", 20)
EV_STRONG_SUPPORT_MIN = _env_int("EV_STRONG_SUPPORT_MIN", 3)
EV_MODERATE_SUPPORT_RATIO = _env_float("EV_MODERATE_SUPPORT_RATIO", 2.0)
EV_HIGH_SIMILARITY = _env_float("EV_HIGH_SIMILARITY", 0.75)
EV_CONFIDENCE_WEIGHT_COUNT = _env_float("EV_CONFIDENCE_WEIGHT_COUNT", 0.4)
EV_CONFIDENCE_WEIGHT_CONSISTENCY = _env_float("EV_CONFIDENCE_WEIGHT_CONSISTENCY", 0.35)
EV_CONFIDENCE_WEIGHT_SIMILARITY = _env_float("EV_CONFIDENCE_WEIGHT_SIMILARITY", 0.25)
EV_CLASSIFIER_BATCH_SIZE = _env_int("EV_CLASSIFIER_BATCH_SIZE", 5)

# ── LLM 模型（共享） ────────────────────────────────────

LLM_PROVIDER = _env("LLM_PROVIDER", "anthropic")
LLM_MODEL = _env("LLM_MODEL", "claude-sonnet-4-20250514")

# ── 缓存（共享） ────────────────────────────────────────

CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 300)
CACHE_MAX_SIZE = _env_int("CACHE_MAX_SIZE", 100)

# ── Chat ────────────────────────────────────────────────

CHAT_TOP_K = _env_int("CHAT_TOP_K", 10)

# ── Discussion ──────────────────────────────────────────

DISCUSSION_EVIDENCE_TOP_K = _env_int("DISCUSSION_EVIDENCE_TOP_K", 10)
DISCUSSION_MAX_RESULTS = _env_int("DISCUSSION_MAX_RESULTS", 10)
DISCUSSION_CACHE_MAX_SIZE = _env_int("DISCUSSION_CACHE_MAX_SIZE", 50)

# ── Review ──────────────────────────────────────────────

REVIEW_MAX_PAPERS = _env_int("REVIEW_MAX_PAPERS", 50)
REVIEW_MIN_THEMES = _env_int("REVIEW_MIN_THEMES", 3)
REVIEW_MAX_THEMES = _env_int("REVIEW_MAX_THEMES", 7)
REVIEW_CACHE_MAX_SIZE = _env_int("REVIEW_CACHE_MAX_SIZE", 30)
REVIEW_CACHE_TTL = _env_int("REVIEW_CACHE_TTL", 600)
