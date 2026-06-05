"""LitMind Evidence Finder — 科研证据检索与归纳系统"""

from .models import EvidenceItem, EvidenceResult
from .service import EvidenceFinderService

__all__ = ["EvidenceItem", "EvidenceResult", "EvidenceFinderService"]
__version__ = "0.1.0"
