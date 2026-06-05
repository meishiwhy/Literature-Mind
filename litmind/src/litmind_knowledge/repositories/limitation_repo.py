"""LimitationRepository — 操作 limitations 表"""

from .base import BaseRepository
from ..database.tables import LimitationTable
from ..models.records import LimitationRecord
from sqlalchemy import select, delete


class LimitationRepository(BaseRepository):
    @property
    def model_class(self):
        return LimitationTable

    @property
    def record_class(self):
        return LimitationRecord

    def find_by_paper_id(self, paper_id: str) -> list[LimitationRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[LimitationRecord]:
        stmt = select(self.model_class).where(self.model_class.limitation.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
