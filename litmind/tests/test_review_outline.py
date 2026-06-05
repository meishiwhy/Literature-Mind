import pytest
from litmind_review.outline import OutlineGenerator


class TestOutlineGenerator:
    def test_generate_empty(self):
        gen = OutlineGenerator(llm_provider=None)
        outline = gen.generate("Test", [], [], [], [])
        sections = ["introduction", "landscape", "themes", "consensus", "controversies", "gaps", "future", "conclusion"]
        for s in sections:
            assert s in outline
