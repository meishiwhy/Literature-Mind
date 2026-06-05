"""Paper Analyzer 主流程"""

from typing import Any

from .models import PaperAnalysis
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .provider import LLMProvider
from .validator import validate_and_repair


def analyze_paper(
    paper_content: dict[str, Any],
    provider: LLMProvider,
) -> PaperAnalysis:
    """分析论文全文，返回结构化 PaperAnalysis

    Args:
        paper_content: PaperContent dict (含 sections, paperKey)
        provider: 已配置的 LLM Provider 实例

    Returns:
        已验证的 PaperAnalysis 对象
    """
    paper_key = paper_content.get("paperKey", "") or paper_content.get("paperId", "")
    sections = paper_content.get("sections", {})

    if not sections:
        return PaperAnalysis(paperId=paper_key)

    try:
        user_prompt = build_user_prompt(sections)
        raw = provider.analyze(SYSTEM_PROMPT, user_prompt)
        analysis = validate_and_repair(raw)
        analysis.paperId = paper_key
        return analysis
    except Exception:
        return PaperAnalysis(paperId=paper_key)
