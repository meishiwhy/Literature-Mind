#!/usr/bin/env python3
"""
LitMind Paper Analyzer — CLI

用法:
    litmind-analyze paper.json -o analysis.json
    litmind-analyze paper.json --provider openai --model gpt-4o
    litmind-analyze batch ./parsed/ -o ./analyses/
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import click
from litmind_analyzer.analyzer import analyze_paper
from litmind_analyzer.providers import AnthropicProvider, OpenAIProvider


def _get_provider(provider_name, api_key, model):
    providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
    }
    cls = providers.get(provider_name)
    if not cls:
        raise click.BadParameter(f"Unknown provider: {provider_name} (use: anthropic, openai)")
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if model:
        kwargs["model"] = model
    return cls(**kwargs)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Output JSON path")
@click.option("--provider", default="anthropic", show_default=True, help="LLM provider")
@click.option("--model", default="", help="Model name")
@click.option("--api-key", default=None, help="API key (overrides env var)")
def single(input, output, provider, model, api_key):
    """分析单篇 PaperContent JSON"""
    with open(input, encoding="utf-8") as f:
        paper = json.load(f)

    prov = _get_provider(provider, api_key, model)
    result = analyze_paper(paper, prov)

    output_path = Path(output or f"{Path(input).stem}_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2, exclude_none=True))

    click.echo(f"分析完成 → {output_path}")


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="analyses", help="Output directory")
@click.option("--provider", default="anthropic", show_default=True)
@click.option("--model", default="")
@click.option("--api-key", default=None)
def batch(input_dir, output, provider, model, api_key):
    """批量分析目录下的所有 PaperContent JSON"""
    input_path = Path(input_dir)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    prov = _get_provider(provider, api_key, model)
    files = list(input_path.glob("*.json"))
    success = 0

    with click.progressbar(files, label="分析论文") as bar:
        for f in bar:
            with open(f, encoding="utf-8") as fh:
                paper = json.load(fh)
            result = analyze_paper(paper, prov)
            out_file = output_path / f"{f.stem}_analysis.json"
            with open(out_file, "w", encoding="utf-8") as fh:
                fh.write(result.model_dump_json(indent=2, exclude_none=True))
            success += 1

    click.echo(f"完成: {success}/{len(files)}")


if __name__ == "__main__":
    cli()
