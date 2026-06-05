#!/usr/bin/env python3
"""
LitMind Evidence Finder — CLI

用法:
    python scripts/evidence.py "Flatfoot increases MTP ROM"
    python scripts/evidence.py "Carbon plate shoes improve jump performance" --top-k 30
    python scripts/evidence.py "query" --json           # JSON 输出
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import click
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_analyzer.providers import AnthropicProvider


@click.command()
@click.argument("query")
@click.option("--top-k", default=20, show_default=True, help="检索论文数")
@click.option("--json-output", is_flag=True, help="输出原始 JSON")
@click.option("--no-llm", is_flag=True, help="不使用 LLM 分类（使用模式匹配）")
def cli(query, top_k, json_output, no_llm):
    """检索并分析科研证据"""

    kb = KnowledgeBase()

    if no_llm:
        service = EvidenceFinderService(kb=kb)
    else:
        provider = AnthropicProvider()
        service = EvidenceFinderService(kb=kb, llm_provider=provider)

    result = service.find_evidence(query, top_k=top_k)

    if json_output:
        click.echo(result.model_dump_json(indent=2, exclude_none=True))
        return

    # 打印摘要
    click.echo(f"\n{'='*60}")
    click.echo(f"  Query: {query}")
    click.echo(f"{'='*60}")

    click.echo(f"\n  Evidence Strength: {result.evidenceStrength}")
    click.echo(f"  Confidence: {result.confidence:.4f}")
    click.echo(f"  Total Papers: {result.totalPapers}")
    click.echo(f"  ├─ Supporting: {result.supportingPapers}")
    click.echo(f"  ├─ Opposing:   {result.opposingPapers}")
    click.echo(f"  └─ Neutral:    {len(result.neutral)}")

    if result.support:
        click.echo(f"\n  ► SUPPORTING EVIDENCE:")
        for item in result.support[:5]:
            click.echo(f"    [{item.paperId}] {item.title or 'Untitled'}")
            click.echo(f"    Claim: {item.claim[:100]}...")
            click.echo(f"    Similarity: {item.similarity:.3f}")
            click.echo()

    if result.oppose:
        click.echo(f"  ► OPPOSING EVIDENCE:")
        for item in result.oppose[:5]:
            click.echo(f"    [{item.paperId}] {item.title or 'Untitled'}")
            click.echo(f"    Claim: {item.claim[:100]}...")
            click.echo()


if __name__ == "__main__":
    cli()
