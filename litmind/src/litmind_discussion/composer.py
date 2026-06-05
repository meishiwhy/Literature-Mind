"""DiscussionComposer — 逐步生成 7 个 Discussion Section"""

from __future__ import annotations
from .config import COMPOSER_MODEL
from .models import CollectedEvidence, DiscussionInput
from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS, build_evidence_reference


SECTIONS = [
    "main_finding", "supporting", "contradictory",
    "mechanisms", "implications", "limitations", "future",
]

SECTION_TITLES = {
    "main_finding": "Main Finding Interpretation",
    "supporting": "Supporting Evidence",
    "contradictory": "Contradictory Evidence",
    "mechanisms": "Potential Mechanisms",
    "implications": "Practical Implications",
    "limitations": "Study Limitations",
    "future": "Future Directions",
}


class DiscussionComposer:
    def __init__(self, llm_provider, model: str = COMPOSER_MODEL):
        self._llm = llm_provider
        self._model = model

    def generate_outline(self, inp: DiscussionInput) -> dict[str, str]:
        outline = {}
        for section_key in SECTIONS:
            outline[section_key] = SECTION_TITLES.get(section_key, section_key)
        return outline

    def compose(self, inp: DiscussionInput, evidence: CollectedEvidence) -> str:
        all_items = evidence.all_items
        supporting = evidence.supporting
        opposing = evidence.opposing

        previous_text = ""
        full_draft = ""

        for section_key in SECTIONS:
            template = SECTION_PROMPTS.get(section_key, "")
            prompt = self._build_prompt(template, inp, previous_text, supporting, opposing, all_items)
            ref_list = build_evidence_reference(all_items)
            full_prompt = f"{prompt}\n\n{ref_list}"

            try:
                result = self._llm.analyze(SYSTEM_PROMPT, full_prompt)
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
                    section_heading = f"### {SECTION_TITLES.get(section_key, section_key)}\n\n"
                    full_draft += section_heading + section_text.strip() + "\n\n"
                    previous_text = section_text
            except Exception:
                previous_text = ""

        return full_draft.strip()

    def _build_prompt(self, template: str, inp: DiscussionInput, previous: str,
                      supporting: list, opposing: list, all_items: list) -> str:
        supporting_text = "\n".join(
            f"[{i.paperId}] {i.title or ''} - {i.claim[:80] if i.claim else ''}"
            for i in supporting[:5]
        ) or "No supporting evidence found."

        opposing_text = "\n".join(
            f"[{i.paperId}] {i.title or ''} - {i.claim[:80] if i.claim else ''}"
            for i in opposing[:5]
        ) or "No opposing evidence found."

        all_text = "\n".join(
            f"[{i.paperId}] {i.title or ''} ({i.direction})"
            for i in all_items[:8]
        ) or "No evidence found."

        return template.format(
            study_topic=inp.studyTopic,
            results="; ".join(inp.results),
            supporting_evidence=supporting_text,
            opposing_evidence=opposing_text,
            all_evidence=all_text,
            previous_section=previous[:500] if previous else "N/A (first section)",
            future_directions=all_text,
        )
