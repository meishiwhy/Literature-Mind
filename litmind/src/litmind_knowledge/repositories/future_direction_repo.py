"""FutureDirectionRepository — 操作 future_directions 表"""

from .base import BaseRepository
from ..database.tables import FutureDirectionTable
from ..models.records import FutureDirectionRecord
from sqlalchemy import select, delete


class FutureDirectionRepository(BaseRepository):
    @property
    def model_class(self):
        return FutureDirectionTable

    @property
    def record_class(self):
        return FutureDirectionRecord

    def find_by_paper_id(self, paper_id: str) -> list[FutureDirectionRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[FutureDirectionRecord]:
        stmt = select(self.model_class).where(self.model_class.future_direction.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
