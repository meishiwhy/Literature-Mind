"""
LitMind · 数据模型

PaperMetadata: 统一的论文元数据模型，只含文献元数据，不含 AI 分析。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Author:
    """作者信息"""
    firstName: str = ""
    lastName: str = ""

    def __str__(self) -> str:
        if self.firstName and self.lastName:
            return f"{self.lastName}, {self.firstName}"
        return self.lastName or self.firstName


@dataclass
class PaperMetadata:
    """统一论文元数据模型"""

    # ── 核心标识 ──
    key: str = ""                           # Zotero item key
    title: str = ""                         # 标题
    itemType: str = "journalArticle"        # 文献类型

    # ── 作者 ──
    authors: list[Author] = field(default_factory=list)

    # ── 出版信息 ──
    year: Optional[int] = None
    doi: str = ""
    journal: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""

    # ── 内容 ──
    abstract: str = ""

    # ── PDF ──
    pdfPath: str = ""
    pdfPaths: list[str] = field(default_factory=list)

    # ── 分类 ──
    tags: list[str] = field(default_factory=list)
    collections: list[str] = field(default_factory=list)

    # ── 杂项 ──
    url: str = ""
    dateAdded: str = ""
    dateModified: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, ensure_ascii: bool = False, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> PaperMetadata:
        authors = [Author(**a) if isinstance(a, dict) else a for a in data.get("authors", [])]
        data["authors"] = authors
        return cls(**data)


@dataclass
class ExportReport:
    total: int = 0
    withPdf: int = 0
    withDoi: int = 0
    withAbstract: int = 0
    errors: list[str] = field(default_factory=list)

    def print(self) -> None:
        print(f"\n{'=' * 50}")
        print(f"  LitMind Zotero Connector — 导出报告")
        print(f"{'=' * 50}")
        print(f"  总文献数:     {self.total}")
        if self.total > 0:
            print(f"  有 PDF:       {self.withPdf} ({self.withPdf / self.total * 100:.1f}%)")
            print(f"  有 DOI:       {self.withDoi} ({self.withDoi / self.total * 100:.1f}%)")
            print(f"  有摘要:       {self.withAbstract} ({self.withAbstract / self.total * 100:.1f}%)")
        if self.errors:
            print(f"\n  错误 ({len(self.errors)}):")
            for e in self.errors[:5]:
                print(f"    - {e}")
        print(f"{'=' * 50}\n")
