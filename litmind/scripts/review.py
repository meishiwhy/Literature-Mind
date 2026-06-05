#!/usr/bin/env python3
"""LitMind Review Generator — CLI"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import click
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_review import ReviewGeneratorService, ReviewInput
from litmind_analyzer.providers.anthropic import AnthropicProvider


@click.command()
@click.argument("topic")
@click.option("--max-papers", default=50, show_default=True, help="Max papers to analyze")
@click.option("--output", "-o", default=None, help="Output JSON path")
@click.option("--json", "json_output", is_flag=True, help="JSON output")
def cli(topic, max_papers, output, json_output):
    kb = KnowledgeBase()
    provider = AnthropicProvider()
    evidence_service = EvidenceFinderService(kb=kb, llm_provider=provider)
    service = ReviewGeneratorService(kb=kb, evidence_service=evidence_service, llm_provider=provider)

    inp = ReviewInput(topic=topic, max_papers=max_papers)
    result = service.generate_review(inp)

    if output:
        import json
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        click.echo(f"输出 -> {output}")
    elif json_output:
        click.echo(result.model_dump_json(indent=2, exclude_none=True))
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"  Topic: {topic}")
        click.echo(f"  Papers: {result.paperCount}")
        click.echo(f"  Themes: {len(result.researchThemes)}")
        click.echo(f"  Consensus: {len(result.researchConsensus)}")
        click.echo(f"  Controversies: {len(result.researchControversies)}")
        click.echo(f"  Gaps: {len(result.researchGaps)}")
        click.echo(f"  Draft: {len(result.reviewDraft)} chars")
        click.echo(f"  Citations: {len(result.citations)}")
        click.echo(f"\n  Draft preview:")
        click.echo(f"  {result.reviewDraft[:500]}...")


if __name__ == "__main__":
    cli()
