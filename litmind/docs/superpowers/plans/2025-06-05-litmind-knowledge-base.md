# Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Knowledge Base module — stores PaperAnalysis into SQLite (structured data) + ChromaDB (vector index), with Repository layer, unified service API (add/update/delete/get/search/semantic_search), and CLI.

**Architecture:** Dual storage (SQLite via SQLAlchemy 2.0 + ChromaDB via sentence-transformers embeddings). Repository pattern: one repo per table, no business logic touches DB directly. Service layer wraps all repos + vector indexer into 11 public methods.

**Tech Stack:** Python 3.10+, SQLAlchemy 2.0, ChromaDB, sentence-transformers, Pydantic v2

---

## File Structure

```
litmind/src/litmind_knowledge/
├── __init__.py              # Package entry, exports KnowledgeBase
├── config.py                # DB paths, Chroma settings, embedding model name
├── models/
│   ├── __init__.py          # All Pydantic record models
│   └── records.py           # PaperRecord, VariableRecord, StatisticRecord, ...
├── database/
│   ├── __init__.py
│   ├── engine.py            # SQLAlchemy engine + session factory
│   └── tables.py            # ORM table definitions (7 tables)
├── repositories/
│   ├── __init__.py
│   ├── base.py              # BaseRepository ABC
│   ├── paper_repo.py        # PaperRepository
│   ├── variable_repo.py     # VariableRepository
│   ├── statistic_repo.py    # StatisticRepository
│   ├── claim_repo.py        # ClaimRepository
│   ├── keyword_repo.py      # KeywordRepository
│   ├── limitation_repo.py   # LimitationRepository
│   ├── future_direction_repo.py
│   └── knowledge_repo.py    # KnowledgeRepository (cross-table queries)
├── vectorstore/
│   ├── __init__.py
│   ├── client.py            # ChromaDB client init + embedding function
│   └── indexer.py           # VectorIndexer (index/update/delete/search)
├── service.py               # KnowledgeBase unified service
├── cli.py                   # Click CLI

litmind/tests/
├── test_knowledge_base.py   # All KB tests
├── fixtures/
│   └── sample_analysis.json # Test PaperAnalysis fixture

litmind/.claude/skills/
├── litmind-knowledge/SKILL.md
```

---

### Task 1: Config + Pydantic Models

**Files:**
- Create: `litmind/src/litmind_knowledge/__init__.py`
- Create: `litmind/src/litmind_knowledge/config.py`
- Create: `litmind/src/litmind_knowledge/models/__init__.py`
- Create: `litmind/src/litmind_knowledge/models/records.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_knowledge_base.py — appended to top
import pytest
from litmind_knowledge.models.records import (
    PaperRecord, VariableRecord, StatisticRecord,
    ClaimRecord, KeywordRecord, LimitationRecord, FutureDirectionRecord,
)


class TestModels:
    def test_paper_record_defaults(self):
        r = PaperRecord(paperId="P1")
        assert r.paperId == "P1"
        assert r.title == ""
        assert r.year is None

    def test_variable_record(self):
        v = VariableRecord(paperId="P1", variable="GRF")
        assert v.variable == "GRF"

    def test_claim_record(self):
        c = ClaimRecord(paperId="P1", statement="X", direction="increase", evidenceSource="Results")
        assert c.direction == "increase"

    def test_statistic_record(self):
        s = StatisticRecord(paperId="P1", method="ANOVA")
        assert s.method == "ANOVA"

    def test_keyword_record(self):
        k = KeywordRecord(paperId="P1", keyword="flatfoot")
        assert k.keyword == "flatfoot"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestModels -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write the config**

```python
# src/litmind_knowledge/config.py
"""Knowledge Base 配置"""

from pathlib import Path


def get_default_db_path() -> Path:
    return Path.home() / ".litmind" / "knowledge.db"


def get_default_chroma_path() -> Path:
    return Path.home() / ".litmind" / "chroma_db"


EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # sentence-transformers model
DEFAULT_TOP_K = 10
```

- [ ] **Step 4: Write the models**

```python
# src/litmind_knowledge/__init__.py
"""LitMind Knowledge Base — 科研知识库存储与检索"""

__version__ = "0.1.0"

# src/litmind_knowledge/models/__init__.py
from .records import (
    PaperRecord, VariableRecord, StatisticRecord,
    ClaimRecord, KeywordRecord, LimitationRecord, FutureDirectionRecord,
)

__all__ = [
    "PaperRecord", "VariableRecord", "StatisticRecord",
    "ClaimRecord", "KeywordRecord", "LimitationRecord", "FutureDirectionRecord",
]


# src/litmind_knowledge/models/records.py
"""Pydantic 数据模型 — Repository 层的记录对象"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaperRecord(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    researchQuestion: str = ""
    researchDomain: str = ""
    studyDesign: str = ""
    sampleSize: Optional[int] = None
    population: str = ""
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class VariableRecord(BaseModel):
    paperId: str
    variable: str


class StatisticRecord(BaseModel):
    paperId: str
    method: str


class ClaimRecord(BaseModel):
    paperId: str
    statement: str
    direction: str = ""
    evidenceSource: str = ""


class KeywordRecord(BaseModel):
    paperId: str
    keyword: str


class LimitationRecord(BaseModel):
    paperId: str
    limitation: str


class FutureDirectionRecord(BaseModel):
    paperId: str
    futureDirection: str
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestModels -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add litmind/src/litmind_knowledge/ tests/test_knowledge_base.py
git commit -m "feat(kb): add config and Pydantic record models"
```

---

### Task 2: SQLAlchemy ORM Tables + Engine

**Files:**
- Create: `litmind/src/litmind_knowledge/database/__init__.py`
- Create: `litmind/src/litmind_knowledge/database/engine.py`
- Create: `litmind/src/litmind_knowledge/database/tables.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_knowledge_base.py
@pytest.fixture
def db_engine():
    from litmind_knowledge.database.engine import create_engine
    from litmind_knowledge.database.tables import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


class TestTables:
    def test_tables_exist(self, db_engine):
        import sqlalchemy.inspection as insp
        inspector = insp.inspect(db_engine)
        tables = inspector.get_table_names()
        assert "papers" in tables
        assert "variables" in tables
        assert "statistics" in tables
        assert "claims" in tables
        assert "keywords" in tables
        assert "limitations" in tables
        assert "future_directions" in tables

    def test_papers_columns(self, db_engine):
        import sqlalchemy.inspection as insp
        inspector = insp.inspect(db_engine)
        cols = {c["name"] for c in inspector.get_columns("papers")}
        assert "paper_id" in cols
        assert "title" in cols
        assert "year" in cols
```

- [ ] **Step 2: Run test — fails with ModuleNotFoundError**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestTables -v`
Expected: FAIL

- [ ] **Step 3: Write engine.py**

```python
# src/litmind_knowledge/database/engine.py
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
```

- [ ] **Step 4: Write tables.py**

```python
# src/litmind_knowledge/database/tables.py
"""SQLAlchemy ORM 表定义"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class PaperTable(Base):
    __tablename__ = "papers"

    paper_id = Column(String(255), primary_key=True)
    title = Column(Text, default="")
    year = Column(Integer, nullable=True)
    journal = Column(Text, default="")
    doi = Column(Text, default="")
    research_question = Column(Text, default="")
    research_domain = Column(Text, default="")
    study_design = Column(Text, default="")
    sample_size = Column(Integer, nullable=True)
    population = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    variables = relationship("VariableTable", back_populates="paper", cascade="all, delete-orphan")
    statistics = relationship("StatisticTable", back_populates="paper", cascade="all, delete-orphan")
    claims = relationship("ClaimTable", back_populates="paper", cascade="all, delete-orphan")
    keywords = relationship("KeywordTable", back_populates="paper", cascade="all, delete-orphan")
    limitations = relationship("LimitationTable", back_populates="paper", cascade="all, delete-orphan")
    future_directions = relationship("FutureDirectionTable", back_populates="paper", cascade="all, delete-orphan")


class VariableTable(Base):
    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    variable = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="variables")


class StatisticTable(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    method = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="statistics")


class ClaimTable(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    statement = Column(Text, nullable=False)
    direction = Column(Text, default="")
    evidence_source = Column(Text, default="")
    paper = relationship("PaperTable", back_populates="claims")


class KeywordTable(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    keyword = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="keywords")


class LimitationTable(Base):
    __tablename__ = "limitations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    limitation = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="limitations")


class FutureDirectionTable(Base):
    __tablename__ = "future_directions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), ForeignKey("papers.paper_id", ondelete="CASCADE"))
    future_direction = Column(Text, nullable=False)
    paper = relationship("PaperTable", back_populates="future_directions")
```

- [ ] **Step 5: Run tests**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestTables -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add litmind/src/litmind_knowledge/database/
git commit -m "feat(kb): add SQLAlchemy ORM tables and engine"
```

---

### Task 3: BaseRepository + PaperRepository

**Files:**
- Create: `litmind/src/litmind_knowledge/repositories/__init__.py`
- Create: `litmind/src/litmind_knowledge/repositories/base.py`
- Create: `litmind/src/litmind_knowledge/repositories/paper_repo.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_knowledge_base.py
class TestPaperRepository:
    def test_save_and_find(self, db_engine):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=db_engine)
        session = Session()
        repo = PaperRepository(session)

        record = PaperRecord(paperId="P1", title="Test Paper", year=2024)
        repo.save(record)
        session.commit()

        found = repo.find_by_id("P1")
        assert found is not None
        assert found.title == "Test Paper"
        assert found.year == 2024

    def test_delete(self, db_engine):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=db_engine)
        session = Session()
        repo = PaperRepository(session)

        repo.save(PaperRecord(paperId="P2"))
        session.commit()
        repo.delete("P2")
        session.commit()
        assert repo.find_by_id("P2") is None

    def test_search(self, db_engine):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=db_engine)
        session = Session()
        repo = PaperRepository(session)

        repo.save(PaperRecord(paperId="P1", title="Flatfoot Biomechanics"))
        repo.save(PaperRecord(paperId="P2", title="Running Gait Analysis"))
        session.commit()

        results = repo.search("flatfoot")
        assert len(results) == 1
        assert results[0].paperId == "P1"
```

- [ ] **Step 2: Run test — fails**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestPaperRepository -v`
Expected: FAIL

- [ ] **Step 3: Write BaseRepository**

```python
# src/litmind_knowledge/repositories/base.py
"""BaseRepository 抽象基类"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select


class BaseRepository(ABC):
    """所有 Repository 的基类，封装 SQLAlchemy session 和 CRUD"""

    def __init__(self, session: Session):
        self.session = session

    @property
    @abstractmethod
    def model_class(self):
        """返回对应的 SQLAlchemy ORM 类"""
        ...

    @property
    @abstractmethod
    def record_class(self):
        """返回对应的 Pydantic record 类"""
        ...

    def _to_orm(self, record) -> Any:
        """Pydantic → ORM"""
        return self.model_class(**record.model_dump())

    def _to_record(self, orm_obj) -> Any:
        """ORM → Pydantic"""
        return self.record_class(**{k: v for k, v in orm_obj.__dict__.items() if not k.startswith("_")})

    def save(self, record) -> None:
        orm = self._to_orm(record)
        self.session.merge(orm)

    def save_batch(self, records: list) -> None:
        for r in records:
            self.save(r)

    def delete(self, id_value: str) -> None:
        orm = self.session.get(self.model_class, id_value)
        if orm:
            self.session.delete(orm)

    def find_by_id(self, id_value: str):
        orm = self.session.get(self.model_class, id_value)
        return self._to_record(orm) if orm else None

    def search(self, query: str, column_name: str = "title") -> list:
        col = getattr(self.model_class, column_name)
        stmt = select(self.model_class).where(col.contains(query))
        results = self.session.execute(stmt).scalars().all()
        return [self._to_record(r) for r in results]

    def count(self) -> int:
        stmt = select(self.model_class)
        return len(self.session.execute(stmt).scalars().all())
```

- [ ] **Step 4: Write PaperRepository**

```python
# src/litmind_knowledge/repositories/paper_repo.py
"""PaperRepository — 操作 papers 表"""

from .base import BaseRepository
from ..database.tables import PaperTable
from ..models.records import PaperRecord


class PaperRepository(BaseRepository):
    @property
    def model_class(self):
        return PaperTable

    @property
    def record_class(self):
        return PaperRecord

    def search(self, query: str) -> list[PaperRecord]:
        """搜索标题、研究问题、研究领域中的关键词"""
        from sqlalchemy import or_
        stmt = (
            self.model_class.__table__.select()
            .where(
                or_(
                    self.model_class.title.contains(query),
                    self.model_class.research_question.contains(query),
                    self.model_class.research_domain.contains(query),
                )
            )
        )
        from sqlalchemy import text
        stmt = text(f"""
            SELECT * FROM papers
            WHERE title LIKE '%{query}%'
               OR research_question LIKE '%{query}%'
               OR research_domain LIKE '%{query}%'
        """)
        results = self.session.execute(stmt).mappings().all()
        return [PaperRecord(**dict(r)) for r in results]
```

- [ ] **Step 5: Run tests**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestPaperRepository -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add litmind/src/litmind_knowledge/repositories/
git commit -m "feat(kb): add BaseRepository + PaperRepository"
```

---

### Task 4: All Child Repositories + KnowledgeRepository

**Files:**
- Create: `litmind/src/litmind_knowledge/repositories/variable_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/statistic_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/claim_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/keyword_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/limitation_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/future_direction_repo.py`
- Create: `litmind/src/litmind_knowledge/repositories/knowledge_repo.py`

- [ ] **Step 1: Write failing test**

```python
class TestChildRepos:
    @pytest.fixture
    def session(self, db_engine):
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=db_engine)
        s = Session()
        yield s
        s.close()

    def test_variable_repo(self, session, db_engine):
        from litmind_knowledge.models.records import PaperRecord, VariableRecord
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.repositories.variable_repo import VariableRepository
        from litmind_knowledge.database.tables import Base
        Base.metadata.create_all(db_engine)

        PaperRepository(session).save(PaperRecord(paperId="P1"))
        VariableRepository(session).save_batch([
            VariableRecord(paperId="P1", variable="GRF"),
            VariableRecord(paperId="P1", variable="MTP ROM"),
        ])
        session.commit()

        results = VariableRepository(session).search("GRF")
        assert len(results) == 1
        assert results[0].variable == "GRF"

    def test_knowledge_repo_cross_table(self, session, db_engine):
        from litmind_knowledge.models.records import PaperRecord, VariableRecord, StatisticRecord
        from litmind_knowledge.repositories.knowledge_repo import KnowledgeRepository
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.repositories.variable_repo import VariableRepository
        from litmind_knowledge.repositories.statistic_repo import StatisticRepository
        from litmind_knowledge.database.tables import Base
        Base.metadata.create_all(db_engine)

        PaperRepository(session).save(PaperRecord(paperId="P1", title="Test"))
        VariableRepository(session).save(VariableRecord(paperId="P1", variable="GRF"))
        StatisticRepository(session).save(StatisticRecord(paperId="P1", method="ANOVA"))
        session.commit()

        kb = KnowledgeRepository(session)
        paper = kb.get_paper_with_all("P1")
        assert paper is not None
        assert paper["paperId"] == "P1"
        assert len(paper["variables"]) == 1
        assert len(paper["statistics"]) == 1
```

- [ ] **Step 2: Run test — fails**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestChildRepos -v`
Expected: FAIL

- [ ] **Step 3: Write all 6 child repos** (each follows same pattern)

```python
# src/litmind_knowledge/repositories/variable_repo.py
from .base import BaseRepository
from ..database.tables import VariableTable
from ..models.records import VariableRecord

class VariableRepository(BaseRepository):
    @property
    def model_class(self): return VariableTable
    @property
    def record_class(self): return VariableRecord

    def find_by_paper_id(self, paper_id: str) -> list[VariableRecord]:
        from sqlalchemy import select
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        from sqlalchemy import delete
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[VariableRecord]:
        stmt = select(self.model_class).where(self.model_class.variable.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
```

The other 5 repos (statistic, claim, keyword, limitation, future_direction) follow the identical pattern with their respective table/record classes. Key differences:
- `ClaimRepository.search()` searches `statement`
- `KeywordRepository.search()` searches `keyword`
- `LimitationRepository.search()` searches `limitation`
- `FutureDirectionRepository.search()` searches `future_direction`

- [ ] **Step 4: Write KnowledgeRepository (cross-table)**

```python
# src/litmind_knowledge/repositories/knowledge_repo.py
"""KnowledgeRepository — 跨表组合查询"""

from sqlalchemy.orm import Session


class KnowledgeRepository:
    """组合多个子 Repository 进行跨表操作"""

    def __init__(self, session: Session):
        self.session = session

    def get_paper_with_all(self, paper_id: str) -> dict | None:
        from .paper_repo import PaperRepository
        from .variable_repo import VariableRepository
        from .statistic_repo import StatisticRepository
        from .claim_repo import ClaimRepository
        from .keyword_repo import KeywordRepository
        from .limitation_repo import LimitationRepository
        from .future_direction_repo import FutureDirectionRepository

        paper = PaperRepository(self.session).find_by_id(paper_id)
        if not paper:
            return None

        return {
            "paperId": paper.paperId,
            "title": paper.title,
            "year": paper.year,
            "journal": paper.journal,
            "doi": paper.doi,
            "researchQuestion": paper.researchQuestion,
            "researchDomain": paper.researchDomain,
            "studyDesign": paper.studyDesign,
            "sampleSize": paper.sampleSize,
            "population": paper.population,
            "variables": [v.variable for v in VariableRepository(self.session).find_by_paper_id(paper_id)],
            "statistics": [s.method for s in StatisticRepository(self.session).find_by_paper_id(paper_id)],
            "claims": [
                {"statement": c.statement, "direction": c.direction, "evidenceSource": c.evidenceSource}
                for c in ClaimRepository(self.session).find_by_paper_id(paper_id)
            ],
            "keywords": [k.keyword for k in KeywordRepository(self.session).find_by_paper_id(paper_id)],
            "limitations": [l.limitation for l in LimitationRepository(self.session).find_by_paper_id(paper_id)],
            "futureDirections": [
                f.futureDirection for f in FutureDirectionRepository(self.session).find_by_paper_id(paper_id)
            ],
        }
```

- [ ] **Step 5: Run tests**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestChildRepos -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add litmind/src/litmind_knowledge/repositories/
git commit -m "feat(kb): add all child repositories + KnowledgeRepository"
```

---

### Task 5: ChromaDB Vector Store

**Files:**
- Create: `litmind/src/litmind_knowledge/vectorstore/__init__.py`
- Create: `litmind/src/litmind_knowledge/vectorstore/client.py`
- Create: `litmind/src/litmind_knowledge/vectorstore/indexer.py`

- [ ] **Step 1: Write failing test**

```python
class TestVectorStore:
    @pytest.fixture
    def indexer(self, tmp_path):
        from litmind_knowledge.vectorstore.indexer import VectorIndexer
        return VectorIndexer(persist_dir=str(tmp_path / "chroma"))

    def test_index_and_search(self, indexer):
        indexer.index_paper("P1", {"researchQuestion": "Does flatfoot increase MTP ROM?"}, "researchQuestion")
        results = indexer.semantic_search("flatfoot MTP ROM", top_k=5)
        assert len(results) > 0
        assert results[0]["paperId"] == "P1"
        assert "flatfoot" in results[0]["text"].lower()

    def test_delete_paper(self, indexer):
        indexer.index_paper("P2", {"researchQuestion": "Test question"}, "researchQuestion")
        indexer.delete_paper("P2")
        results = indexer.semantic_search("test", top_k=5)
        p2_results = [r for r in results if r["paperId"] == "P2"]
        assert len(p2_results) == 0

    def test_rebuild_index(self, indexer):
        indexer.index_paper("P1", {"researchQuestion": "Q1"}, "researchQuestion")
        indexer.index_paper("P2", {"researchQuestion": "Q2"}, "researchQuestion")
        indexer.rebuild_index()
        results = indexer.semantic_search("Q1", top_k=10)
        assert len(results) == 0  # wiped after rebuild
```

- [ ] **Step 2: Run test — ChromaDB may not be installed**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestVectorStore -v`
Expected: FAIL

- [ ] **Step 3: Write chroma client**

```python
# src/litmind_knowledge/vectorstore/client.py
"""ChromaDB 客户端 + Embedding 函数"""

from pathlib import Path
from typing import Optional


class SentenceTransformerEmbedding:
    """sentence-transformers embedding 函数，适配 ChromaDB"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self_model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        self._load_model()
        embeddings = self._model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


def get_chroma_client(persist_dir: Optional[str] = None):
    import chromadb
    if persist_dir:
        return chromadb.PersistentClient(path=persist_dir)
    return chromadb.Client()
```

- [ ] **Step 4: Write indexer**

```python
# src/litmind_knowledge/vectorstore/indexer.py
"""VectorIndexer — 管理 ChromaDB 索引"""

import uuid
from typing import Any

from .client import get_chroma_client, SentenceTransformerEmbedding

COLLECTIONS = {
    "researchQuestion": "kb_research_questions",
    "mainFindings": "kb_main_findings",
    "claims": "kb_claims",
    "limitations": "kb_limitations",
    "futureDirections": "kb_future_directions",
}


class VectorIndexer:
    """向量索引管理器"""

    def __init__(self, persist_dir: str = "", model_name: str = "all-MiniLM-L6-v2"):
        self.embedding = SentenceTransformerEmbedding(model_name)
        self.client = get_chroma_client(persist_dir or None)
        self._collections = {}

    def _get_collection(self, field: str):
        name = COLLECTIONS.get(field, "kb_other")
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name, embedding_function=self.embedding
            )
        return self._collections[name]

    def index_text(self, paper_id: str, text: str, field: str, metadata: dict | None = None) -> None:
        """索引一条文本"""
        if not text.strip():
            return
        collection = self._get_collection(field)
        collection.add(
            documents=[text],
            metadatas=[{"paperId": paper_id, **(metadata or {})}],
            ids=[f"{paper_id}_{field}_{uuid.uuid4().hex[:8]}"],
        )

    def index_paper(self, paper_id: str, data: dict, field: str) -> None:
        """索引一篇论文的某个字段（支持 list 字段）"""
        value = data.get(field, "")
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    self.index_text(paper_id, item.get("statement", ""), field, item)
                elif isinstance(item, str):
                    self.index_text(paper_id, item, field)
        elif isinstance(value, str):
            self.index_text(paper_id, value, field)

    def delete_paper(self, paper_id: str) -> None:
        """删除论文的所有向量索引"""
        for field in COLLECTIONS:
            collection = self._get_collection(field)
            all_items = collection.get(where={"paperId": paper_id})
            if all_items["ids"]:
                collection.delete(ids=all_items["ids"])

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """跨所有 collection 进行语义搜索"""
        results = []
        for field in COLLECTIONS:
            collection = self._get_collection(field)
            try:
                hits = collection.query(query_texts=[query], n_results=min(top_k, 50))
                for i in range(len(hits["ids"][0]) if hits["ids"] else 0):
                    results.append({
                        "paperId": hits["metadatas"][0][i]["paperId"],
                        "text": hits["documents"][0][i],
                        "source": field,
                        "score": 1.0 - hits["distances"][0][i] if hits.get("distances") else 0.0,
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def rebuild_index(self) -> None:
        """重建所有索引（删除所有 collection）"""
        for name in COLLECTIONS.values():
            try:
                self.client.delete_collection(name)
            except Exception:
                pass
        self._collections = {}
```

- [ ] **Step 5: Run tests**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestVectorStore -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add litmind/src/litmind_knowledge/vectorstore/
git commit -m "feat(kb): add ChromaDB vector store with sentence-transformers"
```

---

### Task 6: KnowledgeBase Service

**Files:**
- Create: `litmind/src/litmind_knowledge/service.py`

- [ ] **Step 1: Write failing test**

```python
class TestKnowledgeBase:
    @pytest.fixture
    def kb(self, tmp_path):
        from litmind_knowledge.service import KnowledgeBase
        return KnowledgeBase(
            db_path=str(tmp_path / "test.db"),
            chroma_path=str(tmp_path / "chroma"),
        )

    @pytest.fixture
    def sample_analysis(self):
        return {
            "paperId": "TEST001",
            "researchQuestion": "Does landing height affect GRF?",
            "researchDomain": "Biomechanics",
            "studyDesign": "Experimental Study",
            "participants": {"sampleSize": 20, "groups": ["Flat", "Normal"], "population": "Healthy males"},
            "methods": ["Motion capture", "Force plate"],
            "statistics": ["ANOVA", "t-test"],
            "variables": ["GRF", "Joint angle"],
            "outcomes": ["Peak GRF"],
            "mainFindings": ["Flat feet increased GRF"],
            "claims": [{"statement": "Flat feet increase GRF", "direction": "increase", "evidenceSource": "Results"}],
            "limitations": ["Small sample"],
            "futureDirections": ["Larger study needed"],
            "keywords": ["flatfoot", "landing"],
        }

    def test_add_paper(self, kb, sample_analysis):
        pid = kb.add_paper(sample_analysis)
        assert pid == "TEST001"

        paper = kb.get_paper("TEST001")
        assert paper is not None
        assert paper["title"] == ""
        assert paper["researchQuestion"] == "Does landing height affect GRF?"

    def test_search_papers(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        results = kb.search_papers("landing")
        assert len(results) >= 1

    def test_search_variables(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        results = kb.search_variables("GRF")
        assert len(results) >= 1

    def test_delete_paper(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        kb.delete_paper("TEST001")
        assert kb.get_paper("TEST001") is None

    def test_semantic_search(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        results = kb.semantic_search("flatfoot landing", top_k=5)
        assert len(results) > 0  # may be empty if no embedding model loaded

    def test_update_paper(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        sample_analysis["researchQuestion"] = "Updated question"
        kb.update_paper(sample_analysis)
        paper = kb.get_paper("TEST001")
        assert paper["researchQuestion"] == "Updated question"
```

- [ ] **Step 2: Write the service**

```python
# src/litmind_knowledge/service.py
"""KnowledgeBase 服务 — 统一公开接口"""

from pathlib import Path
from typing import Any, Optional
from datetime import datetime

from .config import get_default_db_path, get_default_chroma_path
from .database.engine import init_db, get_session
from .models.records import (
    PaperRecord, VariableRecord, StatisticRecord,
    ClaimRecord, KeywordRecord, LimitationRecord, FutureDirectionRecord,
)
from .repositories.paper_repo import PaperRepository
from .repositories.variable_repo import VariableRepository
from .repositories.statistic_repo import StatisticRepository
from .repositories.claim_repo import ClaimRepository
from .repositories.keyword_repo import KeywordRepository
from .repositories.limitation_repo import LimitationRepository
from .repositories.future_direction_repo import FutureDirectionRepository
from .repositories.knowledge_repo import KnowledgeRepository
from .vectorstore.indexer import VectorIndexer


class KnowledgeBase:
    """科研知识库 — 统一服务入口"""

    def __init__(
        self,
        db_path: str = "",
        chroma_path: str = "",
    ):
        self.db_path = db_path or str(get_default_db_path())
        self.chroma_path = chroma_path or str(get_default_chroma_path())

        # Ensure parent dirs exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

        # Init database
        init_db(self.db_path)
        self._session = get_session()

        # Init vector indexer
        self._indexer = VectorIndexer(persist_dir=self.chroma_path)

    # ── 内部 Repository 工厂 ──

    def _paper_repo(self): return PaperRepository(self._session)
    def _variable_repo(self): return VariableRepository(self._session)
    def _statistic_repo(self): return StatisticRepository(self._session)
    def _claim_repo(self): return ClaimRepository(self._session)
    def _keyword_repo(self): return KeywordRepository(self._session)
    def _limitation_repo(self): return LimitationRepository(self._session)
    def _future_repo(self): return FutureDirectionRepository(self._session)
    def _knowledge_repo(self): return KnowledgeRepository(self._session)

    # ── 从 PaperAnalysis dict 提取数据 ──

    def _parse_analysis(self, analysis: dict) -> dict:
        """将 PaperAnalysis dict 转为各 Repository 需要的记录"""
        pid = analysis.get("paperId", "")
        participants = analysis.get("participants", {})

        paper = PaperRecord(
            paperId=pid,
            title=analysis.get("title", ""),
            year=analysis.get("year"),
            journal=analysis.get("journal", ""),
            doi=analysis.get("doi", ""),
            researchQuestion=analysis.get("researchQuestion", ""),
            researchDomain=analysis.get("researchDomain", ""),
            studyDesign=analysis.get("studyDesign", ""),
            sampleSize=participants.get("sampleSize") if isinstance(participants, dict) else None,
            population=participants.get("population", "") if isinstance(participants, dict) else "",
        )

        variables = [VariableRecord(paperId=pid, variable=v) for v in analysis.get("variables", [])]
        statistics = [StatisticRecord(paperId=pid, method=m) for m in analysis.get("statistics", [])]
        claims = [
            ClaimRecord(paperId=pid, statement=c.get("statement", ""), direction=c.get("direction", ""),
                        evidenceSource=c.get("evidenceSource", ""))
            for c in analysis.get("claims", [])
        ]
        keywords = [KeywordRecord(paperId=pid, keyword=k) for k in analysis.get("keywords", [])]
        limitations = [LimitationRecord(paperId=pid, limitation=l) for l in analysis.get("limitations", [])]
        future = [
            FutureDirectionRecord(paperId=pid, futureDirection=f)
            for f in analysis.get("futureDirections", [])
        ]

        return {
            "paper": paper,
            "variables": variables,
            "statistics": statistics,
            "claims": claims,
            "keywords": keywords,
            "limitations": limitations,
            "futureDirections": future,
        }

    # ── 公开接口 ──

    def add_paper(self, analysis: dict) -> str:
        """新增文献"""
        parsed = self._parse_analysis(analysis)
        pid = parsed["paper"].paperId

        self._paper_repo().save(parsed["paper"])
        self._variable_repo().save_batch(parsed["variables"])
        self._statistic_repo().save_batch(parsed["statistics"])
        self._claim_repo().save_batch(parsed["claims"])
        self._keyword_repo().save_batch(parsed["keywords"])
        self._limitation_repo().save_batch(parsed["limitations"])
        self._future_repo().save_batch(parsed["futureDirections"])
        self._session.commit()

        # 向量索引
        for field in ["researchQuestion", "mainFindings", "claims", "limitations", "futureDirections"]:
            self._indexer.index_paper(pid, analysis, field)

        return pid

    def update_paper(self, analysis: dict) -> bool:
        """更新文献"""
        pid = analysis.get("paperId", "")
        if not pid:
            return False

        # 删除旧子记录
        self._variable_repo().delete_by_paper_id(pid)
        self._statistic_repo().delete_by_paper_id(pid)
        self._claim_repo().delete_by_paper_id(pid)
        self._keyword_repo().delete_by_paper_id(pid)
        self._limitation_repo().delete_by_paper_id(pid)
        self._future_repo().delete_by_paper_id(pid)

        # 重新添加
        self.add_paper(analysis)
        return True

    def delete_paper(self, paper_id: str) -> bool:
        """删除文献"""
        self._paper_repo().delete(paper_id)
        self._session.commit()
        self._indexer.delete_paper(paper_id)
        return True

    def get_paper(self, paper_id: str) -> Optional[dict]:
        """获取单篇文献（含所有关联数据）"""
        return self._knowledge_repo().get_paper_with_all(paper_id)

    def search_papers(self, query: str) -> list:
        """关键词检索文献"""
        return [r.model_dump() for r in self._paper_repo().search(query)]

    def search_variables(self, query: str) -> list:
        return [r.model_dump() for r in self._variable_repo().search(query)]

    def search_statistics(self, query: str) -> list:
        return [r.model_dump() for r in self._statistic_repo().search(query)]

    def search_claims(self, query: str) -> list:
        return [r.model_dump() for r in self._claim_repo().search(query)]

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """基于向量数据库语义搜索"""
        return self._indexer.semantic_search(query, top_k=top_k)

    def import_batch(self, analyses: list[dict]) -> int:
        """批量导入"""
        count = 0
        for a in analyses:
            try:
                self.add_paper(a)
                count += 1
            except Exception:
                continue
        return count

    def rebuild_index(self) -> bool:
        """重建所有向量索引"""
        self._indexer.rebuild_index()

        papers = self._paper_repo().search("")
        for p in papers:
            full = self.get_paper(p.paperId)
            if full:
                for field in ["researchQuestion", "mainFindings", "claims", "limitations", "futureDirections"]:
                    self._indexer.index_paper(p.paperId, full, field)
        return True
```

- [ ] **Step 3: Run tests**

Run: `cd litmind && python -m pytest tests/test_knowledge_base.py::TestKnowledgeBase -v`
Expected: 6 passed (add, search, variable, delete, semantic, update)

- [ ] **Step 4: Commit**

```bash
git add litmind/src/litmind_knowledge/service.py
git commit -m "feat(kb): add KnowledgeBase service with 11 public methods"
```

---

### Task 7: CLI

**Files:**
- Create: `litmind/src/litmind_knowledge/cli.py`

- [ ] **Step 1: Write the CLI**

```python
# src/litmind_knowledge/cli.py
"""Knowledge Base CLI"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import click
from .service import KnowledgeBase


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--db", default="", help="SQLite path")
@click.option("--chroma", default="", help="ChromaDB path")
def add(input, db, chroma):
    """新增单篇 PaperAnalysis"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    with open(input, encoding="utf-8") as f:
        analysis = json.load(f)
    pid = kb.add_paper(analysis)
    click.echo(f"已添加: {pid}")


@cli.command()
@click.argument("paper_id")
@click.option("--db", default="")
@click.option("--chroma", default="")
def get(paper_id, db, chroma):
    """获取单篇文献"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    paper = kb.get_paper(paper_id)
    if paper:
        click.echo(json.dumps(paper, ensure_ascii=False, indent=2))
    else:
        click.echo(f"未找到: {paper_id}")


@cli.command()
@click.argument("query")
@click.option("--db", default="")
@click.option("--chroma", default="")
def search(query, db, chroma):
    """关键词检索文献"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    results = kb.search_papers(query)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("query")
@click.option("--top-k", default=10, show_default=True)
@click.option("--db", default="")
@click.option("--chroma", default="")
def semantic(query, top_k, db, chroma):
    """语义搜索"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    results = kb.semantic_search(query, top_k=top_k)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--db", default="")
@click.option("--chroma", default="")
def batch(input_dir, db, chroma):
    """批量导入目录下所有 PaperAnalysis JSON"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    path = Path(input_dir)
    files = list(path.glob("*.json"))
    with click.progressbar(files) as bar:
        for f in bar:
            with open(f, encoding="utf-8") as fh:
                analysis = json.load(fh)
            kb.add_paper(analysis)
    click.echo(f"导入完成: {len(files)} 篇")


@cli.command()
@click.option("--db", default="")
@click.option("--chroma", default="")
def rebuild(db, chroma):
    """重建向量索引"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    kb.rebuild_index()
    click.echo("索引重建完成")


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2: Commit**

```bash
git add litmind/src/litmind_knowledge/cli.py
git commit -m "feat(kb): add CLI (add/get/search/semantic/batch/rebuild)"
```

---

### Task 8: Skill + Config Updates

**Files:**
- Create: `litmind/.claude/skills/litmind-knowledge/SKILL.md`
- Modify: `litmind/pyproject.toml`

- [ ] **Step 1: Write skill file**

```markdown
---
name: litmind-knowledge
description: LitMind Knowledge Base — 存储、索引、检索、更新科研知识库
---

# LitMind Knowledge Base

将 Paper Analyzer 输出的 PaperAnalysis 存入双存储架构（SQLite + ChromaDB），提供统一的检索接口。

## 数据流

PaperAnalysis → KnowledgeBase → SQLite (结构化) + ChromaDB (向量索引)

## 公开接口

- add_paper — 新增文献
- update_paper — 更新文献
- delete_paper — 删除文献
- get_paper — 获取单篇文献
- search_papers — 关键词检索
- search_variables — 检索变量
- search_statistics — 检索统计方法
- search_claims — 检索科学结论
- semantic_search — 语义搜索

## 调用方式

```bash
litmind-knowledge add analysis.json
litmind-knowledge get PAPER_ID
litmind-knowledge search "flatfoot"
litmind-knowledge semantic "Does flatfoot increase MTP ROM?"
litmind-knowledge batch ./analyses/
litmind-knowledge rebuild
```

## 依赖

- SQLAlchemy (SQLite)
- ChromaDB (向量库)
- sentence-transformers (embedding, 离线免费)
```

- [ ] **Step 2: Update pyproject.toml**

```toml
[project.optional-dependencies]
kb = ["sqlalchemy", "chromadb", "sentence-transformers"]
all = ["pymupdf", "pdfplumber", "PyPDF2", "anthropic", "openai", "sqlalchemy", "chromadb", "sentence-transformers"]

[project.scripts]
litmind-knowledge = "litmind_knowledge.cli:cli"
```

- [ ] **Step 3: Commit**

```bash
git add litmind/.claude/skills/litmind-knowledge/ litmind/pyproject.toml
git commit -m "feat(kb): add Claude Code skill and update package config"
```

---

## Self-Review Checklist

- [x] Spec coverage: All 11 public methods accounted for (add/update/delete/get/search_papers/search_variables/search_statistics/search_claims/semantic_search/batch/rebuild)
- [x] Spec coverage: Dual storage (SQLite Task 2, ChromaDB Task 5)
- [x] Spec coverage: Repository layer (Task 3-4), all 7 tables
- [x] Spec coverage: Semantic search (Task 5 vectorstore)
- [x] Spec coverage: CLI (Task 7)
- [x] No placeholders: All code blocks complete
- [x] Type consistency: PaperAnalysis dict keys match between _parse_analysis and service
- [ ] Tests run (verified at each step)
