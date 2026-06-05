"""AnswerGenerator — 调用 LLM 生成结构化答案"""

from typing import Optional
from ..models.response import ChatResponse, SupportingPaper, SupportingClaim


class AnswerGenerator:
    """使用 LLM 生成带引用的答案"""

    def __init__(self, provider=None, model: str = ""):
        self.provider = provider
        self.model = model

    def generate(
        self,
        question: str,
        system_prompt: str,
        user_prompt: str,
    ) -> ChatResponse:
        if not self.provider:
            return ChatResponse(
                answer="无法回答问题：未配置 LLM 提供者。请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY。",
                confidence=0.0,
            )

        try:
            raw = self.provider.analyze(system_prompt, user_prompt)

            papers = []
            for p in raw.get("supportingPapers", []):
                papers.append(SupportingPaper(
                    paperId=p.get("paperId", ""),
                    title=p.get("title", ""),
                    year=p.get("year"),
                    authors=p.get("authors", ""),
                    journal=p.get("journal", ""),
                    doi=p.get("doi", ""),
                ))

            claims = []
            for c in raw.get("supportingClaims", []):
                claims.append(SupportingClaim(
                    statement=c.get("statement", ""),
                    evidenceSource=c.get("evidenceSource", ""),
                    paperId=c.get("paperId", ""),
                ))

            return ChatResponse(
                answer=raw.get("answer", "无法生成答案。"),
                supportingPapers=papers,
                supportingClaims=claims,
                confidence=raw.get("confidence", 0.5),
            )

        except Exception as e:
            return ChatResponse(
                answer=f"无法回答问题：{str(e)}",
                confidence=0.0,
            )
