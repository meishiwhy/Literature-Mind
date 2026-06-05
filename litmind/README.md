# LitMind

学术文献智能处理工具集。三个模块，覆盖文献从元数据到结构化知识的全流程。

| 模块 | 功能 | 路径 |
|---|---|---|
| **litmind-zotero** | Zotero Connector — 导出文献元数据 | `src/litmind_zotero/` |
| **litmind-parser** | Paper Parser — PDF 解析与结构化 | `src/litmind_parser/` |
| **litmind-analyzer** | Paper Analyzer — LLM 论文知识提取 | `src/litmind_analyzer/` |

---

## 模块一：Zotero Connector

从 Zotero 本地 SQLite 数据库读取 **journalArticle** 类型文献，提取元数据并输出为统一的 `PaperMetadata` 数据模型。

### CLI

```bash
python scripts/cli.py export
python scripts/cli.py export --db /path/to/zotero.sqlite -o papers.json
python scripts/cli.py stats
```

### Python API

```python
from litmind_zotero import discover_database, export_all, export_to_json
papers = export_all(discover_database())
export_to_json(papers, "papers.json")
```

---

## 模块二：Paper Parser

从 PDF 提取全文 → 自动清洗（页眉/页脚/页码/重复）→ 识别标准章节 → 输出结构化 `PaperContent`。

### CLI

```bash
# 单篇解析
python scripts/parse.py single paper.pdf -o parsed.json

# 批量解析（从 Zotero 导出出发）
python scripts/parse.py batch --from-zotero papers.json -o parsed/
```

### Python API

```python
from litmind_parser import parse_pdf
result = parse_pdf("paper.pdf")
print(f"{result.pageCount} 页, {result.charCount} 字符")
print(result.sections.abstract[:200])
```

---

## 模块三：Paper Analyzer

将 `PaperContent` 通过 LLM 分析，提取结构化科研知识。**不做自由文本摘要。**

输出 `PaperAnalysis`：研究问题、方法、变量、统计、发现、声明、局限、未来方向等。

### CLI

```bash
# 需要设置 API key
export ANTHROPIC_API_KEY=sk-...

# 分析单篇
litmind-analyze parsed_paper.json -o analysis.json

# 指定 provider
litmind-analyze paper.json --provider openai --model gpt-4o

# 批量分析
litmind-analyze batch ./parsed/ -o ./analyses/
```

### Python API

```python
from litmind_analyzer import analyze_paper
from litmind_analyzer.providers import AnthropicProvider

provider = AnthropicProvider()
result = analyze_paper(paper_content, provider)
print(f"研究问题: {result.researchQuestion}")
print(f"发现: {len(result.mainFindings)} 条")
print(f"方法: {result.methods}")
```

### 环境变量

| 变量 | 用途 |
|---|---|
| `ANTHROPIC_API_KEY` | Claude provider |
| `OPENAI_API_KEY` | OpenAI provider |

---

## 安装

```bash
pip install litmind

# 按需安装依赖
pip install litmind[pdf]     # pymupdf (PDF 解析)
pip install litmind[llm]     # anthropic + openai (LLM 分析)
pip install litmind[all]     # 全部依赖
```

或从源码安装：

```bash
git clone https://github.com/<your>/litmind
cd litmind
pip install -e .
pip install -e ".[all]"
```

---

## 项目结构

```
litmind/
├── src/
│   ├── litmind_zotero/        # 模块一
│   ├── litmind_parser/        # 模块二
│   └── litmind_analyzer/      # 模块三
├── scripts/
│   ├── cli.py                 # Zotero 导出
│   ├── parse.py               # PDF 解析
│   └── analyze.py             # LLM 分析
├── tests/
├── .claude/skills/
│   ├── litmind-zotero/
│   ├── litmind-parser/
│   └── litmind-analyzer/
├── pyproject.toml
└── README.md
```
