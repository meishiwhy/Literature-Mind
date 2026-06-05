"""SQLAlchemy engine + session factory"""

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import sessionmaker, Session

_ENGINE = None
_SESSION_FACTORY = None


def get_engine(db_path: str = ""):
    global _ENGINE
    if _ENGINE is None:
        if not db_path:
            from ..config import get_default_db_path
            db_path = str(get_default_db_path())
        _ENGINE = _create_engine(f"sqlite:///{db_path}", echo=False)
    return _ENGINE


def create_engine(db_path: str):
    """Create engine for testing (bypasses global singleton)"""
    return _create_engine(db_path, echo=False)


def get_session() -> Session:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine())
    return _SESSION_FACTORY()


def init_db(db_path: str = ""):
    """Initialize database (create tables)"""
    from .tables import Base
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
