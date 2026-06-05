"""TrendAnalyzer — 研究趋势分析：高频变量/方法/设计/年份"""
from __future__ import annotations
from collections import Counter
from typing import Any


class TrendAnalyzer:
    def analyze(self, papers: list[dict[str, Any]]) -> dict:
        variables = []
        statistics = []
        designs = []
        years = []

        for p in papers:
            variables.extend(p.get("variables") or [])
            statistics.extend(p.get("statistics") or [])
            sd = p.get("studyDesign", "")
            if sd:
                designs.append(sd)
            y = p.get("year")
            if y:
                years.append(y)

        return {
            "top_variables": Counter(variables).most_common(10),
            "top_statistics": Counter(statistics).most_common(10),
            "top_designs": Counter(designs).most_common(10),
            "year_distribution": dict(sorted(Counter(years).items())),
        }
