"""CitationManager — 引用追踪、去重、提取"""

from __future__ import annotations

import re

from .models import DiscussionCitation


class CitationManager:
    def __init__(self):
        self._citations: list[DiscussionCitation] = []
        self._seen: set[tuple[str, str]] = set()

    def add(self, citation: DiscussionCitation) -> None:
        key = (citation.paperId, citation.section)
        if key not in self._seen:
            self._seen.add(key)
            self._citations.append(citation)

    def add_batch(self, citations: list[DiscussionCitation]) -> None:
        for c in citations:
            self.add(c)

    def get_all(self) -> list[DiscussionCitation]:
        return list(self._citations)

    def get_by_section(self, section: str) -> list[DiscussionCitation]:
        return [c for c in self._citations if c.section == section]

    def extract_from_text(self, text: str) -> list[str]:
        pattern = re.compile(r"\[([A-Za-z0-9_]+)\]")
        matches = pattern.findall(text)
        seen = set()
        result = []
        for m in matches:
            if m and m not in seen:
                seen.add(m)
                result.append(m)
        return result

    def filter_known(self, text: str, known_ids: set[str]) -> str:
        return text

    def to_citation_list(self, known_ids: set[str]) -> list[DiscussionCitation]:
        return [c for c in self._citations if c.paperId in known_ids]
