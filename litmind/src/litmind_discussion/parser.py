"""ResultParser — 解析用户研究结果，提取变量和方向"""
from __future__ import annotations
import re
from .models import ParsedResult

DIRECTION_PATTERNS = {
    "increase": re.compile(r"(increased?|greater|higher|larger|elevated|enhanced|improved)", re.I),
    "decrease": re.compile(r"(decreased?|lower|smaller|reduced|diminished|suppressed)", re.I),
    "no_difference": re.compile(r"(no significant|no difference|not different|similar|comparable|did not differ)", re.I),
}

STOP_WORDS = {"the", "a", "an", "in", "of", "to", "and", "that", "was", "were", "with", "for", "on", "by", "at", "from"}

class ResultParser:
    def parse(self, results: list[str]) -> list[ParsedResult]:
        if not results:
            return []
        return [self._parse_single(r) for r in results]

    def _parse_single(self, text: str) -> ParsedResult:
        direction = self._detect_direction(text)
        variables = self._extract_variables(text)
        return ParsedResult(original=text, variables=variables, direction=direction)

    def _detect_direction(self, text: str) -> str:
        for direction, pattern in DIRECTION_PATTERNS.items():
            if pattern.search(text):
                return direction
        return ""

    def _extract_variables(self, text: str) -> list[str]:
        words = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", text)
        return [w for w in words if w.lower() not in STOP_WORDS and len(w) > 2][:5]
