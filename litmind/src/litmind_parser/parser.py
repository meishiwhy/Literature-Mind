"""
LitMind · Paper Parser 主入口

从 PDF 读取全文 + 提取表格 → 清洗 → 识别章节 → 输出 PaperContent。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from .cleaner import clean
from .models import ExtractedTable, PaperContent, PaperSections
from .sectionizer import sectionize

logger = logging.getLogger(__name__)


# ── PDF 读取器（pymupdf / 备用） ──────────────────────────

def _read_pdf_pymupdf(pdf_path: str) -> tuple[str, list[str], int]:
    """
    使用 pymupdf 读取 PDF。
    返回 (全文, 每页文本列表, 页数)
    """
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    pages: list[str] = []
    full_text_parts: list[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")
        pages.append(page_text)
        full_text_parts.append(page_text)

    doc.close()
    return "\n\n".join(full_text_parts), pages, len(pages)


def _extract_tables_pymupdf(pdf_path: str) -> list[ExtractedTable]:
    """
    使用 pymupdf 的 find_tables() 提取 PDF 中所有表格。
    返回 ExtractedTable 列表。
    """
    import fitz  # pymupdf
    doc = fitz.open(pdf_path)
    tables: list[ExtractedTable] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        found = page.find_tables()
        for t in found:
            # t.extract() 返回 list[list[str]]，第一行是 header
            raw = t.extract()
            if not raw or len(raw) < 1:
                continue

            header = raw[0] if raw else []
            rows = raw[1:] if len(raw) > 1 else []

            # 构建 Markdown 表格
            md_lines: list[str] = []
            # 表头
            if header:
                md_lines.append("| " + " | ".join(header) + " |")
                md_lines.append("| " + " | ".join("---" for _ in header) + " |")
            # 数据行
            for row in rows:
                # 补齐短行
                while len(row) < len(header):
                    row.append("")
                md_lines.append("| " + " | ".join(row) + " |")

            tables.append(ExtractedTable(
                pageNum=page_num + 1,
                header=header,
                rows=rows,
                markdown="\n".join(md_lines),
            ))

    doc.close()
    return tables


def _read_pdf_fallback(pdf_path: str) -> tuple[str, list[str], int]:
    """
    备用：使用 pdfplumber 或 PyPDF2 读取 PDF。
    """
    try:
        import pdfplumber
        pages: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                text = p.extract_text() or ""
                pages.append(text)
        return "\n\n".join(pages), pages, len(pages)
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        pages = []
        reader = PdfReader(pdf_path)
        for p in reader.pages:
            text = p.extract_text() or ""
            pages.append(text)
        return "\n\n".join(pages), pages, len(pages)
    except ImportError:
        pass

    raise ImportError(
        "需要安装 PDF 解析库:\n"
        "  pip install pymupdf\n"
        "  或 pip install pdfplumber\n"
        "  或 pip install PyPDF2"
    )


def read_pdf(pdf_path: str) -> tuple[str, list[str], int]:
    """读取 PDF，自动选择可用的解析引擎"""
    try:
        return _read_pdf_pymupdf(pdf_path)
    except ImportError:
        return _read_pdf_fallback(pdf_path)


def _tables_to_text(tables: list[ExtractedTable]) -> str:
    """将提取的表格转为纯文本，拼接到全文末尾"""
    if not tables:
        return ""
    parts = ["\n\n--- Extracted Tables ---"]
    for i, t in enumerate(tables, 1):
        caption = t.caption or f"Table {i}"
        parts.append(f"\n[{caption}]\n{t.markdown}")
    return "\n".join(parts)


# ── 主导出 ────────────────────────────────────────────────

def parse_pdf(
    pdf_path: str,
    paper_key: str = "",
    engine: str = "auto",
    extract_tables: bool = True,
) -> PaperContent:
    """
    解析单篇 PDF，返回结构化的 PaperContent。

    Args:
        pdf_path: PDF 文件路径
        paper_key: 对应的 Zotero paper key（可选）
        engine: PDF 解析引擎 (auto / pymupdf / pdfplumber / PyPDF2)
        extract_tables: 是否提取表格（仅 pymupdf 支持）

    Returns:
        PaperContent 对象
    """
    content = PaperContent(
        paperKey=paper_key,
        sourcePath=pdf_path,
    )

    if not pdf_path or not os.path.exists(pdf_path):
        content.parseErrors.append(f"PDF 文件不存在: {pdf_path}")
        return content

    try:
        # 1. 读取原始文本
        if engine == "auto":
            full_text, pages, page_count = read_pdf(pdf_path)
        else:
            content.parseErrors.append(f"不支持的引擎: {engine}")
            return content

        content.rawText = full_text
        content.pageCount = page_count

        if not full_text.strip():
            content.parseErrors.append("PDF 中未提取到文本")
            return content

        # 2. 提取表格（仅 pymupdf）
        if extract_tables:
            try:
                content.tables = _extract_tables_pymupdf(pdf_path)
            except ImportError:
                pass  # 无 pymupdf 时静默跳过表格提取

        # 3. 将表格 markdown 拼接到全文末尾（供 LLM 分析使用）
        table_text = _tables_to_text(content.tables)

        # 4. 清洗
        cleaned = clean(full_text, pages=pages)
        content.fullText = cleaned + table_text

        # 5. 章节识别
        content.sections = sectionize(cleaned)
        content.charCount = len(cleaned)

        # 6. 统计
        content.parseSuccess = True

    except Exception as e:
        content.parseErrors.append(f"解析错误: {e}")

    return content


def parse_multiple(
    pdf_paths: list[tuple[str, str]],  # [(pdf_path, paper_key), ...]
    engine: str = "auto",
) -> list[PaperContent]:
    """批量解析多篇 PDF"""
    results = []
    total = len(pdf_paths)
    for idx, (path, key) in enumerate(pdf_paths, 1):
        if idx % 5 == 0 or idx == 1 or idx == total:
            logger.info("Parsing PDF %d/%d: %s", idx, total, path)
        result = parse_pdf(path, paper_key=key, engine=engine)
        results.append(result)
    logger.info("Parsed %d/%d PDFs successfully", total, total)
    return results
