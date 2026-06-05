"""Knowledge Base CLI"""

import json
from pathlib import Path

import click
from .service import KnowledgeBase


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("--db", default="", help="SQLite path")
@click.option("--chroma", default="", help="ChromaDB path")
def add(input, db, chroma):
    """新增单篇 PaperAnalysis"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    with open(input, encoding="utf-8") as f:
        analysis = json.load(f)
    pid = kb.add_paper(analysis)
    click.echo(f"已添加: {pid}")


@cli.command()
@click.argument("paper_id")
@click.option("--db", default="")
@click.option("--chroma", default="")
def get(paper_id, db, chroma):
    """获取单篇文献"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    paper = kb.get_paper(paper_id)
    if paper:
        click.echo(json.dumps(paper, ensure_ascii=False, indent=2))
    else:
        click.echo(f"未找到: {paper_id}")


@cli.command()
@click.argument("query")
@click.option("--db", default="")
@click.option("--chroma", default="")
def search(query, db, chroma):
    """关键词检索文献"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    results = kb.search_papers(query)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("query")
@click.option("--top-k", default=10, show_default=True)
@click.option("--db", default="")
@click.option("--chroma", default="")
def semantic(query, top_k, db, chroma):
    """语义搜索"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    results = kb.semantic_search(query, top_k=top_k)
    click.echo(json.dumps(results, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.option("--db", default="")
@click.option("--chroma", default="")
def batch(input_dir, db, chroma):
    """批量导入目录下所有 PaperAnalysis JSON"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    path = Path(input_dir)
    files = list(path.glob("*.json"))
    with click.progressbar(files) as bar:
        for f in bar:
            with open(f, encoding="utf-8") as fh:
                analysis = json.load(fh)
            kb.add_paper(analysis)
    click.echo(f"导入完成: {len(files)} 篇")


@cli.command()
@click.option("--db", default="")
@click.option("--chroma", default="")
def rebuild(db, chroma):
    """重建向量索引"""
    kb = KnowledgeBase(db_path=db, chroma_path=chroma)
    kb.rebuild_index()
    click.echo("索引重建完成")


if __name__ == "__main__":
    cli()
