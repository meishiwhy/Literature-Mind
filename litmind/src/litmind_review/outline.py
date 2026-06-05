"""OutlineGenerator — 综述框架生成"""
from __future__ import annotations

SECTIONS = [
    "introduction", "landscape", "themes",
    "consensus", "controversies", "gaps",
    "future", "conclusion",
]

SECTION_LABELS = {
    "introduction": "Introduction",
    "landscape": "Current Research Landscape",
    "themes": "Major Research Themes",
    "consensus": "Evidence Consensus",
    "controversies": "Research Controversies",
    "gaps": "Research Gaps",
    "future": "Future Directions",
    "conclusion": "Conclusion",
}


class OutlineGenerator:
    def __init__(self, llm_provider=None):
        self._llm = llm_provider

    def generate(
        self,
        topic: str,
        theme_names: list[str],
        consensus_statements: list[str],
        controversy_statements: list[str],
        gap_descriptions: list[str],
    ) -> dict[str, list[str]]:
        outline = {}
        for section_key in SECTIONS:
            outline[section_key] = []
        return outline
