"""VariableRepository — 操作 variables 表"""

from .base import BaseRepository
from ..database.tables import VariableTable
from ..models.records import VariableRecord
from sqlalchemy import select, delete


class VariableRepository(BaseRepository):
    @property
    def model_class(self):
        return VariableTable

    @property
    def record_class(self):
        return VariableRecord

    def find_by_paper_id(self, paper_id: str) -> list[VariableRecord]:
        stmt = select(self.model_class).where(self.model_class.paper_id == paper_id)
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]

    def delete_by_paper_id(self, paper_id: str) -> None:
        self.session.execute(delete(self.model_class).where(self.model_class.paper_id == paper_id))

    def search(self, query: str) -> list[VariableRecord]:
        stmt = select(self.model_class).where(self.model_class.variable.contains(query))
        return [self._to_record(r) for r in self.session.execute(stmt).scalars().all()]
