"""LitMind Discussion Generator — 基于证据的 Discussion 生成系统"""

from .models import DiscussionInput, DiscussionResult, DiscussionCitation, ParsedResult
from .service import DiscussionGeneratorService
from . import parser, prompts

__all__ = [
    "DiscussionInput", "DiscussionResult", "DiscussionCitation",
    "DiscussionGeneratorService", "ParsedResult",
    "parser", "prompts",
]
__version__ = "0.1.0"
