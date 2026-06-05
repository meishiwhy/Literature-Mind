#!/usr/bin/env python3
"""
LitMind Zotero Connector — CLI 入口

用法:
    python scripts/cli.py export                          # 自动导出
    python scripts/cli.py export --db /path/to/zotero.sqlite -o papers.json
    python scripts/cli.py stats                           # 仅统计
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from litmind_zotero import ExportReport, discover_database, export_all, export_to_json


def cmd_export(args):
    db = discover_database(args.db)
    print(f"数据库: {db}")
    report = ExportReport()
    papers = export_all(db, report=report)
    export_to_json(papers, Path(args.output or "litmind_export.json"))
    report.print()


def cmd_stats(args):
    db = discover_database(args.db)
    print(f"数据库: {db}")
    report = ExportReport()
    export_all(db, report=report)
    report.print()


def main():
    p = argparse.ArgumentParser(description="LitMind Zotero Connector")
    sub = p.add_subparsers(dest="command")

    pe = sub.add_parser("export", help="导出所有 journalArticle")
    pe.add_argument("--db", "-d", type=Path, default=None)
    pe.add_argument("--output", "-o", type=str, default=None)
    pe.set_defaults(func=cmd_export)

    ps = sub.add_parser("stats", help="仅统计")
    ps.add_argument("--db", "-d", type=Path, default=None)
    ps.set_defaults(func=cmd_stats)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
