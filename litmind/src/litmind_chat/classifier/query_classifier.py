"""QueryClassifier — 问题分类器（规则优先，LLM 可选）"""

import re
from typing import Optional
from ..models.query import QueryType


_RULE_PATTERNS = [
    (QueryType.VARIABLE_SEARCH, [
        # 中文 — 变量/指标
        r"(变量|指标|参数|因素|因子|自变量|因变量|控制变量)\s+(研究|关注|使用|包括|涉及|有哪些|是什么|如何选择)",
        r"(研究|考察|测量|分析|记录了)\s*(了?\s*)?哪些\s*(变量|指标|参数)",
        r"哪些\s*(变量|指标|参数)",
        r"what\s+(variables|parameters|measures).*?(studied|measured|used)",
        r"which\s+(variables|parameters)\s+(were|are|did)",
    ]),
    (QueryType.STATISTIC_SEARCH, [
        # 中文
        r"哪些\s*(文献|研究).*?(使用了|采用|应用|用了)\s+[\w一-鿿]+",
        r"(用了|使用|采用|应用)\s*(什么|哪些)\s*(统计|分析)\s*(方法|手段|技术)",
        r"(统计|统计分析)\s*(方法|手段|技术|工具|软件).*?(是什么|有哪些|用什么)",
        r"(ANOVA|SPM|t.?test|regression|MANOVA|mixed.?model|repeated.?measure|卡方|t检验|方差分析|回归分析|主成分|因子分析)",
        r"(显著性|p值|效应量|effect.size|cohen|置信区间|confidence.interval)",
    ]),
    (QueryType.PAPER_SEARCH, [
        # 中文
        r"哪些\s*(文献|论文|研究|文章|工作|课题组).*?(研究|关注|探讨|讨论|分析|使用|采用|涉及|发表|做了)",
        r"有[没有嘛]?\s*(什么|哪些)\s*(文献|论文|研究|文章).*?(关于|研究|探讨|分析)",
        r"推荐.*?(几篇|一些|哪些).*(文献|论文|文章|研究)",
        r"(求推|求推荐|有没有|谁能推荐).*?(文献|论文|文章|研究)",
        r"what\s*(papers|studies|research|articles).*?(on|about|investigat|examin|stud|analyz)",
        r"find\s+(papers|studies|research).*?(on|about|for)",
        r"(recommend|suggest|looking.for)\s+(papers|studies|articles)",
    ]),
    (QueryType.CLAIM_SEARCH, [
        # 中文
        r"有哪些\s*(研究|证据|文献).*?(支持|反对|认为|表明|提出|指出|发现|证实|证明)",
        r"有什么\s*(研究|证据|文献).*?(支持|反对|认为|表明|指出)",
        r"(支持|反对|支撑).*?(观点|假说|假设|理论|claim|hypothesis|statement)",
        r"(有没|是否).*?(证据|研究).*?(支持|反对)",
        r"有没有.*?证据.*?(表明|证明|说明|支持|反对)",
        r"(支持|反对|support|evidence|against).*?(claim|hypothesis|statement|view)",
        r"evidence\s+(for|against|supporting|opposing)",
    ]),
    (QueryType.EVIDENCE_SEARCH, [
        # 中文 — 因果关系/效应/关联
        r".+?(是否|会不会|能不能|有没有|可否).+?(影响|增加|减少|改变|促进|抑制|导致|引起|降低|提高)",
        r".+?与.+?(的)?\s*(关系|关联|相关性|影响|作用|机制)",
        r".+?\s*(对|对于)\s*.+?(的)?\s*(影响|作用|效果|贡献|机制)",
        r"(什么|哪些)\s*(因素|原因|机制).*?(影响|导致|引起|造成|决定)",
        r"(how|does|do|can|what|is|are|whether|why)\s+.*\?",
        r"(evidence|effect|impact|relationship|association|correlation|difference)\s+(of|between|on|in)",
        r"(does|can|will|may|could)\s+\w+\s+(increase|decrease|affect|change|alter|improve|reduce)",
        r"(mechanism|reason|cause|factor|role)\s+(of|for|behind|underlying)",
    ]),
    (QueryType.TREND_SEARCH, [
        # 中文
        r"(热点|趋势|前沿|动态|现状|进展|发展方向|未来方向)",
        r"最近|最新|近年来|近几年|当前|目前|眼下",
        r"(热门|新兴|主流|前沿).*?(方向|领域|话题|主题|方法)",
        r"目前.*?(研究|领域)\s*(热点|趋势|前沿|动态|现状)",
        r"what.*?(hot|trending|popular|emerging|new|recent)\s+(in|research|studies)",
        r"(current|recent|latest|state.?of.?art|cutting.?edge)\s+(research|trend|development)",
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
                        # 英文疑问词 → 明确证据问题
                        if re.search(r"(what|is|are|does|do|can|how|whether|which)", question, re.IGNORECASE):
                            return qtype.value
                        # 中文 evidence 模式匹配 → 也是证据问题
                        if re.search(r"(是否|会不会|能不能|有没有|可否|.+?与.+?关系|.+?对.+?影响)", question):
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
