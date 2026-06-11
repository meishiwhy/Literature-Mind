"""Research Chat CLI — 交互式问答"""

import json
import logging
import os
from pathlib import Path

import click
from litmind_chat.service import ResearchChatService
from litmind_chat.generator.citation_formatter import CitationFormatter


def _setup_logging():
    level = os.environ.get("LITMIND_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.WARNING),
        format="[litmind] %(levelname)s %(name)s: %(message)s",
    )

import click
from litmind_chat.service import ResearchChatService
from litmind_chat.generator.citation_formatter import CitationFormatter


def _get_provider(provider_name: str, api_key: str | None, model: str | None):
    if provider_name == "anthropic":
        from litmind_analyzer.providers import AnthropicProvider
        return AnthropicProvider(api_key=api_key or "", model=model or "claude-sonnet-4-20250514")
    elif provider_name == "openai":
        from litmind_analyzer.providers import OpenAIProvider
        return OpenAIProvider(api_key=api_key or "", model=model or "gpt-4o")
    return None


@click.group()
def cli():
    _setup_logging()


@cli.command()
@click.argument("question")
@click.option("--provider", default="anthropic", show_default=True)
@click.option("--model", default="")
@click.option("--api-key", default=None)
@click.option("--db", default="", help="SQLite path")
@click.option("--chroma", default="", help="ChromaDB path")
@click.option("--json-output", is_flag=True, help="Output as JSON")
def ask(question, provider, model, api_key, db, chroma, json_output):
    """提问并获取答案"""
    from litmind_knowledge.service import KnowledgeBase
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    llm_provider = _get_provider(provider, api_key, model)

    service = ResearchChatService(kb=kb, llm_provider=llm_provider)
    result = service.ask(question)

    if json_output:
        click.echo(result.model_dump_json(indent=2, ensure_ascii=False))
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"Q: {question}")
        click.echo(f"{'='*60}")
        click.echo(f"\n{result.answer}\n")
        if result.supportingPapers:
            click.echo("📚 相关文献:")
            for p in result.supportingPapers:
                click.echo(f"  - {CitationFormatter.format_paper(p)}")
        if result.supportingClaims:
            click.echo("\n📎 支撑证据:")
            for c in result.supportingClaims:
                click.echo(f"  - {CitationFormatter.format_claim(c)}")
        click.echo(f"\n置信度: {result.confidence:.2f}")


@cli.command()
@click.argument("question")
@click.option("--db", default="")
@click.option("--chroma", default="")
@click.option("--json-output", is_flag=True)
def search(question, db, chroma, json_output):
    """仅检索知识库，不生成答案"""
    from litmind_knowledge.service import KnowledgeBase
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    service = ResearchChatService(kb=kb)
    result = service.search(question)

    if json_output:
        click.echo(result.model_dump_json(indent=2, ensure_ascii=False))
    else:
        click.echo(f"\n相关文献 ({len(result.papers)}):")
        for p in result.papers:
            click.echo(f"  - {CitationFormatter.format_paper(p)}")
        if result.claims:
            click.echo(f"\n相关结论 ({len(result.claims)}):")
            for c in result.claims:
                click.echo(f"  - {CitationFormatter.format_claim(c)}")


@cli.command()
@click.option("--provider", default="anthropic", show_default=True)
@click.option("--db", default="")
@click.option("--chroma", default="")
def interactive(provider, db, chroma):
    """交互式问答模式"""
    from litmind_knowledge.service import KnowledgeBase

    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    llm_provider = _get_provider(provider, api_key, None)
    service = ResearchChatService(kb=kb, llm_provider=llm_provider)

    click.echo("\n🔬 LitMind Research Chat — 输入问题开始查询 (输入 /exit 退出)\n")

    while True:
        question = click.prompt("\n❓", prompt_suffix=" ")
        if question.lower() in ("/exit", "/quit", "exit", "quit"):
            break

        result = service.ask(question)

        click.echo(f"\n{result.answer}\n")
        if result.supportingPapers:
            click.echo("📚 相关文献:")
            for p in result.supportingPapers[:3]:
                click.echo(f"  - {CitationFormatter.format_paper_short(p)}")
        if result.supportingClaims:
            click.echo("📎 证据:")
            for c in result.supportingClaims[:3]:
                click.echo(f"  - {CitationFormatter.format_claim(c)}")


if __name__ == "__main__":
    cli()
