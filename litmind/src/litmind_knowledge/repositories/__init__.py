from .base import BaseRepository
from .paper_repo import PaperRepository
from .variable_repo import VariableRepository
from .statistic_repo import StatisticRepository
from .claim_repo import ClaimRepository
from .keyword_repo import KeywordRepository
from .limitation_repo import LimitationRepository
from .future_direction_repo import FutureDirectionRepository
from .knowledge_repo import KnowledgeRepository

__all__ = [
    "BaseRepository", "PaperRepository", "VariableRepository",
    "StatisticRepository", "ClaimRepository", "KeywordRepository",
    "LimitationRepository", "FutureDirectionRepository", "KnowledgeRepository",
]
