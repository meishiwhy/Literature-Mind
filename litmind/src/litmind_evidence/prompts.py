"""LLM 提示词模板 — Evidence Finder"""

CLASSIFY_SYSTEM_PROMPT = """You are a scientific evidence classifier. Your task is to determine whether a research claim from a paper SUPPORTS, OPPOSES, or is NEUTRAL relative to a given research query.

Rules:
1. Output ONLY valid JSON. No explanatory text.
2. Return: {"classifications": [{"paperId": "...", "direction": "support|oppose|neutral", "confidence": 0.0-1.0}]}
3. "support" = the claim directly supports or is consistent with the query
4. "oppose" = the claim directly contradicts or challenges the query
5. "neutral" = the claim is unrelated, describes methods only, has no clear direction, or is inconclusive
6. Be conservative - if uncertain, use "neutral"
7. confidence reflects how clearly the claim relates to the query"""


def build_classify_prompt(query: str, claims: list[dict]) -> str:
    """组装分类 prompt

    Args:
        query: 用户输入的研究观点
        claims: [{"paperId": "...", "claim": "..."}, ...]

    Returns:
        分类 prompt 字符串
    """
    parts = [
        f"Research Query: {query}",
        "",
        "Claims to classify (each claim is from a published paper):",
        "",
    ]
    for i, c in enumerate(claims, 1):
        parts.append(f"{i}. [paperId: {c.get('paperId', '')}] {c.get('claim', '')}")

    parts.extend([
        "",
        "For each claim, determine if it supports, opposes, or is neutral to the research query.",
        "Output JSON format: {\"classifications\": [{\"paperId\": \"...\", \"direction\": \"support|oppose|neutral\", \"confidence\": 0.0}]}",
    ])

    return "\n".join(parts)
