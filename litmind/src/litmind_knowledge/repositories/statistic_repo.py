"""StatisticRepository — 操作 statistics 表"""

from .base import BaseRepository
from ..database.tables import StatisticTable
from ..models.records import StatisticRecord
from sqlalchemy import select, delete


class StatisticRepository(BaseRepository):
    @property
    def model_class(self):
        return StatisticTable

    @property
    def record_class(self):
        return StatisticRecord

    def find_by_paper_id(self, paper_id: str) -> list[StatisticRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[StatisticRecord]:
        stmt = select(self.model_class).where(self.model_class.method.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
