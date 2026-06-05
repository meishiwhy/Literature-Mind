"""ThemeDiscoveryEngine — 主题发现与聚类"""
from __future__ import annotations
import json
from typing import Any, Optional

from .models import ReviewTheme
from .prompts import THEME_DISCOVERY_PROMPT


class ThemeDiscoveryEngine:
    """Discover research themes by clustering papers via LLM analysis.

    Parameters
    ----------
    llm_provider : optional
        An object with an ``analyze(system_prompt, user_prompt)`` method
        that returns a dict (or JSON string) with a ``"themes"`` key.
        When ``None`` the engine returns an empty list (graceful fallback).
    """

    def __init__(self, llm_provider: Optional[Any] = None) -> None:
        self._llm = llm_provider

    def discover(self, papers: list[dict[str, Any]]) -> list[ReviewTheme]:
        """Cluster *papers* into themed groups.

        Returns an empty list when *papers* is empty or no LLM provider is
        available, or when the LLM response cannot be parsed.
        """
        if not papers or not self._llm:
            return []

        papers_text = "\n".join(
            f"{i}. {p.get('title', 'Untitled')}"
            f" | Keywords: {', '.join(p.get('keywords', []) or [])}"
            f" | Variables: {', '.join(p.get('variables', []) or [])}"
            for i, p in enumerate(papers)
        )

        try:
            result = self._llm.analyze(
                "Output JSON only.",
                THEME_DISCOVERY_PROMPT.format(papers=papers_text),
            )
            data = result if isinstance(result, dict) else json.loads(str(result))
            themes_data = data.get("themes", [])
        except Exception:
            return []

        themes: list[ReviewTheme] = []
        for td in themes_data:
            indices = td.get("paper_indices", [])
            theme = ReviewTheme(
                name=td.get("name", "Untitled Theme"),
                paperCount=len(indices),
                paperIds=[
                    str(papers[i].get("paperId", f"idx_{i}"))
                    for i in indices
                    if i < len(papers)
                ],
                description=td.get("description", ""),
            )
            themes.append(theme)

        return themes
