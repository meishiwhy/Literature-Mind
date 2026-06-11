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
        """过滤文本中的引用标记，移除不在 known_ids 中的虚构引用

        Args:
            text: 包含 [paperId] 引用的文本
            known_ids: 知识库中真实存在的 paperId 集合

        Returns:
            过滤后的文本（虚构引用标记被删除）
        """
        if not text:
            return text

        def _replace_match(m: re.Match) -> str:
            pid = m.group(1)
            if pid in known_ids:
                return m.group(0)  # 保留
            return ""  # 删除

        return re.sub(r"\[([A-Za-z0-9_]+)\]", _replace_match, text)

    def to_citation_list(self, known_ids: set[str]) -> list[DiscussionCitation]:
        return [c for c in self._citations if c.paperId in known_ids]
