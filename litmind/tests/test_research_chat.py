import pytest
from litmind_chat.models.query import QueryType, ChatQuery
from litmind_chat.models.response import ChatResponse, SupportingPaper, SupportingClaim


class TestModels:
    def test_query_type_values(self):
        assert QueryType.PAPER_SEARCH.value == "paper_search"
        assert QueryType.CLAIM_SEARCH.value == "claim_search"
        assert QueryType.GENERAL_QUESTION.value == "general_question"

    def test_chat_query_defaults(self):
        q = ChatQuery(question="Does flatfoot increase motion?")
        assert q.question == "Does flatfoot increase motion?"
        assert q.top_k == 10

    def test_supporting_paper(self):
        p = SupportingPaper(paperId="P1", title="Test", year=2024, authors="Author A")
        assert p.title == "Test"
        assert p.doi == ""

    def test_chat_response_defaults(self):
        r = ChatResponse(answer="Test answer")
        assert r.answer == "Test answer"
        assert r.supportingPapers == []
        assert r.supportingClaims == []
        assert r.confidence == 0.0

    def test_chat_response_with_claims(self):
        c = SupportingClaim(statement="X", evidenceSource="Results", paperId="P1")
        r = ChatResponse(answer="A", supportingClaims=[c])
        assert r.answer == "A"
        assert r.supportingClaims[0].statement == "X"


class TestCache:
    def test_cache_set_get(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=60)
        cache.put("test_q", "result")
        assert cache.get("test_q") == "result"

    def test_cache_expiry(self):
        import time
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=1)
        cache.put("test_q", "result")
        time.sleep(1.5)
        assert cache.get("test_q") is None

    def test_cache_max_size(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=2, ttl=60)
        cache.put("q1", "r1")
        cache.put("q2", "r2")
        cache.put("q3", "r3")
        assert cache.get("q1") is None
        assert cache.get("q3") == "r3"

    def test_cache_clear(self):
        from litmind_chat.cache import QueryCache
        cache = QueryCache(max_size=10, ttl=60)
        cache.put("q1", "r1")
        cache.clear()
        assert cache.get("q1") is None


class TestQueryClassifier:
    def test_classify_paper_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("哪些文献研究了 Flatfoot？")
        assert result == "paper_search"

    def test_classify_paper_search_recommend(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("推荐几篇关于足弓生物力学的文献")
        assert result == "paper_search"

    def test_classify_statistic_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("哪些文献使用了 SPM1D？")
        assert result == "statistic_search"

    def test_classify_statistic_search_anova(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("用了什么统计方法？")
        assert result == "statistic_search"

    def test_classify_claim_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("有哪些研究支持 Flatfoot increases forefoot motion？")
        assert result == "claim_search"

    def test_classify_claim_search_chinese(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("有没有证据表明碳板鞋能减少 MTP 活动度？")
        assert result == "claim_search"

    def test_classify_evidence_search_english(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("Does flatfoot increase forefoot motion?")
        assert result in ("evidence_search", "general_question")

    def test_classify_evidence_search_chinese(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("扁平足是否会影响踝关节活动度？")
        assert result == "evidence_search"

    def test_classify_evidence_search_relationship(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("足弓高度与 GRF 之间的关系")
        assert result == "evidence_search"

    def test_classify_trend_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("目前关于 Foot Arch 的研究热点有哪些？")
        assert result == "trend_search"

    def test_classify_trend_search_progress(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("碳板跑鞋的最新研究进展")
        assert result == "trend_search"

    def test_classify_variable_search(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("该研究关注了哪些变量？")
        assert result == "variable_search"

    def test_classify_general_question(self):
        from litmind_chat.classifier.query_classifier import QueryClassifier
        classifier = QueryClassifier(provider=None)
        result = classifier.classify("Tell me about foot biomechanics")
        assert result == "general_question"


class TestContextBuilder:
    @pytest.fixture
    def builder(self):
        from litmind_chat.context.builder import ContextBuilder
        return ContextBuilder(kb=None)

    def test_retrieve_no_kb(self, builder):
        result = builder.retrieve("flatfoot", "paper_search", top_k=10)
        assert result["papers"] == []
        assert result["claims"] == []

    def test_build_system_prompt(self, builder):
        prompt = builder.build_system_prompt()
        assert "证据" in prompt or "evidence" in prompt.lower()

    def test_format_papers_empty(self, builder):
        formatted = builder._format_papers([])
        assert formatted == ""

    def test_build_user_prompt_basic(self, builder):
        import json
        context = {"papers": [{"paperId": "P1", "title": "Test Flatfoot Study", "year": 2024}],
                   "claims": [], "semantic_results": [],
                   "variables": [], "statistics": []}
        prompt = builder.build_user_prompt("Flatfoot research?", "paper_search", context)
        assert "Flatfoot" in prompt
        assert "Test Flatfoot Study" in prompt


class TestCitationFormatter:
    def test_format_paper_short(self):
        from litmind_chat.generator.citation_formatter import CitationFormatter
        from litmind_chat.models.response import SupportingPaper
        p = SupportingPaper(paperId="P1", title="Test", year=2024, authors="Stone et al.", doi="10.1234/test")
        result = CitationFormatter.format_paper_short(p)
        assert "Stone et al." in result

    def test_format_paper_full(self):
        from litmind_chat.generator.citation_formatter import CitationFormatter
        from litmind_chat.models.response import SupportingPaper
        p = SupportingPaper(paperId="P1", title="Flatfoot Biomechanics", year=2024, authors="Stone", journal="J Biomech", doi="10.1234/test")
        result = CitationFormatter.format_paper(p)
        assert "DOI" in result

    def test_format_claim(self):
        from litmind_chat.generator.citation_formatter import CitationFormatter
        from litmind_chat.models.response import SupportingClaim
        c = SupportingClaim(statement="Flatfoot increases motion", evidenceSource="Results", paperId="P1")
        result = CitationFormatter.format_claim(c)
        assert "Flatfoot" in result


class TestAnswerGenerator:
    def test_generate_with_mock(self):
        from litmind_chat.generator.answer_generator import AnswerGenerator
        from litmind_analyzer.provider import LLMProvider

        class MockProvider(LLMProvider):
            def analyze(self, system_prompt, user_prompt):
                return {
                    "answer": "Flatfoot increases forefoot motion based on current evidence.",
                    "supportingPapers": [
                        {"paperId": "P1", "title": "Flatfoot Study", "year": 2024, "authors": "Stone et al."}
                    ],
                    "supportingClaims": [
                        {"statement": "Flatfoot increases forefoot motion", "evidenceSource": "Results", "paperId": "P1"}
                    ],
                    "confidence": 0.91,
                }

        gen = AnswerGenerator(provider=MockProvider())
        result = gen.generate("Does flatfoot increase motion?", "System prompt", "User prompt")
        assert result.answer == "Flatfoot increases forefoot motion based on current evidence."
        assert len(result.supportingPapers) == 1
        assert result.confidence == 0.91

    def test_generate_empty_fallback(self):
        from litmind_chat.generator.answer_generator import AnswerGenerator
        from litmind_analyzer.provider import LLMProvider

        class FailingProvider(LLMProvider):
            def analyze(self, system_prompt, user_prompt):
                raise Exception("API Error")

        gen = AnswerGenerator(provider=FailingProvider())
        result = gen.generate("question", "sys", "user")
        assert result.confidence == 0.0

    def test_generate_no_provider(self):
        from litmind_chat.generator.answer_generator import AnswerGenerator
        gen = AnswerGenerator(provider=None)
        result = gen.generate("question", "sys", "user")
        assert result.confidence == 0.0
        assert "未配置" in result.answer or "no LLM" in result.answer.lower()


class TestResearchChatService:
    @pytest.fixture
    def service(self):
        from litmind_chat.service import ResearchChatService
        return ResearchChatService(kb=None)

    def test_ask_basic(self, service):
        result = service.ask("哪些文献研究了 Flatfoot？")
        assert result.queryType == "paper_search"
        assert result.answer != ""

    def test_search_only(self, service):
        result = service.search("SPM1D")
        assert result.queryType == "statistic_search"

    def test_get_sources(self, service):
        sources = service.get_sources("Does flatfoot increase motion?")
        assert isinstance(sources, list)

    def test_ask_caching(self, service):
        result1 = service.ask("test question")
        result2 = service.ask("test question")
        assert result1.answer == result2.answer

    def test_search_returns_result_model(self, service):
        from litmind_chat.models.response import SearchResult
        result = service.search("flatfoot")
        assert isinstance(result, SearchResult)
