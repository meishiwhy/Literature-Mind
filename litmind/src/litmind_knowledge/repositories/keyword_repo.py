"""KeywordRepository — 操作 keywords 表"""

from .base import BaseRepository
from ..database.tables import KeywordTable
from ..models.records import KeywordRecord
from sqlalchemy import select, delete


class KeywordRepository(BaseRepository):
    @property
    def model_class(self):
        return KeywordTable

    @property
    def record_class(self):
        return KeywordRecord

    def find_by_paper_id(self, paper_id: str) -> list[KeywordRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[KeywordRecord]:
        stmt = select(self.model_class).where(self.model_class.keyword.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
