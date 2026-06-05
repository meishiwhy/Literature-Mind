"""LLM-based Claim 分类器

复用 litmind_analyzer 的 LLMProvider 进行语义理解分类。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..config import CLASSIFIER_BATCH_SIZE
from ..models import ClassificationResult
from ..prompts import CLASSIFY_SYSTEM_PROMPT, build_classify_prompt
from .base import ClaimClassifier

logger = logging.getLogger(__name__)


class LLMClaimClassifier(ClaimClassifier):
    """使用 LLM 判断 claim 方向"""

    def __init__(self, provider):
        self._provider = provider

    def classify_batch(
        self,
        query: str,
        claims: list[dict[str, Any]],
    ) -> list[ClassificationResult]:
        if not claims:
            return []

        results: list[ClassificationResult] = []

        # 分批次处理
        for i in range(0, len(claims), CLASSIFIER_BATCH_SIZE):
            batch = claims[i : i + CLASSIFIER_BATCH_SIZE]
            batch_results = self._classify_one_batch(query, batch)
            results.extend(batch_results)

        return results

    def _classify_one_batch(
        self, query: str, batch: list[dict[str, Any]]
    ) -> list[ClassificationResult]:
        try:
            prompt = build_classify_prompt(query, batch)
            raw = self._provider.analyze(CLASSIFY_SYSTEM_PROMPT, prompt)

            if isinstance(raw, dict) and "classifications" in raw:
                classifications = raw["classifications"]
            elif isinstance(raw, str):
                data = json.loads(raw)
                classifications = data.get("classifications", [])
            else:
                logger.warning(f"Unexpected LLM output format: {type(raw)}")
                return self._neutral_fallback(batch)

            return self._parse_classifications(classifications, batch)

        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return self._neutral_fallback(batch)

    def _parse_classifications(
        self, classifications: list[dict], batch: list[dict[str, Any]]
    ) -> list[ClassificationResult]:
        """解析 LLM 输出，与输入 batch 对齐"""
        result_map = {}
        for c in classifications:
            pid = c.get("paperId", "")
            result_map[pid] = ClassificationResult(
                paperId=pid,
                claim=c.get("claim", ""),
                direction=c.get("direction", "neutral"),
                confidence=c.get("confidence", 0.5),
            )

        results = []
        for item in batch:
            pid = item.get("paperId", "")
            if pid in result_map:
                results.append(result_map[pid])
            else:
                results.append(ClassificationResult(
                    paperId=pid,
                    claim=item.get("statement", ""),
                    direction="neutral",
                    confidence=0.0,
                ))
        return results

    def _neutral_fallback(
        self, batch: list[dict[str, Any]]
    ) -> list[ClassificationResult]:
        return [
            ClassificationResult(
                paperId=item.get("paperId", ""),
                claim=item.get("statement", ""),
                direction="neutral",
                confidence=0.0,
            )
            for item in batch
        ]
