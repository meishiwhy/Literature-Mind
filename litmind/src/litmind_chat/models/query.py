from enum import Enum
from pydantic import BaseModel


class QueryType(str, Enum):
    PAPER_SEARCH = "paper_search"
    VARIABLE_SEARCH = "variable_search"
    STATISTIC_SEARCH = "statistic_search"
    CLAIM_SEARCH = "claim_search"
    EVIDENCE_SEARCH = "evidence_search"
    TREND_SEARCH = "trend_search"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


class ChatQuery(BaseModel):
    question: str
    top_k: int = 10
    stream: bool = False
