"""
LitMind · 文本清洗器

去除 PDF 提取文本中的：
- 页眉 / 页脚（跨页重复文本）
- 页码
- 重复内容
"""

from __future__ import annotations

import re
from collections import Counter


# ── 页码模式 ──────────────────────────────────────────────

PAGE_NUM_PATTERNS = [
    re.compile(r"^\s*\d+\s*$"),                    # 纯数字行 "12"
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),            # "- 12 -"
    re.compile(r"^\s*\d+\s*of\s*\d+\s*$", re.I),   # "12 of 20"
    re.compile(r"^\s*Page\s*\d+\s*$", re.I),       # "Page 12"
    re.compile(r"^\s*第\s*\d+\s*页\s*$"),          # "第12页"
]


def _is_page_number(line: str) -> bool:
    """判断一行是否仅为页码"""
    for pat in PAGE_NUM_PATTERNS:
        if pat.match(line):
            return True
    return False


# ── 页眉/页脚检测 ────────────────────────────────────────

def _find_repeated_lines(pages: list[list[str]], threshold: float = 0.6) -> set[str]:
    """
    找出在超过 threshold 比例的页面中重复出现的行。
    这些很可能是页眉或页脚。
    """
    if len(pages) < 3:
        return set()

    # 只看每页的前 3 行和后 3 行
    candidates: list[str] = []
    for page in pages:
        candidates.extend(page[:3])
        if len(page) > 3:
            candidates.extend(page[-3:])

    # 统计出现次数
    counter = Counter(candidates)
    min_count = max(2, int(len(pages) * threshold))

    return {line for line, count in counter.items() if count >= min_count}


def _remove_repeated_lines(
    text: str,
    repeated: set[str],
    lines_per_page: int = 3,
) -> str:
    """移除重复的页眉/页脚行"""
    blocks = text.split("\n\n")  # 按段落分割
    cleaned = []
    for block in blocks:
        lines = block.split("\n")
        # 如果整个块就是重复行，跳过
        if len(lines) <= lines_per_page and all(
            l.strip() in repeated for l in lines if l.strip()
        ):
            continue
        # 否则保留
        cleaned.append(block)
    return "\n\n".join(cleaned)


# ── 重复段落去重 ──────────────────────────────────────────

def _deduplicate_paragraphs(text: str) -> str:
    """去除相邻的重复段落"""
    paragraphs = text.split("\n\n")
    deduped = []
    prev = ""
    for para in paragraphs:
        stripped = para.strip()
        if stripped and stripped != prev:
            deduped.append(para)
            prev = stripped
        elif not stripped:
            deduped.append(para)
    return "\n\n".join(deduped)


# ── 噪声行清理 ────────────────────────────────────────────

NOISE_PATTERNS = [
    re.compile(r"^\s*doi:\s*10\.\S+", re.I),
    re.compile(r"^\s*(received|accepted|published)\s*:", re.I),
    re.compile(r"^\s*correspondence\s*(to|author)", re.I),
    re.compile(r"^\s*e[- ]?mail\s*:"),
    re.compile(r"^\s*copyright\s.*", re.I),
    re.compile(r"^\s*©\s"),
    re.compile(r"^\s*This\s+article\s+is\s+(an?\s+)?(open\s+access|protected|distributed)", re.I),
    re.compile(r"^\s*Figure\s+\d+[\.\-\s]"),
    re.compile(r"^\s*Table\s+\d+[\.\-\s]"),
    re.compile(r"^\s*Author\s+(contributions|note)", re.I),
    re.compile(r"^\s*Conflict", re.I),
    re.compile(r"^\s*Funding", re.I),
    re.compile(r"^\s*Data\s+availability", re.I),
    re.compile(r"^\s*Supplementary", re.I),
    re.compile(r"^\s*Supporting\s+information", re.I),
    re.compile(r"^\s*Ethics", re.I),
]


def _remove_noise_lines(text: str) -> str:
    """移除明显的噪声行"""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if not line.strip():
            cleaned.append(line)
            continue
        if any(pat.match(line) for pat in NOISE_PATTERNS):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ── 主导出 ────────────────────────────────────────────────

def clean(text: str, pages: list[str] | None = None) -> str:
    """
    清洗 PDF 提取文本。

    Args:
        text: 原始提取文本
        pages: 每页文本列表（用于页眉/页脚检测）

    Returns:
        清洗后的文本
    """
    # 1. 页码
    lines = text.split("\n")
    text = "\n".join(l for l in lines if not _is_page_number(l))

    # 2. 页眉/页脚（如果有分页信息）
    if pages and len(pages) > 2:
        page_lines = [p.split("\n") for p in pages]
        repeated = _find_repeated_lines(page_lines)
        if repeated:
            text = _remove_repeated_lines(text, repeated)

    # 3. 噪声行
    text = _remove_noise_lines(text)

    # 4. 重复段落
    text = _deduplicate_paragraphs(text)

    # 5. 多余空白
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text
