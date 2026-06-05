"""ChromaDB 客户端 + Embedding 函数"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb import EmbeddingFunction


class SentenceTransformerEmbedding(EmbeddingFunction):
    """sentence-transformers embedding 函数，适配 ChromaDB"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        self._load_model()
        embeddings = self._model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()

    @staticmethod
    def name() -> str:
        return "sentence_transformers_all-MiniLM-L6-v2"

    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "SentenceTransformerEmbedding":
        return SentenceTransformerEmbedding(
            model_name=config.get("model_name", "all-MiniLM-L6-v2")
        )

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> List[str]:
        return ["cosine", "l2", "ip"]


def get_chroma_client(persist_dir: Optional[str] = None):
    if persist_dir:
        return chromadb.PersistentClient(path=persist_dir)
    return chromadb.Client()
