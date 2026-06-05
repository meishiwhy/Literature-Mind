"""BaseRepository 抽象基类"""

import re
from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r"([A-Z])", r"_\1", name)
    return s1.lower().lstrip("_")


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class BaseRepository(ABC):
    def __init__(self, session: Session):
        self.session = session

    @property
    @abstractmethod
    def model_class(self):
        ...

    @property
    @abstractmethod
    def record_class(self):
        ...

    def _to_orm(self, record) -> Any:
        data = {}
        for k, v in record.model_dump().items():
            data[_camel_to_snake(k)] = v
        return self.model_class(**data)

    def _to_record(self, orm_obj) -> Any:
        data = {}
        for k, v in orm_obj.__dict__.items():
            if not k.startswith("_"):
                data[_snake_to_camel(k)] = v
        return self.record_class(**data)

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
