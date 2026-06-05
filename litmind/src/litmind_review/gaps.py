"""GapAnalyzer — 研究空白识别"""
from __future__ import annotations
from .models import ResearchGap, ReviewTheme


class GapAnalyzer:
    def analyze(
        self,
        themes: list[ReviewTheme],
        consensuses: list,
        trend_data: dict,
    ) -> list[ResearchGap]:
        gaps = []

        for theme in themes:
            if theme.paperCount <= 2:
                gaps.append(ResearchGap(
                    description=f"Limited research on {theme.name}",
                    evidence=f"Only {theme.paperCount} paper(s) found in current knowledge base",
                ))

        year_dist = trend_data.get("year_distribution", {})
        if year_dist:
            recent_years = {k: v for k, v in year_dist.items() if k >= 2023}
            if not recent_years and len(year_dist) > 0:
                gaps.append(ResearchGap(
                    description="Limited recent publications in this field",
                    evidence="No papers from 2023 or later found in current knowledge base",
                ))

        return gaps
