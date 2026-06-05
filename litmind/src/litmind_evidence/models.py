"""Evidence Finder 数据模型"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class EvidenceItem(BaseModel):
    """单条证据"""
    paperId: str = ""
    title: str = ""
    year: Optional[int] = None
    doi: str = ""
    claim: str = ""
    similarity: float = 0.0
    direction: str = ""  # "support", "oppose", "neutral"


class EvidenceResult(BaseModel):
    """完整证据检索结果"""
    query: str = ""
    support: list[EvidenceItem] = Field(default_factory=list)
    oppose: list[EvidenceItem] = Field(default_factory=list)
    neutral: list[EvidenceItem] = Field(default_factory=list)
    evidenceStrength: str = ""
    confidence: float = 0.0
    totalPapers: int = 0
    supportingPapers: int = 0
    opposingPapers: int = 0


class ClassificationResult(BaseModel):
    """单条 claim 的分类结果"""
    paperId: str = ""
    claim: str = ""
    direction: str = ""  # "support", "oppose", "neutral"
    confidence: float = 0.0
