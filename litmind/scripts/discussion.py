#!/usr/bin/env python3
"""LitMind Discussion Generator -- CLI"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import click
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_discussion import DiscussionGeneratorService, DiscussionInput
from litmind_analyzer.providers import AnthropicProvider


@click.command()
@click.option("--topic", required=True, help="研究主题")
@click.option("--results", required=True, multiple=True, help="研究结果（可多次）")
@click.option("--output", "-o", default=None, help="输出 JSON 路径")
@click.option("--json", "json_output", is_flag=True, help="JSON 输出")
def cli(topic, results, output, json_output):
    kb = KnowledgeBase()
    provider = AnthropicProvider()
    evidence_service = EvidenceFinderService(kb=kb, llm_provider=provider)
    service = DiscussionGeneratorService(evidence_service=evidence_service, llm_provider=provider)

    inp = DiscussionInput(studyTopic=topic, results=list(results))
    result = service.generate_discussion(inp)

    if output:
        out_path = Path(output)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        click.echo(f"输出 -> {out_path}")
    elif json_output:
        click.echo(result.model_dump_json(indent=2, exclude_none=True))
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"  Topic: {topic}")
        click.echo(f"{'='*60}")
        click.echo(f"\n  Outline:")
        for k, v in result.discussionOutline.items():
            click.echo(f"    - {k}: {v}")
        click.echo(f"\n  Draft ({len(result.discussionDraft)} chars):")
        click.echo(f"  {result.discussionDraft[:500]}...")
        click.echo(f"\n  Citations: {len(result.citations)}")
        click.echo(f"  Supporting: {len(result.supportingPapers)} papers")
        click.echo(f"  Opposing: {len(result.opposingPapers)} papers")


if __name__ == "__main__":
    cli()
