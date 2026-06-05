"""PaperAnalysis Pydantic 模型 — 结构化论文知识"""
from pydantic import BaseModel, Field
from typing import Optional


class Claim(BaseModel):
    statement: str = ""
    evidenceSource: str = ""


class ParticipantInfo(BaseModel):
    sampleSize: Optional[int] = None
    groups: list[str] = []
    population: str = ""


class PaperAnalysis(BaseModel):
    paperId: str = ""
    researchQuestion: str = ""
    researchDomain: str = ""
    studyDesign: str = ""
    participants: ParticipantInfo = Field(default_factory=ParticipantInfo)
    methods: list[str] = []
    statistics: list[str] = []
    variables: list[str] = []
    outcomes: list[str] = []
    mainFindings: list[str] = []
    claims: list[Claim] = []
    limitations: list[str] = []
    futureDirections: list[str] = []
    keywords: list[str] = []
