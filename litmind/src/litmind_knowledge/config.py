"""Knowledge Base 配置 — 从统一配置继承"""

from litmind.config import (
    KB_DB_PATH,
    KB_CHROMA_PATH,
    KB_EMBEDDING_MODEL,
    KB_DEFAULT_TOP_K,
)
from pathlib import Path


def get_default_db_path() -> Path:
    return Path(KB_DB_PATH)


def get_default_chroma_path() -> Path:
    return Path(KB_CHROMA_PATH)


EMBEDDING_MODEL = KB_EMBEDDING_MODEL
DEFAULT_TOP_K = KB_DEFAULT_TOP_K
