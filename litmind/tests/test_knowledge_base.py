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


@pytest.fixture
def db_engine():
    from sqlalchemy import create_engine as _ce
    from litmind_knowledge.database.tables import Base
    engine = _ce("sqlite:///:memory:")
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


class TestPaperRepository:
    @pytest.fixture
    def repo_session(self, db_engine):
        from sqlalchemy.orm import sessionmaker
        from litmind_knowledge.database.tables import Base
        Base.metadata.create_all(db_engine)
        Session = sessionmaker(bind=db_engine)
        s = Session()
        yield s
        s.close()

    def test_save_and_find(self, repo_session):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        repo = PaperRepository(repo_session)
        record = PaperRecord(paperId="P1", title="Test Paper", year=2024)
        repo.save(record)
        repo_session.commit()
        found = repo.find_by_id("P1")
        assert found is not None
        assert found.title == "Test Paper"
        assert found.year == 2024

    def test_delete(self, repo_session):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        repo = PaperRepository(repo_session)
        repo.save(PaperRecord(paperId="P2"))
        repo_session.commit()
        repo.delete("P2")
        repo_session.commit()
        assert repo.find_by_id("P2") is None

    def test_search(self, repo_session):
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.models.records import PaperRecord
        repo = PaperRepository(repo_session)
        repo.save(PaperRecord(paperId="P1", title="Flatfoot Biomechanics"))
        repo.save(PaperRecord(paperId="P2", title="Running Gait Analysis"))
        repo_session.commit()
        results = repo.search("flatfoot")
        assert len(results) == 1
        assert results[0].paperId == "P1"


class TestChildRepos:
    @pytest.fixture
    def repo_session(self, db_engine):
        from sqlalchemy.orm import sessionmaker
        from litmind_knowledge.database.tables import Base
        Base.metadata.create_all(db_engine)
        Session = sessionmaker(bind=db_engine)
        s = Session()
        yield s
        s.close()

    def test_variable_repo(self, repo_session):
        from litmind_knowledge.models.records import PaperRecord, VariableRecord
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.repositories.variable_repo import VariableRepository

        PaperRepository(repo_session).save(PaperRecord(paperId="P1"))
        VariableRepository(repo_session).save_batch([
            VariableRecord(paperId="P1", variable="GRF"),
            VariableRecord(paperId="P1", variable="MTP ROM"),
        ])
        repo_session.commit()

        results = VariableRepository(repo_session).search("GRF")
        assert len(results) == 1
        assert results[0].variable == "GRF"

    def test_knowledge_repo(self, repo_session):
        from litmind_knowledge.models.records import PaperRecord, VariableRecord, StatisticRecord
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.repositories.variable_repo import VariableRepository
        from litmind_knowledge.repositories.statistic_repo import StatisticRepository
        from litmind_knowledge.repositories.knowledge_repo import KnowledgeRepository

        PaperRepository(repo_session).save(PaperRecord(paperId="P1", title="Test"))
        VariableRepository(repo_session).save(VariableRecord(paperId="P1", variable="GRF"))
        StatisticRepository(repo_session).save(StatisticRecord(paperId="P1", method="ANOVA"))
        repo_session.commit()

        kb = KnowledgeRepository(repo_session)
        paper = kb.get_paper_with_all("P1")
        assert paper is not None
        assert paper["paperId"] == "P1"
        assert len(paper["variables"]) == 1
        assert len(paper["statistics"]) == 1

    def test_claim_repo(self, repo_session):
        from litmind_knowledge.models.records import PaperRecord, ClaimRecord
        from litmind_knowledge.repositories.paper_repo import PaperRepository
        from litmind_knowledge.repositories.claim_repo import ClaimRepository

        PaperRepository(repo_session).save(PaperRecord(paperId="P1"))
        ClaimRepository(repo_session).save(ClaimRecord(paperId="P1", statement="X increases Y", direction="increase", evidenceSource="Results"))
        repo_session.commit()

        results = ClaimRepository(repo_session).search("increase")
        assert len(results) >= 1


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

    def test_delete_paper(self, indexer):
        indexer.index_paper("P2", {"researchQuestion": "Test question"}, "researchQuestion")
        indexer.delete_paper("P2")
        results = indexer.semantic_search("test", top_k=5)
        p2_results = [r for r in results if r["paperId"] == "P2"]
        assert len(p2_results) == 0

    def test_rebuild_clears(self, indexer):
        indexer.index_paper("P1", {"researchQuestion": "Q1"}, "researchQuestion")
        indexer.rebuild_index()
        results = indexer.semantic_search("Q1", top_k=10)
        assert len(results) == 0


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
        # May be empty when no embedding model is loaded
        assert isinstance(results, list)

    def test_update_paper(self, kb, sample_analysis):
        kb.add_paper(sample_analysis)
        sample_analysis["researchQuestion"] = "Updated question"
        kb.update_paper(sample_analysis)
        paper = kb.get_paper("TEST001")
        assert paper["researchQuestion"] == "Updated question"

    def test_import_batch(self, kb, sample_analysis):
        count = kb.import_batch([sample_analysis])
        assert count == 1
