"""ResearchChatService — 科研问答统一入口"""

from typing import Optional

from .config import DEFAULT_LLM_MODEL, CACHE_TTL_SECONDS, CACHE_MAX_SIZE, DEFAULT_TOP_K
from .models.query import QueryType
from .models.response import ChatResponse, SearchResult, SupportingPaper, SupportingClaim
from .cache import QueryCache
from .classifier.query_classifier import QueryClassifier
from .context.builder import ContextBuilder
from .generator.answer_generator import AnswerGenerator
from .generator.citation_formatter import CitationFormatter


class ResearchChatService:
    """科研知识库问答系统 — 统一入口"""

    def __init__(
        self,
        kb=None,
        llm_provider=None,
        model: str = "",
    ):
        self.kb = kb
        self.cache = QueryCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)
        self.classifier = QueryClassifier(provider=llm_provider, model=model)
        self.context_builder = ContextBuilder(kb=kb)
        self.generator = AnswerGenerator(provider=llm_provider, model=model or DEFAULT_LLM_MODEL)
        self.formatter = CitationFormatter()

    def ask(self, question: str, top_k: int = DEFAULT_TOP_K) -> ChatResponse:
        cached = self.cache.get(question)
        if cached and isinstance(cached, ChatResponse):
            return cached

        query_type = self.classifier.classify(question)
        context = self.context_builder.retrieve(question, query_type, top_k=top_k)
        sys_prompt, user_prompt = self.context_builder.build_prompt(question, query_type, context)
        response = self.generator.generate(question, sys_prompt, user_prompt)
        response.queryType = query_type

        self.cache.put(question, response)
        return response

    def search(self, question: str, top_k: int = DEFAULT_TOP_K) -> SearchResult:
        query_type = self.classifier.classify(question)
        context = self.context_builder.retrieve(question, query_type, top_k=top_k)

        papers = []
        for p_data in context.get("papers", []):
            if isinstance(p_data, dict):
                papers.append(SupportingPaper(
                    paperId=p_data.get("paperId", ""),
                    title=p_data.get("title", ""),
                    year=p_data.get("year"),
                    authors=p_data.get("authors", ""),
                    journal=p_data.get("journal", ""),
                    doi=p_data.get("doi", ""),
                ))

        claims = []
        for c_data in context.get("claims", []):
            if isinstance(c_data, dict):
                claims.append(SupportingClaim(
                    statement=c_data.get("statement", ""),
                    evidenceSource=c_data.get("evidenceSource", ""),
                    paperId=c_data.get("paperId", ""),
                ))

        return SearchResult(
            query=question,
            queryType=query_type,
            papers=papers,
            claims=claims,
        )

    def get_sources(self, question: str, top_k: int = DEFAULT_TOP_K) -> list[SupportingPaper]:
        search_result = self.search(question, top_k=top_k)
        return search_result.papers
