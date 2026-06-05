"""PaperRepository — 操作 papers 表"""

from .base import BaseRepository, _snake_to_camel
from ..database.tables import PaperTable
from ..models.records import PaperRecord
from sqlalchemy import text


class PaperRepository(BaseRepository):
    @property
    def model_class(self):
        return PaperTable

    @property
    def record_class(self):
        return PaperRecord

    def search(self, query: str) -> list[PaperRecord]:
        stmt = text(f"""
            SELECT * FROM papers
            WHERE title LIKE '%{query}%'
               OR research_question LIKE '%{query}%'
               OR research_domain LIKE '%{query}%'
        """)
        results = self.session.execute(stmt).mappings().all()
        return [
            PaperRecord(**{_snake_to_camel(k): v for k, v in dict(r).items()})
            for r in results
        ]
