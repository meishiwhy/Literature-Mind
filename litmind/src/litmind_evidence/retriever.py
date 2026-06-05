"""ClaimRetriever — 从 Knowledge Base 检索相关 claims 和论文"""

from __future__ import annotations

from typing import Any

from litmind_knowledge.service import KnowledgeBase

from .config import LIKE_TOP_K, SEMANTIC_TOP_K


class ClaimRetriever:
    """证据检索器

    通过多路搜索策略从 Knowledge Base 检索相关 claims:
    1. search_claims — LIKE 搜索 claim.statement
    2. search_variables — LIKE 搜索变量名
    3. semantic_search — 向量语义搜索
    """

    def __init__(self, kb: KnowledgeBase):
        self._kb = kb

    def retrieve_claims(
        self,
        query: str,
        top_k: int = SEMANTIC_TOP_K,
    ) -> list[dict[str, Any]]:
        """检索与 query 相关的所有 claims

        Returns:
            [{paperId, statement, direction, evidenceSource, title, year, doi, similarity}, ...]
        """
        seen_paper_ids: set[str] = set()
        results: list[dict[str, Any]] = []

        # 1. 从 claim 表搜索
        for row in self._kb.search_claims(query):
            paper_id = row.get("paperId", "")
            if paper_id and paper_id not in seen_paper_ids:
                seen_paper_ids.add(paper_id)
                enriched = self._enrich(paper_id, row.get("statement", ""), "claim_search")
                if enriched:
                    results.append(enriched)

        # 2. 从变量表搜索
        for row in self._kb.search_variables(query):
            paper_id = row.get("paperId", "")
            if paper_id and paper_id not in seen_paper_ids:
                seen_paper_ids.add(paper_id)
                enriched = self._enrich(paper_id, "", "variable_search")
                if enriched:
                    results.append(enriched)

        # 3. 语义搜索
        for hit in self._kb.semantic_search(query, top_k=top_k):
            paper_id = hit.get("paperId", "")
            if paper_id and paper_id not in seen_paper_ids:
                seen_paper_ids.add(paper_id)
                results.append({
                    "paperId": paper_id,
                    "statement": hit.get("text", ""),
                    "direction": "",
                    "evidenceSource": hit.get("source", ""),
                    "title": hit.get("title", ""),
                    "year": hit.get("year"),
                    "doi": hit.get("doi", ""),
                    "similarity": hit.get("score", 0.0),
                })

        return results[:top_k]

    def retrieve_by_paper_ids(
        self, paper_ids: list[str]
    ) -> list[dict[str, Any]]:
        """根据 paperId 列表获取 claims"""
        results = []
        seen = set()
        for pid in paper_ids:
            if pid in seen:
                continue
            seen.add(pid)
            paper = self._kb.get_paper(pid)
            if paper and "claims" in paper:
                for c in paper["claims"]:
                    results.append({
                        "paperId": pid,
                        "statement": c.get("statement", ""),
                        "direction": c.get("direction", ""),
                        "evidenceSource": c.get("evidenceSource", ""),
                        "title": paper.get("title", ""),
                        "year": paper.get("year"),
                        "doi": paper.get("doi", ""),
                        "similarity": 1.0,
                    })
        return results

    def _enrich(
        self, paper_id: str, statement: str, source: str
    ) -> dict[str, Any] | None:
        """补充论文元数据"""
        paper = self._kb.get_paper(paper_id)
        if not paper:
            return None

        # 如果没有 statement，尝试从 paper claims 取第一条
        if not statement and paper.get("claims"):
            statement = paper["claims"][0].get("statement", "")

        return {
            "paperId": paper_id,
            "statement": statement,
            "direction": "",
            "evidenceSource": source,
            "title": paper.get("title", ""),
            "year": paper.get("year"),
            "doi": paper.get("doi", ""),
            "similarity": 0.0,
        }
