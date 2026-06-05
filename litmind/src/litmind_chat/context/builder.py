"""ContextBuilder — 检索知识库 + 组装 LLM 上下文"""

from typing import Any, Optional
from ..models.query import QueryType


class ContextBuilder:
    """检索 Knowledge Base 并构建 LLM 提示上下文"""

    def __init__(self, kb=None):
        self.kb = kb

    def retrieve(self, question: str, query_type: str, top_k: int = 10) -> dict:
        result = {
            "papers": [],
            "claims": [],
            "semantic_results": [],
            "variables": [],
            "statistics": [],
        }

        if not self.kb:
            return result

        result["semantic_results"] = self.kb.semantic_search(question, top_k=top_k)

        if query_type == QueryType.PAPER_SEARCH.value:
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.VARIABLE_SEARCH.value:
            result["variables"] = self.kb.search_variables(question)
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.STATISTIC_SEARCH.value:
            result["statistics"] = self.kb.search_statistics(question)
        elif query_type in (QueryType.CLAIM_SEARCH.value, QueryType.EVIDENCE_SEARCH.value):
            result["claims"] = self.kb.search_claims(question)
            result["papers"] = self.kb.search_papers(question)
        elif query_type == QueryType.TREND_SEARCH.value:
            result["papers"] = self.kb.search_papers(question)

        return result

    def build_system_prompt(self) -> str:
        return (
            "You are a scientific research assistant. Answer questions based solely on "
            "the provided evidence. Every claim in your answer must cite specific papers.\n\n"
            "Rules:\n"
            "1. Only use information from the provided evidence.\n"
            "2. Every factual statement must cite a paper (author, year).\n"
            "3. If the evidence does not answer the question, say so.\n"
            "4. Do not fabricate citations or evidence.\n"
            "5. Output in Chinese or English matching the user's question language."
        )

    def _format_papers(self, papers: list) -> str:
        if not papers:
            return ""
        lines = []
        for p in papers:
            pid = p.get("paperId", "?")
            title = p.get("title", "Untitled")[:80]
            year = p.get("year", "?")
            lines.append(f"- {title} ({year}) [ID: {pid}]")
        return "\n".join(lines)

    def _format_claims(self, claims: list) -> str:
        if not claims:
            return ""
        lines = []
        for c in claims:
            stmt = c.get("statement", c.get("claim", ""))[:120]
            src = c.get("evidenceSource", "")
            lines.append(f'- "{stmt}" (from: {src})')
        return "\n".join(lines)

    def build_user_prompt(self, question: str, query_type: str, context: dict) -> str:
        parts = [f"## User Question\n{question}\n"]

        if context.get("papers"):
            parts.append("## Relevant Papers\n" + self._format_papers(context["papers"]))

        if context.get("claims"):
            parts.append("## Relevant Claims\n" + self._format_claims(context["claims"]))

        if context.get("semantic_results"):
            lines = []
            for r in context["semantic_results"][:5]:
                lines.append(f'- "{r.get("text", "")[:120]}" (paper: {r.get("paperId", "?")})')
            parts.append("## Semantic Search Results\n" + "\n".join(lines))

        return "\n\n".join(parts)

    def build_prompt(self, question: str, query_type: str, context: dict) -> tuple[str, str]:
        return self.build_system_prompt(), self.build_user_prompt(question, query_type, context)
