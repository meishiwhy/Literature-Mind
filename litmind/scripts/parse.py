#!/usr/bin/env python3
"""
LitMind Paper Parser — CLI 入口

用法:
    # 解析单篇 PDF
    python scripts/parse.py path/to/paper.pdf -o paper.json

    # 从 Zotero 导出 JSON 批量解析
    python scripts/parse.py --from-zotero litmind_export.json -o output_dir/

    # 指定解析引擎
    python scripts/parse.py paper.pdf --engine pymupdf
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from litmind_parser import parse_pdf


def cmd_single(args):
    """解析单篇 PDF"""
    pdf_path = args.pdf
    if not Path(pdf_path).exists():
        print(f"错误: 文件不存在 {pdf_path}")
        sys.exit(1)

    result = parse_pdf(pdf_path, engine=args.engine)

    if args.output:
        output_path = Path(args.output)
    else:
        stem = Path(pdf_path).stem
        output_path = Path(f"{stem}_parsed.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"解析完成: {result.pageCount} 页, {result.charCount} 字符")
    print(f"输出: {output_path}")

    if result.parseErrors:
        print(f"错误 ({len(result.parseErrors)}):")
        for e in result.parseErrors:
            print(f"  - {e}")


def cmd_batch(args):
    """从 Zotero 导出文件批量解析"""
    zotero_path = Path(args.from_zotero)
    if not zotero_path.exists():
        print(f"错误: 文件不存在 {zotero_path}")
        sys.exit(1)

    with open(zotero_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    output_dir = Path(args.output) if args.output else Path("parsed_papers")
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(papers)
    success = 0
    errors = []

    for i, paper in enumerate(papers, 1):
        pdf_path = paper.get("pdfPath", "")
        paper_key = paper.get("key", "")
        print(f"[{i}/{total}] {paper.get('title', '')[:50]}...", end=" ")

        if not pdf_path or not Path(pdf_path).exists():
            print(f"⚠ PDF 不存在")
            errors.append(f"[{paper_key}] PDF 不存在: {pdf_path}")
            continue

        result = parse_pdf(pdf_path, paper_key=paper_key, engine=args.engine)

        # 保存
        output_file = output_dir / f"{paper_key}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        if result.parseSuccess:
            success += 1
            print(f"✓ ({result.pageCount}页, {result.charCount}字)")
        else:
            errors.extend(result.parseErrors)
            print(f"✗ {result.parseErrors[0] if result.parseErrors else '未知错误'}")

    print(f"\n完成: {success}/{total} 成功")
    if errors:
        print(f"错误 ({len(errors)}):")
        for e in errors[:5]:
            print(f"  - {e}")


def main():
    p = argparse.ArgumentParser(description="LitMind Paper Parser")
    sub = p.add_subparsers(dest="command")

    # single
    ps = sub.add_parser("single", help="解析单篇 PDF")
    ps.add_argument("pdf", type=str, help="PDF 文件路径")
    ps.add_argument("-o", "--output", type=str, default=None, help="输出 JSON 路径")
    ps.add_argument("--engine", type=str, default="auto", choices=["auto", "pymupdf", "pdfplumber", "PyPDF2"])
    ps.set_defaults(func=cmd_single)

    # batch
    pb = sub.add_parser("batch", help="从 Zotero 导出 JSON 批量解析")
    pb.add_argument("--from-zotero", type=str, required=True, help="Zotero 导出 JSON (litmind_export.json)")
    pb.add_argument("-o", "--output", type=str, default=None, help="输出目录")
    pb.add_argument("--engine", type=str, default="auto")
    pb.set_defaults(func=cmd_batch)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
