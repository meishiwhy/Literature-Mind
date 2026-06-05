"""ReviewComposer — LLM 逐 Section 生成综述全文"""
from __future__ import annotations
from typing import Any

from .config import COMPOSER_MODEL
from .models import ReviewInput, ReviewTheme, ResearchConsensus, ResearchControversy, ResearchGap
from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS


SECTIONS = [
    "introduction", "landscape", "themes",
    "consensus", "controversies", "gaps",
    "future", "conclusion",
]


class ReviewComposer:
    def __init__(self, llm_provider, model: str = COMPOSER_MODEL):
        self._llm = llm_provider
        self._model = model

    def compose(
        self,
        inp: ReviewInput,
        themes: list[ReviewTheme],
        consensus: list[ResearchConsensus],
        controversies: list[ResearchControversy],
        gaps: list[ResearchGap],
        trend_data: dict,
        outline: dict[str, list[str]],
    ) -> str:
        previous_text = ""
        full_draft = ""

        themes_text = "\n".join(f"- {t.name}: {t.description}" for t in themes[:5]) or "No themes identified."
        themes_detail = "\n\n".join(f"Theme: {t.name}\nPapers: {t.paperCount}\n{t.description}" for t in themes[:5]) or "No themes."
        consensus_text = "\n".join(f"- {c.statement} ({c.supportingPapers} papers)" for c in consensus[:5]) or "No consensus items."
        controversy_text = "\n".join(f"- {c.statement} (support={c.support}, oppose={c.oppose})" for c in controversies[:5]) or "No controversies."
        gaps_text = "\n".join(f"- {g.description}: {g.evidence}" for g in gaps[:5]) or "No gaps identified."

        trend_items = []
        for var, count in trend_data.get("top_variables", [])[:5]:
            trend_items.append(f"  - {var}: {count} papers")
        trend_text = "\n".join(trend_items) or "No trend data."

        for section_key in SECTIONS:
            template = SECTION_PROMPTS.get(section_key, "")
            if not template:
                continue
            prompt = template.format(
                topic=inp.topic,
                paper_count=inp.max_papers,
                themes_text=themes_text,
                themes_detail=themes_detail,
                trend_text=trend_text,
                paper_refs=themes_detail,
                consensus_text=consensus_text,
                controversy_text=controversy_text,
                gaps_text=gaps_text,
                previous_text=previous_text[:800] if previous_text else "No previous sections yet.",
            )

            try:
                result = self._llm.analyze(SYSTEM_PROMPT, prompt)
                section_text = ""
                if isinstance(result, dict):
                    for key in ("draft", "text", "content", "output"):
                        if key in result and isinstance(result[key], str):
                            section_text = result[key]
                            break
                elif isinstance(result, str):
                    section_text = result
                else:
                    section_text = str(result) if result else ""

                if section_text:
                    full_draft += f"## {section_key.capitalize()}\n\n{section_text.strip()}\n\n"
                    previous_text = section_text
            except Exception:
                previous_text = ""

        return full_draft.strip()
