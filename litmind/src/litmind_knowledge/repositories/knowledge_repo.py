"""KnowledgeRepository — 跨表组合查询"""

from sqlalchemy.orm import Session


class KnowledgeRepository:
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
