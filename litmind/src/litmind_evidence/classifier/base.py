"""ClaimClassifier 抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import ClassificationResult


class ClaimClassifier(ABC):
    """将 claim 分类为 support / oppose / neutral"""

    @abstractmethod
    def classify_batch(
        self,
        query: str,
        claims: list[dict[str, Any]],
    ) -> list[ClassificationResult]:
        """批量分类 claims

        Args:
            query: 用户研究观点
            claims: [{paperId, statement, ...}, ...]

        Returns:
            与 claims 一一对应的分类结果
        """
        ...
