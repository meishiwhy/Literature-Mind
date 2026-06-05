"""LLM prompts for Review Generator"""

SYSTEM_PROMPT = """You are a scientific review writer. Your task is to write a literature review based on retrieved papers and analysis results.

Rules:
1. Every statement must be supported by evidence from the provided reference list.
2. Use [paperId] markers to cite sources within the text.
3. Do NOT fabricate authors, DOIs, or citations. Only use references from the provided list.
4. Output plain text with [paperId] markers for citations."""

THEME_DISCOVERY_PROMPT = """You are a research theme discovery engine. Given a list of papers, group them into 3-7 research themes.

Papers:
{papers}

For each theme, provide:
- name: short theme name
- description: one-sentence description
- paper_indices: list of paper numbers belonging to this theme

Output JSON format: {"themes": [{"name": "...", "description": "...", "paper_indices": [0,1,2]}]}"""

SECTION_PROMPTS = {
    "introduction": """Write the Introduction section. Set the research context, explain why this topic is important, and state the review's objectives.

Topic: {topic}
Paper count: {paper_count}
Themes: {themes_text}""",

    "landscape": """Write the Current Research Landscape section. Describe the volume of research, publication timeline, study designs, and statistical methods used in this field.

Topic: {topic}
Trend data: {trend_text}""",

    "themes": """Write the Major Research Themes section. For each theme, describe the key findings and representative studies.

Themes detail: {themes_detail}
Paper references: {paper_refs}""",

    "consensus": """Write the Evidence Consensus section. Discuss findings that are consistently supported across multiple studies.

Consensus items: {consensus_text}""",

    "controversies": """Write the Research Controversies section. Discuss topics where evidence is mixed or conflicting.

Controversy items: {controversy_text}""",

    "gaps": """Write the Research Gaps section. Identify understudied areas, methodological limitations in the literature, and unanswered questions.

Gap items: {gaps_text}""",

    "future": """Write the Future Directions section. Propose specific research questions and methodological improvements for future work.

Previous sections: {previous_text}""",

    "conclusion": """Write the Conclusion section. Summarize the main findings of this review.

Previous sections: {previous_text}""",
}
