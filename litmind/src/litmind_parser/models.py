"""
LitMind · PaperContent 数据模型

PaperContent: 结构化论文全文，不含 AI 分析。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class PaperSections:
    """论文各章节原始文本"""
    abstract: str = ""
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    conclusion: str = ""
    references: str = ""
    other: str = ""  # 未匹配到标准章节的内容


@dataclass
class ExtractedTable:
    """从 PDF 中提取的表格"""
    pageNum: int = 0          # 所在页码
    caption: str = ""          # 表格标题/说明
    header: list[str] = field(default_factory=list)   # 表头行
    rows: list[list[str]] = field(default_factory=list)  # 数据行
    markdown: str = ""         # Markdown 格式的完整表格文本


@dataclass
class PaperContent:
    """结构化论文全文"""

    # ── 来源 ──
    paperKey: str = ""               # 对应 PaperMetadata.key (可选)
    sourcePath: str = ""             # PDF 源文件路径

    # ── 原始文本 ──
    fullText: str = ""               # 清洗后的完整文本
    rawText: str = ""                # 清洗前的原始文本

    # ── 结构化章节 ──
    sections: PaperSections = field(default_factory=PaperSections)

    # ── 表格 ──
    tables: list[ExtractedTable] = field(default_factory=list)

    # ── 元数据 ──
    pageCount: int = 0
    charCount: int = 0
    parseSuccess: bool = False
    parseErrors: list[str] = field(default_factory=list)

    # ── 序列化 ──

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_json(self, ensure_ascii: bool = False, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> PaperContent:
        if isinstance(data.get("sections"), dict):
            data["sections"] = PaperSections(**data["sections"])
        return cls(**data)
