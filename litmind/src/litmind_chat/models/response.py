from pydantic import BaseModel
from typing import Optional


class SupportingPaper(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    authors: str = ""
    journal: str = ""
    doi: str = ""


class SupportingClaim(BaseModel):
    statement: str
    evidenceSource: str = ""
    paperId: str = ""


class ChatResponse(BaseModel):
    answer: str
    supportingPapers: list[SupportingPaper] = []
    supportingClaims: list[SupportingClaim] = []
    confidence: float = 0.0
    queryType: str = ""


class SearchResult(BaseModel):
    query: str = ""
    queryType: str = ""
    papers: list[SupportingPaper] = []
    claims: list[SupportingClaim] = []
