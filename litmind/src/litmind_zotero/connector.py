"""
LitMind · Zotero Connector

从 Zotero 本地 SQLite 数据库中读取 journalArticle 类型文献，
提取元数据并输出为统一 PaperMetadata 模型。

只读操作，绝不修改数据库。
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from .models import Author, ExportReport, PaperMetadata

FIELD_NAMES: dict[int, str] = {}

# ── 独立附件文件名解析 ──────────────────────────────────────

_RE_FILENAME_META = re.compile(
    r"^(?:"
    r"(?P<author_cn>[一-鿿]+)"              # 中文作者
    r"(?:[\s_\-、]?[\(【]?"                     # 分隔符
    r"(?P<year_cn>\d{4})"                               # 年份
    r"[\)】]?[\s_\-、]?)"                       # 闭括号
    r")?"
    r"(?P<rest>.*?)"
    r"\.pdf$"
)

_RE_FILENAME_EN = re.compile(
    r"^(?P<author_en>[A-Z][a-zà-ü]+(?:\s[A-Z][a-zà-ü]+)*)"  # 英文作者
    r"[\s_\-(]*"
    r"(?:(?:\((?P<year_en>\d{4})\)|(?P<year_en2>\d{4}))[\s_\-]*)?"  # 年份
    r"(?:[\(\[].*?[\)\]][\s_]*)?"                                # 括号信息
    r"(?P<rest_en>.*?)"
    r"\.pdf$"
)


def _resolve_attachment_path(raw: str) -> str:
    """将 Zotero 存储路径转为真实文件路径"""
    if not raw:
        return ""
    if raw.startswith("storage:"):
        return raw[len("storage:"):]
    if raw.startswith("attachments:"):
        return raw[len("attachments:"):]
    if raw.startswith("file://"):
        return raw[len("file://"):].lstrip("/")
    return raw


def _extract_meta_from_filename(filename: str) -> dict:
    """从 PDF 文件名尽量提取标题、作者、年份"""
    name = Path(filename).stem.strip()
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", name)
    year_str = years[0] if years else ""
    cleaned = re.sub(
        r"[\s_\-]*(\.pdf|英文|中文|全文|终稿|修改稿|定稿)\s*$", "", name, flags=re.I
    ).strip()
    return {
        "title": cleaned,
        "year": int(year_str) if year_str.isdigit() else None,
        "filename": filename,
    }


# ── 数据库发现 ──────────────────────────────────────────────

def _find_default_db() -> Optional[Path]:
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        for base in [Path(appdata) / "Zotero" / "Zotero" / "Profiles",
                      Path(appdata) / "Zotero" / "Profiles"]:
            if base.exists():
                candidates.extend(sorted(base.glob("*/zotero.sqlite")))
    home = os.environ.get("HOME", "")
    if home:
        for p in [Path(home) / "Zotero" / "zotero.sqlite",
                  Path(home) / ".zotero" / "zotero.sqlite"]:
            if p.exists():
                candidates.append(p)
    return candidates[0] if candidates else None


def discover_database(custom_path: Optional[Path] = None) -> Path:
    if custom_path:
        if custom_path.exists():
            return custom_path
        raise FileNotFoundError(f"指定路径不存在: {custom_path}")
    found = _find_default_db()
    if found:
        return found
    raise FileNotFoundError("未找到 zotero.sqlite。")


# ── 数据库连接 ──────────────────────────────────────────────

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?immutable=1", uri=True)
    conn.execute("PRAGMA query_only = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def _load_field_names(conn: sqlite3.Connection) -> None:
    FIELD_NAMES.clear()
    for row in conn.execute("SELECT fieldID, fieldName FROM fields"):
        FIELD_NAMES[row["fieldID"]] = row["fieldName"]


# ── 数据提取 ──────────────────────────────────────────────

def _get_creators(conn: sqlite3.Connection, item_id: int) -> list[Author]:
    cur = conn.execute("""
        SELECT c.firstName, c.lastName, ic.orderIndex
        FROM itemCreators ic JOIN creators c ON ic.creatorID = c.creatorID
        WHERE ic.itemID = ? ORDER BY ic.orderIndex
    """, (item_id,))
    return [Author(firstName=r["firstName"] or "", lastName=r["lastName"] or "") for r in cur]


def _get_item_data(conn: sqlite3.Connection, item_id: int) -> dict[str, str]:
    cur = conn.execute("""
        SELECT id.fieldID, idv.value
        FROM itemData id JOIN itemDataValues idv ON id.valueID = idv.valueID
        WHERE id.itemID = ?
    """, (item_id,))
    return {FIELD_NAMES.get(r["fieldID"], f"f{r['fieldID']}"): r["value"] for r in cur}


def _get_attachments(conn: sqlite3.Connection, item_id: int) -> list[str]:
    cur = conn.execute("""
        SELECT path FROM itemAttachments
        WHERE parentItemID = ? AND contentType = 'application/pdf'
        ORDER BY itemID
    """, (item_id,))
    paths = []
    for row in cur:
        raw = row["path"] or ""
        if raw.startswith("attachments:"):
            raw = raw[len("attachments:"):]
        elif raw.startswith("file://"):
            raw = raw[len("file://"):].lstrip("/")
        paths.append(raw)
    return paths


def _get_tags(conn: sqlite3.Connection, item_id: int) -> list[str]:
    cur = conn.execute("""
        SELECT t.name FROM itemTags it JOIN tags t ON it.tagID = t.tagID
        WHERE it.itemID = ? ORDER BY t.name
    """, (item_id,))
    return [r["name"] for r in cur]


def _get_collections(conn: sqlite3.Connection, item_id: int) -> list[str]:
    cur = conn.execute("""
        SELECT c.collectionName
        FROM collectionItems ci JOIN collections c ON ci.collectionID = c.collectionID
        WHERE ci.itemID = ?
    """, (item_id,))
    return [r["collectionName"] for r in cur]


# ── 主导出流程 ──────────────────────────────────────────────

def export_all(db_path: Path, report: ExportReport | None = None) -> list[PaperMetadata]:
    if report is None:
        report = ExportReport()
    conn = _connect(db_path)
    _load_field_names(conn)

    cur = conn.execute("""
        SELECT itemID, key, dateAdded, dateModified FROM items
        WHERE itemTypeID NOT IN (1, 14) AND libraryID = 1
        ORDER BY dateAdded DESC
    """)

    results: list[PaperMetadata] = []
    for row in cur:
        item_id, key = row["itemID"], row["key"]
        try:
            data = _get_item_data(conn, item_id)
            year_str = re.sub(r"[^0-9].*", "", data.get("date", ""))
            pdfs = _get_attachments(conn, item_id)
            meta = PaperMetadata(
                key=key, title=data.get("title", ""),
                authors=_get_creators(conn, item_id),
                year=int(year_str) if year_str.isdigit() else None,
                doi=data.get("DOI", ""),
                journal=data.get("publicationTitle", "") or data.get("journalAbbreviation", ""),
                volume=data.get("volume", ""), issue=data.get("issue", ""),
                pages=data.get("pages", ""),
                abstract=(data.get("abstractNote", "") or "")[:500],
                pdfPath=pdfs[0] if pdfs else "", pdfPaths=pdfs,
                tags=_get_tags(conn, item_id),
                collections=_get_collections(conn, item_id),
                url=data.get("url", ""),
                dateAdded=row["dateAdded"] or "", dateModified=row["dateModified"] or "",
            )
            results.append(meta)
            report.total += 1
            if meta.pdfPath: report.withPdf += 1
            if meta.doi: report.withDoi += 1
            if meta.abstract: report.withAbstract += 1
        except Exception as e:
            report.errors.append(f"[{key}] {e}")

    # ── 导出独立 PDF 附件（没有父条目的 PDF） ──────────────
    standalone_cur = conn.execute("""
        SELECT i.itemID, i.key, i.dateAdded, i.dateModified,
               ia.title AS filename, ia.path, ia.contentType
        FROM items i
        JOIN itemAttachments ia ON i.itemID = ia.itemID
        WHERE i.itemTypeID = 14
          AND i.libraryID = 1
          AND ia.contentType = 'application/pdf'
          AND (ia.parentItemID IS NULL
               OR NOT EXISTS (
                   SELECT 1 FROM items pi
                   WHERE pi.itemID = ia.parentItemID
                     AND pi.itemTypeID NOT IN (1, 14)
               ))
        ORDER BY i.dateAdded DESC
    """)

    for row in standalone_cur:
        try:
            raw_path = row["path"] or ""
            resolved = _resolve_attachment_path(raw_path)
            filename = row["filename"] or Path(resolved).name
            meta_from_name = _extract_meta_from_filename(filename)

            meta = PaperMetadata(
                key=row["key"],
                title=meta_from_name["title"],
                authors=[],
                year=meta_from_name.get("year"),
                pdfPath=resolved,
                pdfPaths=[resolved] if resolved else [],
                itemType="standalone_pdf",
                dateAdded=row["dateAdded"] or "",
                dateModified=row["dateModified"] or "",
            )
            results.append(meta)
            report.standalonePdfs += 1
            if meta.pdfPath:
                report.withPdf += 1
        except Exception as e:
            report.errors.append(f"[{row['key']}] {e}")

    conn.close()
    return results


def export_to_json(papers: list[PaperMetadata], output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in papers], f, ensure_ascii=False, indent=2)
    print(f"  输出: {output_path}")
