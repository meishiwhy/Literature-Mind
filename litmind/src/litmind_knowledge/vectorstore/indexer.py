"""VectorIndexer — 管理 ChromaDB 索引"""

import uuid
from collections import defaultdict
from typing import Any

from .client import get_chroma_client, SentenceTransformerEmbedding

COLLECTIONS = {
    "researchQuestion": "kb_research_questions",
    "mainFindings": "kb_main_findings",
    "claims": "kb_claims",
    "limitations": "kb_limitations",
    "futureDirections": "kb_future_directions",
    # 深度提取
    "numericalFindings": "kb_numerical_findings",
    "experimentalProtocols": "kb_experimental_protocols",
}


class VectorIndexer:
    """向量索引管理器"""

    def __init__(self, persist_dir: str = "", model_name: str = "BAAI/bge-small-zh-v1.5"):
        self.embedding = SentenceTransformerEmbedding(model_name)
        self.client = get_chroma_client(persist_dir or None)
        self._collections = {}

    def _get_collection(self, field: str):
        name = COLLECTIONS.get(field, "kb_other")
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name, embedding_function=self.embedding
            )
        return self._collections[name]

    def _all_collections(self) -> set[str]:
        return set(COLLECTIONS.values())

    # ── 单条索引（保持向后兼容） ──

    def index_text(self, paper_id: str, text: str, field: str, metadata: dict | None = None) -> None:
        """索引一条文本"""
        if not text.strip():
            return
        collection = self._get_collection(field)
        collection.add(
            documents=[text],
            metadatas=[{"paperId": paper_id, **(metadata or {})}],
            ids=[f"{paper_id}_{field}_{uuid.uuid4().hex[:8]}"],
        )

    def index_paper(self, paper_id: str, data: dict, field: str) -> None:
        """索引一篇论文的某个字段（单字段版本）"""
        value = data.get(field, "")
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if field == "numericalFindings":
                        text = self._fmt_numerical(item)
                        self.index_text(paper_id, text, field, item)
                    else:
                        self.index_text(paper_id, item.get("statement", ""), field, item)
                elif isinstance(item, str):
                    self.index_text(paper_id, item, field)
        elif isinstance(value, str):
            self.index_text(paper_id, value, field)
        elif isinstance(value, dict):
            for sub_field in ("numericalFindings", "experimentalProtocols"):
                if sub_field in value:
                    self.index_paper(paper_id, value, sub_field)

    # ── 批量索引（推荐使用） ──

    def index_paper_batch(self, paper_id: str, data: dict) -> None:
        """批量索引一篇论文的全部字段（每个 collection 只调一次 add）

        Args:
            paper_id: 论文 ID
            data: PaperAnalysis dict（含所有字段 + deepExtraction）
        """
        # 按 collection 分组收集
        batches: dict[str, dict] = defaultdict(lambda: {"documents": [], "metadatas": [], "ids": []})

        def _collect(text: str, field: str, metadata: dict | None = None):
            if not text.strip():
                return
            cname = COLLECTIONS.get(field, "kb_other")
            batches[cname]["documents"].append(text)
            batches[cname]["metadatas"].append({"paperId": paper_id, **(metadata or {})})
            batches[cname]["ids"].append(f"{paper_id}_{field}_{uuid.uuid4().hex[:8]}")

        # 收集标准字段
        for field in ("researchQuestion", "mainFindings", "claims", "limitations", "futureDirections"):
            value = data.get(field, "")
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        _collect(item.get("statement", ""), field, item)
                    elif isinstance(item, str):
                        _collect(item, field)
            elif isinstance(value, str):
                _collect(value, field)

        # 收集深度提取字段
        de = data.get("deepExtraction")
        if isinstance(de, dict):
            for item in de.get("numericalFindings", []):
                if isinstance(item, dict):
                    text = self._fmt_numerical(item)
                    _collect(text, "numericalFindings", item)
            for item in de.get("experimentalProtocols", []):
                if isinstance(item, str):
                    _collect(item, "experimentalProtocols")

        # 逐 collection 批量写入
        for cname, batch in batches.items():
            collection = self._get_collection_by_name(cname)
            if batch["documents"]:
                collection.add(
                    documents=batch["documents"],
                    metadatas=batch["metadatas"],
                    ids=batch["ids"],
                )

    def _get_collection_by_name(self, name: str):
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name, embedding_function=self.embedding
            )
        return self._collections[name]

    @staticmethod
    def _fmt_numerical(item: dict) -> str:
        """将 numericalFinding dict 组装为可搜索文本"""
        parts = []
        if item.get("condition"):
            parts.append(item["condition"])
        if item.get("metric"):
            parts.append(item["metric"])
        if item.get("value") is not None:
            val_str = f"{item['value']}"
            if item.get("unit"):
                val_str += f" {item['unit']}"
            parts.append(val_str)
        if item.get("statistics"):
            parts.append(f"({item['statistics']})")
        return " ".join(parts)

    def delete_paper(self, paper_id: str) -> None:
        """删除论文的所有向量索引"""
        for field in COLLECTIONS:
            collection = self._get_collection(field)
            all_items = collection.get(where={"paperId": paper_id})
            if all_items["ids"]:
                collection.delete(ids=all_items["ids"])

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """跨所有 collection 进行语义搜索"""
        results = []
        for field in COLLECTIONS:
            collection = self._get_collection(field)
            try:
                hits = collection.query(query_texts=[query], n_results=min(top_k, 50))
                for i in range(len(hits["ids"][0]) if hits["ids"] else 0):
                    results.append({
                        "paperId": hits["metadatas"][0][i]["paperId"],
                        "text": hits["documents"][0][i],
                        "source": field,
                        "score": 1.0 - hits["distances"][0][i] if hits.get("distances") else 0.0,
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def rebuild_index(self) -> None:
        """重建所有索引"""
        for name in COLLECTIONS.values():
            try:
                self.client.delete_collection(name)
            except Exception:
                pass
        self._collections = {}
