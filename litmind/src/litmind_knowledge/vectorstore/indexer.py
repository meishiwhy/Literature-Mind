"""VectorIndexer — 管理 ChromaDB 索引"""

import uuid
from typing import Any

from .client import get_chroma_client, SentenceTransformerEmbedding

COLLECTIONS = {
    "researchQuestion": "kb_research_questions",
    "mainFindings": "kb_main_findings",
    "claims": "kb_claims",
    "limitations": "kb_limitations",
    "futureDirections": "kb_future_directions",
}


class VectorIndexer:
    """向量索引管理器"""

    def __init__(self, persist_dir: str = "", model_name: str = "all-MiniLM-L6-v2"):
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
        """索引一篇论文的某个字段"""
        value = data.get(field, "")
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    self.index_text(paper_id, item.get("statement", ""), field, item)
                elif isinstance(item, str):
                    self.index_text(paper_id, item, field)
        elif isinstance(value, str):
            self.index_text(paper_id, value, field)

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
