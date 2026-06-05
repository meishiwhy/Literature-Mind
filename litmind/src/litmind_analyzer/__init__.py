"""LitMind Paper Analyzer — 论文知识提取模块"""
from .analyzer import analyze_paper
from .models import Claim, PaperAnalysis, ParticipantInfo
from .provider import LLMProvider

__all__ = ["Claim", "LLMProvider", "PaperAnalysis", "ParticipantInfo", "analyze_paper"]
__version__ = "0.1.0"
