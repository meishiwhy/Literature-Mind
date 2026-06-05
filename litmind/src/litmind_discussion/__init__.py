"""LitMind Discussion Generator — 基于证据的 Discussion 生成系统"""

from .models import DiscussionInput, DiscussionResult, DiscussionCitation
from .service import DiscussionGeneratorService

__all__ = ["DiscussionInput", "DiscussionResult", "DiscussionCitation", "DiscussionGeneratorService"]
__version__ = "0.1.0"
