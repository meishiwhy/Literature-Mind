from pathlib import Path


def get_default_db_path() -> Path:
    return Path.home() / ".litmind" / "knowledge.db"


def get_default_chroma_path() -> Path:
    return Path.home() / ".litmind" / "chroma_db"


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 10
