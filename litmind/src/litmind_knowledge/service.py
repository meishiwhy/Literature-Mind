"""KnowledgeBase 服务 — 统一公开接口"""

import logging
from pathlib import Path
from typing import Any, Optional

from .config import get_default_db_path, get_default_chroma_path
from .database.engine import init_db, get_session
from .models.records import (
    PaperRecord, VariableRecord, StatisticRecord,
    ClaimRecord, KeywordRecord, LimitationRecord, FutureDirectionRecord,
)
from .repositories.paper_repo import PaperRepository
from .repositories.variable_repo import VariableRepository
from .repositories.statistic_repo import StatisticRepository
from .repositories.claim_repo import ClaimRepository
from .repositories.keyword_repo import KeywordRepository
from .repositories.limitation_repo import LimitationRepository
from .repositories.future_direction_repo import FutureDirectionRepository
from .repositories.knowledge_repo import KnowledgeRepository
from .vectorstore.indexer import VectorIndexer

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """科研知识库 — 统一服务入口"""

    def __init__(
        self,
        db_path: str = "",
        chroma_path: str = "",
    ):
        self.db_path = db_path or str(get_default_db_path())
        self.chroma_path = chroma_path or str(get_default_chroma_path())

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

        init_db(self.db_path)
        self._session = get_session()
        self._indexer = VectorIndexer(persist_dir=self.chroma_path)

    def _paper_repo(self): return PaperRepository(self._session)
    def _variable_repo(self): return VariableRepository(self._session)
    def _statistic_repo(self): return StatisticRepository(self._session)
    def _claim_repo(self): return ClaimRepository(self._session)
    def _keyword_repo(self): return KeywordRepository(self._session)
    def _limitation_repo(self): return LimitationRepository(self._session)
    def _future_repo(self): return FutureDirectionRepository(self._session)
    def _knowledge_repo(self): return KnowledgeRepository(self._session)

    def _parse_analysis(self, analysis: dict) -> dict:
        """将 PaperAnalysis dict 转为各 Repository 需要的记录"""
        pid = analysis.get("paperId", "") or analysis.get("paper_id", "")
        participants = analysis.get("participants", {}) or {}

        import json
        paper = PaperRecord(
            paperId=pid,
            title=analysis.get("title", ""),
            year=analysis.get("year"),
            journal=analysis.get("journal", ""),
            doi=analysis.get("doi", ""),
            researchQuestion=analysis.get("researchQuestion", ""),
            researchDomain=analysis.get("researchDomain", ""),
            studyDesign=analysis.get("studyDesign", ""),
            sampleSize=participants.get("sampleSize") if isinstance(participants, dict) else None,
            population=participants.get("population", "") if isinstance(participants, dict) else "",
            rawAnalysis=json.dumps(analysis, ensure_ascii=False),
        )

        variables = [VariableRecord(paperId=pid, variable=v) for v in analysis.get("variables", [])]
        statistics = [StatisticRecord(paperId=pid, method=m) for m in analysis.get("statistics", [])]
        claims = [
            ClaimRecord(paperId=pid, statement=c.get("statement", ""),
                       direction=c.get("direction", ""),
                       evidenceSource=c.get("evidenceSource", ""))
            for c in analysis.get("claims", [])
        ]
        keywords = [KeywordRecord(paperId=pid, keyword=k) for k in analysis.get("keywords", [])]
        limitations = [LimitationRecord(paperId=pid, limitation=l) for l in analysis.get("limitations", [])]
        future = [
            FutureDirectionRecord(paperId=pid, futureDirection=f)
            for f in analysis.get("futureDirections", [])
        ]

        return {
            "paper": paper, "variables": variables, "statistics": statistics,
            "claims": claims, "keywords": keywords, "limitations": limitations,
            "futureDirections": future,
        }

    # ── 公开接口 ──

    def add_paper(self, analysis: dict) -> str:
        """新增文献"""
        parsed = self._parse_analysis(analysis)
        pid = parsed["paper"].paperId

        self._paper_repo().save(parsed["paper"])
        self._variable_repo().save_batch(parsed["variables"])
        self._statistic_repo().save_batch(parsed["statistics"])
        self._claim_repo().save_batch(parsed["claims"])
        self._keyword_repo().save_batch(parsed["keywords"])
        self._limitation_repo().save_batch(parsed["limitations"])
        self._future_repo().save_batch(parsed["futureDirections"])
        self._session.commit()

        # 批量索引：一篇论文的全部字段一次写入 ChromaDB
        self._indexer.index_paper_batch(pid, analysis)

        return pid

    def update_paper(self, analysis: dict) -> bool:
        """更新文献"""
        pid = analysis.get("paperId", "") or analysis.get("paper_id", "")
        if not pid:
            return False

        self._variable_repo().delete_by_paper_id(pid)
        self._statistic_repo().delete_by_paper_id(pid)
        self._claim_repo().delete_by_paper_id(pid)
        self._keyword_repo().delete_by_paper_id(pid)
        self._limitation_repo().delete_by_paper_id(pid)
        self._future_repo().delete_by_paper_id(pid)
        self._indexer.delete_paper(pid)

        self.add_paper(analysis)
        return True

    def delete_paper(self, paper_id: str) -> bool:
        """删除文献"""
        self._paper_repo().delete(paper_id)
        self._session.commit()
        self._indexer.delete_paper(paper_id)
        return True

    def get_paper(self, paper_id: str) -> Optional[dict]:
        """获取单篇文献（含所有关联数据）"""
        return self._knowledge_repo().get_paper_with_all(paper_id)

    def search_papers(self, query: str) -> list:
        """关键词检索文献"""
        return [r.model_dump() for r in self._paper_repo().search(query)]

    def search_variables(self, query: str) -> list:
        return [r.model_dump() for r in self._variable_repo().search(query)]

    def search_statistics(self, query: str) -> list:
        return [r.model_dump() for r in self._statistic_repo().search(query)]

    def search_claims(self, query: str) -> list:
        return [r.model_dump() for r in self._claim_repo().search(query)]

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """基于向量数据库语义搜索"""
        return self._indexer.semantic_search(query, top_k=top_k)

    def import_batch(self, analyses: list[dict]) -> int:
        """批量导入

        Args:
            analyses: PaperAnalysis dict 列表

        Returns:
            成功导入的文献数量（失败的在日志中记录 paperId 和原因）
        """
        count = 0
        for a in analyses:
            pid = a.get("paperId", "") or a.get("paper_id", "") or "unknown"
            try:
                self.add_paper(a)
                count += 1
            except Exception as e:
                logger.error("[%s] Batch import failed: %s", pid, e, exc_info=True)
                continue
        logger.info("Batch import: %d/%d succeeded", count, len(analyses))
        return count

    def rebuild_index(self) -> bool:
        """重建所有向量索引"""
        self._indexer.rebuild_index()
        papers = self._paper_repo().search("")
        total = len(papers)
        logger.info("Rebuilding index for %d papers...", total)
        for i, p in enumerate(papers, 1):
            full = self.get_paper(p.paperId)
            if full:
                self._indexer.index_paper_batch(p.paperId, full)
            if i % 10 == 0:
                logger.info("  Rebuilt %d/%d papers", i, total)
        logger.info("Index rebuild complete: %d papers", total)
        return True
