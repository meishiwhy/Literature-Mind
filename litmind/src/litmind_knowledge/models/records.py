from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaperRecord(BaseModel):
    paperId: str
    title: str = ""
    year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    researchQuestion: str = ""
    researchDomain: str = ""
    studyDesign: str = ""
    sampleSize: Optional[int] = None
    population: str = ""
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class VariableRecord(BaseModel):
    paperId: str
    variable: str


class StatisticRecord(BaseModel):
    paperId: str
    method: str


class ClaimRecord(BaseModel):
    paperId: str
    statement: str
    direction: str = ""
    evidenceSource: str = ""


class KeywordRecord(BaseModel):
    paperId: str
    keyword: str


class LimitationRecord(BaseModel):
    paperId: str
    limitation: str


class FutureDirectionRecord(BaseModel):
    paperId: str
    futureDirection: str
