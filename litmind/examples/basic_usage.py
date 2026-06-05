#!/usr/bin/env python3
"""LitMind Zotero Connector — 使用示例"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from litmind_zotero import discover_database, export_all, export_to_json


def main():
    db = discover_database()
    print(f"数据库: {db}")
    papers = export_all(db)
    print(f"共 {len(papers)} 篇\n")
    for i, p in enumerate(papers[:3], 1):
        print(f"--- #{i} ---")
        print(f"  {p.title[:80]}")
        print(f"  {', '.join(str(a) for a in p.authors[:3])} | {p.year} | {p.journal}")
        print()
    export_to_json(papers, Path("example_export.json"))


if __name__ == "__main__":
    main()
