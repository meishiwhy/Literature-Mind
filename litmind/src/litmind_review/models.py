from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from litmind_discussion.models import DiscussionCitation


class ReviewInput(BaseModel):
    topic: str
    max_papers: int = 50


class ReviewTheme(BaseModel):
    name: str
    paperCount: int = 0
    paperIds: list[str] = Field(default_factory=list)
    description: str = ""


class ResearchConsensus(BaseModel):
    statement: str
    supportingPapers: int = 0
    paperIds: list[str] = Field(default_factory=list)


class ResearchControversy(BaseModel):
    statement: str
    support: int = 0
    oppose: int = 0
    supportingPaperIds: list[str] = Field(default_factory=list)
    opposingPaperIds: list[str] = Field(default_factory=list)


class ResearchGap(BaseModel):
    description: str
    evidence: str = ""


class ReviewResult(BaseModel):
    topic: str
    paperCount: int = 0
    researchThemes: list[ReviewTheme] = Field(default_factory=list)
    researchConsensus: list[ResearchConsensus] = Field(default_factory=list)
    researchControversies: list[ResearchControversy] = Field(default_factory=list)
    researchGaps: list[ResearchGap] = Field(default_factory=list)
    reviewOutline: dict[str, list[str]] = Field(default_factory=dict)
    reviewDraft: str = ""
    citations: list[DiscussionCitation] = Field(default_factory=list)
