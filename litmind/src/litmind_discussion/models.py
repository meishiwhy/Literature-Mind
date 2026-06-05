"""Discussion Generator 数据模型"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from litmind_evidence.models import EvidenceItem, EvidenceResult


class DiscussionInput(BaseModel):
    studyTopic: str
    results: list[str]


class DiscussionCitation(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    authors: str = ""
    doi: str = ""
    claim: str = ""
    section: str = ""


class DiscussionResult(BaseModel):
    discussionOutline: dict[str, str] = Field(default_factory=dict)
    discussionDraft: str = ""
    supportingPapers: list[EvidenceItem] = Field(default_factory=list)
    opposingPapers: list[EvidenceItem] = Field(default_factory=list)
    citations: list[DiscussionCitation] = Field(default_factory=list)


class ParsedResult(BaseModel):
    original: str
    variables: list[str] = Field(default_factory=list)
    direction: str = ""


class CollectedEvidence(BaseModel):
    by_result: dict[int, EvidenceResult] = Field(default_factory=dict)
    supporting: list[EvidenceItem] = Field(default_factory=list)
    opposing: list[EvidenceItem] = Field(default_factory=list)
    all_items: list[EvidenceItem] = Field(default_factory=list)
