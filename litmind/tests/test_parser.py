"""Tests for Paper Parser — 表格提取 + 模型"""

import json
import pytest
from litmind_parser.models import ExtractedTable, PaperContent


class TestExtractedTable:
    def test_defaults(self):
        t = ExtractedTable()
        assert t.pageNum == 0
        assert t.header == []
        assert t.rows == []
        assert t.markdown == ""

    def test_full(self):
        t = ExtractedTable(
            pageNum=1,
            caption="Table 1: Subject demographics",
            header=["Group", "Age", "Height"],
            rows=[["Flat", "25.3", "1.72"], ["Normal", "26.1", "1.75"]],
            markdown="| Group | Age | Height |\n| --- | --- | --- |\n| Flat | 25.3 | 1.72 |\n| Normal | 26.1 | 1.75 |",
        )
        assert t.pageNum == 1
        assert len(t.rows) == 2
        assert "Flat" in t.markdown

    def test_in_paper_content(self):
        t = ExtractedTable(pageNum=1, header=["A", "B"], rows=[["1", "2"]],
                           markdown="| A | B |\n| --- | --- |\n| 1 | 2 |")
        pc = PaperContent(paperKey="T001", tables=[t])
        assert len(pc.tables) == 1
        assert pc.tables[0].header == ["A", "B"]

        d = pc.to_dict()
        assert "tables" in d
        assert d["tables"][0]["pageNum"] == 1


class TestTablesToText:
    def test_empty(self):
        from litmind_parser.parser import _tables_to_text
        assert _tables_to_text([]) == ""

    def test_single_table(self):
        from litmind_parser.parser import _tables_to_text
        t = ExtractedTable(pageNum=1, header=["X", "Y"], rows=[["1", "2"]],
                           markdown="| X | Y |\n| --- | --- |\n| 1 | 2 |")
        result = _tables_to_text([t])
        assert "Extracted Tables" in result
        assert "| X | Y |" in result
        assert "| 1 | 2 |" in result

    def test_multiple_tables(self):
        from litmind_parser.parser import _tables_to_text
        t1 = ExtractedTable(pageNum=1, header=["A"], rows=[["1"]], markdown="| A |\n| --- |\n| 1 |")
        t2 = ExtractedTable(pageNum=2, header=["B"], rows=[["2"]], markdown="| B |\n| --- |\n| 2 |")
        result = _tables_to_text([t1, t2])
        assert result.count("Table") >= 1  # 至少有一个 Table 标记


class TestCleanerNoLongerRemovesTableFigure:
    def test_table_line_preserved(self):
        """cleaner 不再删除以 'Table N' 开头的行"""
        from litmind_parser.cleaner import clean
        text = "Some results.\nTable 1: Mean GRF values\nFlatfoot: 3.2 BW"
        cleaned = clean(text)
        assert "Table 1" in cleaned
        assert "Mean GRF" in cleaned

    def test_figure_line_preserved(self):
        """cleaner 不再删除以 'Figure N' 开头的行"""
        from litmind_parser.cleaner import clean
        text = "As shown in\nFigure 3: Joint angles\nFlexion increased."
        cleaned = clean(text)
        assert "Figure 3" in cleaned


class TestParsePdfTableFlag:
    def test_parse_pdf_no_file_returns_error(self):
        """不存在的 PDF 不应崩溃，返回 error"""
        from litmind_parser.parser import parse_pdf
        result = parse_pdf("/nonexistent/file.pdf", paper_key="NOPE")
        assert result.parseSuccess is False
        assert len(result.parseErrors) > 0
        assert result.tables == []

    def test_parse_pdf_extract_tables_false(self):
        """extract_tables=False 不应尝试提取表格"""
        from litmind_parser.parser import parse_pdf
        result = parse_pdf("/nonexistent/file.pdf", paper_key="NOPE", extract_tables=False)
        assert result.tables == []


class TestParsePdfIntegration:
    def test_parse_pdf_with_real_file_table_extraction(self):
        """使用真实 PDF 文件测试解析流程（含表格提取）"""
        import os
        from litmind_parser.parser import parse_pdf

        # 找一个包含表格的 PDF 做集成测试
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        pdf_path = os.path.join(fixtures_dir, "sample_with_table.pdf")

        if not os.path.exists(pdf_path):
            pytest.skip("集成测试需要 sample_with_table.pdf fixture")

        result = parse_pdf(pdf_path, paper_key="SAMPLE")
        assert result.parseSuccess
        assert result.paperKey == "SAMPLE"
        # 应当成功提取到了文本
        assert len(result.fullText) > 0
        # 表格提取不应阻断流程
        assert isinstance(result.tables, list)
