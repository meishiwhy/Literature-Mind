"""PaperAnalysis Pydantic 模型 — 结构化论文知识"""
from typing import Optional

from pydantic import BaseModel, Field


class Claim(BaseModel):
    statement: str = ""
    evidenceSource: str = ""


class ParticipantInfo(BaseModel):
    sampleSize: Optional[int] = None
    groups: list[str] = []
    population: str = ""


class NumericalFinding(BaseModel):
    """深度提取：数值型发现（含条件、指标、数值、单位、统计量）"""
    condition: str = ""          # 实验条件，如 "Flatfoot + CS shoe"
    metric: str = ""             # 指标，如 "Ankle eversion ROM"
    value: Optional[float] = None  # 数值
    unit: str = ""               # 单位，如 "deg", "N·m", "BW"
    statistics: str = ""         # 统计量，如 "p=0.003, η²=0.42"
    context: str = ""            # 简短上下文


class DeepExtraction(BaseModel):
    """深度提取：从论文 Results / Methods 中提取的细粒度结构化数据
    此字段为 optional，LLM 在无法提取时可留空。
    """
    numericalFindings: list[NumericalFinding] = Field(
        default_factory=list,
        description="数值型发现列表，每条包含条件、指标、数值、单位、统计量",
    )
    experimentalProtocols: list[str] = Field(
        default_factory=list,
        description="实验方案/参数，如 'Drop height: 45cm', 'Sampling: 1000Hz'",
    )


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
    deepExtraction: Optional[DeepExtraction] = Field(
        default=None,
        description="深度提取（可选）：数值数据、实验参数等细粒度信息",
    )
