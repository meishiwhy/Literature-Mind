"""
LitMind · 章节识别器

根据清洗后的全文，识别论文的标准章节边界。
返回各章节的起始/结束位置及提取的文本。
"""

from __future__ import annotations

import re
from typing import Optional

from .models import PaperSections


# ── 章节标题模式 ──────────────────────────────────────────

# 数字前缀（阿拉伯/罗马/无）
_NUM = r"(?:\d+\.?\s*|(?:I{1,3}V?|IV|VI{0,3})\.?\s*)?"  # "1.", "1", "I.", "II.", "III."

# 英文
SECTION_PATTERNS_EN: dict[str, list[re.Pattern]] = {
    "abstract": [
        re.compile(rf"^{_NUM}[Aa]bstract\s*\.?\s*$"),
        # 也匹配 "Abstract. The study..."（同一行无换行）
        re.compile(rf"^{_NUM}[Aa]bstract\.\s+\w"),
    ],
    "introduction": [
        re.compile(rf"^{_NUM}[Ii]ntroduction\s*$"),
        re.compile(rf"^{_NUM}[Ii]ntroduction\s*\.?\s*$"),
    ],
    "methods": [
        re.compile(rf"^{_NUM}[Mm]ethods?\s*$"),
        re.compile(rf"^{_NUM}[Mm]aterials?\s+(?:and\s+)?[Mm]ethods?\s*$"),
        re.compile(rf"^{_NUM}[Mm]ethodology\s*$"),
        re.compile(rf"^{_NUM}[Ee]xperimental\s+(?:setup|procedures?|design|protocol)\s*$"),
        re.compile(rf"^{_NUM}[Pp]articipants?\s+(?:and\s+)?(?:procedures?|methods?)\s*$"),
        re.compile(rf"^{_NUM}[Ss]ubjects?\s+and\s+[Mm]ethods?\s*$"),
        re.compile(rf"^{_NUM}[Ss]ubjects?\s*[&,]\s*[Mm]ethods?\s*$"),
    ],
    "results": [
        re.compile(rf"^{_NUM}[Rr]esults?\s*$"),
        re.compile(rf"^{_NUM}[Rr]esults?\s+.*$"),
    ],
    "discussion": [
        re.compile(rf"^{_NUM}[Dd]iscussion\s*$"),
    ],
    "conclusion": [
        re.compile(rf"^{_NUM}[Cc]onclusion[s]?\s*$"),
        re.compile(rf"^{_NUM}[Ss]ummary\s*$"),
        re.compile(rf"^{_NUM}[Cc]oncluding\s+[Rr]emarks?\s*$"),
    ],
    "references": [
        re.compile(r"^[Rr]eferences?\s*$"),
        re.compile(r"^[Bb]ibliography\s*$"),
        re.compile(r"^[Cc]itations?\s*$"),
        re.compile(r"^[Ww]orks\s+[Cc]ited\s*$"),
        re.compile(r"^Acknowledg(?:e)?ment\s*$", re.I),
    ],
}

# 中文
SECTION_PATTERNS_CN: dict[str, list[re.Pattern]] = {
    "abstract": [re.compile(r"^摘\s*要\s*\.?\s*$")],
    "introduction": [re.compile(r"^(?:引\s*言|前\s*言|绪\s*论|概\s*述|引\s*论)\s*\.?\s*$")],
    "methods": [re.compile(r"^(?:研究\s*方法|实验\s*方法|材料\s*与\s*方[法式]|方[法式]|实验\s*设计|研究对象)\s*\.?\s*$")],
    "results": [re.compile(r"^(?:研究\s*结果|实验\s*结果|结\s*果|分析\s*结果)\s*\.?\s*$")],
    "discussion": [re.compile(r"^(?:讨\s*论|分析与\s*讨论)\s*\.?\s*$")],
    "conclusion": [re.compile(r"^(?:结\s*论|结\s*语|总\s*结|研究\s*结论)\s*\.?\s*$")],
    "references": [re.compile(r"^(?:参\s*考\s*文\s*献|参考书目|参考文献|致\s*谢)\s*\.?\s*$")],
}


def _merge_patterns() -> dict[str, list[re.Pattern]]:
    """合并中英文所有章节匹配模式"""
    merged: dict[str, list[re.Pattern]] = {}
    for key in SECTION_PATTERNS_EN:
        merged.setdefault(key, []).extend(SECTION_PATTERNS_EN[key])
    for key in SECTION_PATTERNS_CN:
        merged.setdefault(key, []).extend(SECTION_PATTERNS_CN[key])
    return merged


# ── 章节边界检测 ──────────────────────────────────────────

def _detect_section_boundaries(
    lines: list[str],
) -> dict[str, tuple[int, int]]:
    """
    检测章节边界，返回 {section_key: (start_line_idx, end_line_idx)}
    """
    patterns = _merge_patterns()
    boundaries: dict[str, int] = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for section_key, pats in patterns.items():
            if section_key in boundaries:
                continue
            for pat in pats:
                m = pat.match(stripped)
                if m:
                    # 匹配内容短于整行 → 标题和内容在同一行（如 "Abstract. xxx"）
                    is_inline = m.end() < len(stripped)
                    boundaries[section_key] = (i, is_inline)
                    break

    # 按出现顺序排序
    sorted_sections = sorted(boundaries.items(), key=lambda x: x[1][0])

    # 构建区间 [{section_key: (content_start, content_end)}]
    result: dict[str, tuple[int, int]] = {}
    items = list(sorted_sections)
    for idx, (key, (line_idx, inline)) in enumerate(items):
        # 内容起始行
        start = line_idx if inline else line_idx + 1
        # 内容结束行（下一章节标题行）
        if idx + 1 < len(items):
            end = items[idx + 1][1][0]
        else:
            end = len(lines)
        result[key] = (start, end)

    return result


# ── 主导出 ────────────────────────────────────────────────

def sectionize(full_text: str) -> PaperSections:
    """
    将清洗后的全文分割为标准章节。

    Args:
        full_text: 清洗后的论文全文

    Returns:
        PaperSections 对象
    """
    sections = PaperSections()
    lines = full_text.split("\n")

    if not lines or not full_text.strip():
        sections.other = full_text
        return sections

    boundaries = _detect_section_boundaries(lines)

    # 提取各章节内容
    taken_lines: set[int] = set()
    for section_key, (start, end) in boundaries.items():
        content = "\n".join(lines[start + 1:end]).strip()
        setattr(sections, section_key, content)
        taken_lines.update(range(start, end))

    # 剩余内容归入 other
    all_lines_set = set(range(len(lines)))
    remaining = sorted(all_lines_set - taken_lines)
    if remaining:
        other_text = "\n".join(lines[i] for i in remaining).strip()
        sections.other = _distribute_remaining(other_text, boundaries, lines, sections)

    return sections


def _distribute_remaining(
    other_text: str,
    boundaries: dict[str, tuple[int, int]],
    lines: list[str],
    sections: PaperSections,
) -> str:
    """
    尝试将未匹配的文本分配到最近的章节。
    如果无法合理分配，则归入 other。
    """
    # 如果边界为空，全部归入 other
    if not boundaries:
        return other_text

    # 合并 discussion + conclusion（常见写法是合并在一起）
    if not sections.discussion and not sections.conclusion:
        pass  # 保留在 other

    return other_text


# ── 直接从文本提取单个章节 ──────────────────────────────────

def extract_section(text: str, section_name: str) -> str:
    """从文本中提取指定章节的文本"""
    sections = sectionize(text)
    return getattr(sections, section_name, "")
