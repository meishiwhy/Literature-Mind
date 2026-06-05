"""LLM prompts for Discussion Generator — 7 section generation prompts"""

SYSTEM_PROMPT = """You are a scientific discussion writer. Your task is to write the Discussion section of a research paper based on the study's results and retrieved evidence from the literature.

Rules:
1. Every statement must be supported by evidence from the provided reference list.
2. Use [paperId] markers to cite sources within the text.
3. Clearly distinguish between: the study's own findings, literature evidence, and speculative interpretations.
4. Do NOT fabricate authors, DOIs, or citations. Only use references from the provided list.
5. Output plain text with [paperId] markers for citations."""

SECTION_PROMPTS: dict[str, str] = {
    "main_finding": """Write the Main Finding Interpretation section. Summarize the study's primary findings and explain what they mean in the context of the research question.

Study Topic: {study_topic}
Results: {results}
Supporting Evidence: {supporting_evidence}""",
    "supporting": """Write the Supporting Evidence section. Compare the study's findings with existing literature that supports or aligns with the results.

Previous section: {previous_section}
Supporting evidence details: {supporting_evidence}""",
    "contradictory": """Write the Contradictory Evidence section. Discuss any findings that differ from or contradict the current results, and suggest possible reasons for discrepancies.

Previous section: {previous_section}
Opposing evidence: {opposing_evidence}""",
    "mechanisms": """Write the Potential Mechanisms section. Explain the potential biomechanical, physiological, or mechanical mechanisms underlying the observed findings.

Previous section: {previous_section}
Relevant evidence: {all_evidence}""",
    "implications": """Write the Practical Implications section. Discuss the clinical, practical, or applied significance of the findings.

Previous section: {previous_section}
Evidence: {all_evidence}""",
    "limitations": """Write the Study Limitations section. Discuss methodological limitations, constraints, and potential sources of bias.

Previous section: {previous_section}
Study topic: {study_topic}""",
    "future": """Write the Future Directions section. Suggest specific research questions, methodological improvements, or new directions based on the current findings.

Previous section: {previous_section}
Future directions from literature: {future_directions}""",
}


def build_evidence_reference(evidence_items: list) -> str:
    lines = ["Reference papers available for citation:"]
    for item in evidence_items:
        year_str = f" ({item.year})" if item.year else ""
        lines.append(f"  [{item.paperId}] {item.title or 'Untitled'}{year_str}")
        if item.claim:
            lines.append(f"       Claim: {item.claim[:120]}")
    return "\n".join(lines)
