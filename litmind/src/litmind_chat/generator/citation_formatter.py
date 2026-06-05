"""CitationFormatter — 格式化引用文本"""

from ..models.response import SupportingPaper, SupportingClaim


class CitationFormatter:
    """将 SupportingPaper 和 SupportingClaim 格式化为可读引用"""

    @staticmethod
    def format_paper(paper: SupportingPaper) -> str:
        parts = []
        if paper.authors:
            parts.append(paper.authors)
        if paper.year:
            parts.append(f"({paper.year})")
        if paper.title:
            parts.append(paper.title[:100])
        if paper.journal:
            parts.append(paper.journal)
        if paper.doi:
            parts.append(f"DOI: {paper.doi}")
        return ". ".join(parts) if parts else f"[ID: {paper.paperId}]"

    @staticmethod
    def format_paper_short(paper: SupportingPaper) -> str:
        if paper.authors and paper.year:
            return f"{paper.authors} ({paper.year})"
        return f"[{paper.paperId}]"

    @staticmethod
    def format_claim(claim: SupportingClaim) -> str:
        source = f" [{claim.evidenceSource}]" if claim.evidenceSource else ""
        return f'"{claim.statement}"{source}'
