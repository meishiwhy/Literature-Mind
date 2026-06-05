"""ClaimRepository — 操作 claims 表"""

from .base import BaseRepository
from ..database.tables import ClaimTable
from ..models.records import ClaimRecord
from sqlalchemy import select, delete


class ClaimRepository(BaseRepository):
    @property
    def model_class(self):
        return ClaimTable

    @property
    def record_class(self):
        return ClaimRecord

    def find_by_paper_id(self, paper_id: str) -> list[ClaimRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[ClaimRecord]:
        stmt = select(self.model_class).where(self.model_class.statement.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
