"""QueryClassifier — 问题分类器（规则优先，LLM 可选）"""

import re
from typing import Optional
from ..models.query import QueryType


_RULE_PATTERNS = [
    (QueryType.VARIABLE_SEARCH, [
        r"(变量|指标|parameter|variable|measure)\s+(研究|关注|使用|used|measured|analyzed)",
        r"what\s+(variables|parameters|measures).*?(studied|measured|used)",
    ]),
    (QueryType.STATISTIC_SEARCH, [
        r"哪些\s*(文献|研究).*?(使用了|采用|应用|used|applied|employed)\s+[\w\d]+",
        r"(统计|statistical|analysis)\s+(方法|method|technique).*?(使用|used|applied)",
        r"(ANOVA|SPM|t.test|regression|MANOVA|mixed.model|repeated.measure)",
    ]),
    (QueryType.PAPER_SEARCH, [
        r"哪些\s*(文献|论文|研究|文章).*?(研究|关注|探讨|讨论|分析|使用|采用|涉及)",
        r"what\s*(papers|studies|research|articles).*?(on|about|investigat|examin|stud|analyz)",
        r"find\s+(papers|studies|research).*?(on|about|for)",
    ]),
    (QueryType.CLAIM_SEARCH, [
        r"有哪些\s*(研究|证据|文献).*?(支持|反对|认为|表明|提出|suggest|show|indicate|demonstrat)",
        r"(支持|反对|support|evidence|against).*?(claim|hypothesis|statement|view)",
        r"evidence\s+(for|against|supporting|opposing)",
    ]),
    (QueryType.EVIDENCE_SEARCH, [
        r"(what|is|are|does|do|can|how)\s+.*?\?",
        r"(evidence|effect|impact|relationship|association|correlation|difference)\s+(of|between|on)",
        r"(does|can|will|may|could)\s+\w+\s+(increase|decrease|affect|change|alter|improve|reduce)",
    ]),
    (QueryType.TREND_SEARCH, [
        r"(研究|热点|趋势|前沿|current|recent|hotspot|trend|frontier|state.of.art)",
        r"what.*?(hot|trending|popular|emerging|new|recent)\s+(in|research|studies)",
    ]),
]


class QueryClassifier:
    """问题分类器 — 规则匹配 + LLM 兜底"""

    def __init__(self, provider=None, model: str = ""):
        self.provider = provider
        self.model = model

    def classify(self, question: str) -> str:
        for qtype, patterns in _RULE_PATTERNS:
            for pat in patterns:
                if re.search(pat, question, re.IGNORECASE):
                    if qtype == QueryType.EVIDENCE_SEARCH:
                        if re.search(r"(what|is|are|does|do|can|how|whether|which)", question, re.IGNORECASE):
                            return qtype.value
                        continue
                    return qtype.value

        if self.provider:
            try:
                result = self.provider.analyze(
                    "You are a query classifier. Output ONLY the type name.",
                    f"Classify this research question into one of: paper_search, variable_search, statistic_search, claim_search, evidence_search, trend_search, general_question.\nQuestion: {question}\nOutput only the type name.",
                )
                text = result if isinstance(result, str) else (result.get("answer", "") if isinstance(result, dict) else "")
                if text.strip() in {t.value for t in QueryType}:
                    return text.strip()
            except Exception:
                pass

        return QueryType.GENERAL_QUESTION.value
