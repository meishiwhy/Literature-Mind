# LitMind

学术文献智能处理工具集。覆盖文献从元数据到结构化知识的全流程，帮助科研人员自动完成文献检索、PDF 解析、知识提取、证据检索、Discussion 生成和综述撰写。

## 模块总览

```
Zotero → Metadata → PDF → Full Text → Analysis → KB → Evidence → Discussion → Review
 (m1)      (m2)      (m3)         (m4/5)     (m6)      (m7)        (m8)
```

| 模块 | 名称 | 功能 |
|---|---|---|
| m1 | **litmind-zotero** | Zotero 连接器 — 导出文献元数据 |
| m2 | **litmind-parser** | PDF 解析 — 清洗噪声、识别章节结构 |
| m3 | **litmind-analyzer** | LLM 知识提取 — 研究问题/方法/变量/发现/声明 |
| m4 | **litmind-knowledge** | 知识库 — SQLite + ChromaDB 存储与检索 |
| m5 | **litmind-chat** | 科研问答 — 基于知识库的自然语言问答 |
| m6 | **litmind-evidence** | 证据检索 — 支持/反对/中性证据分类 |
| m7 | **litmind-discussion** | Discussion 生成 — 7 节结构化草稿 |
| m8 | **litmind-review** | 综述生成 — 主题聚类/共识/争议/空白+全文 |

---

## 快速开始

### 安装

```bash
pip install litmind

# 按需安装依赖
pip install litmind[pdf]     # PDF 解析 (pymupdf)
pip install litmind[llm]     # LLM 分析 (anthropic + openai)
pip install litmind[kb]      # 知识库 (sqlalchemy + chromadb)
pip install litmind[all]     # 全部依赖
```

### 环境变量

```bash
export ANTHROPIC_API_KEY=sk-...   # Claude provider (m3, m5, m6, m7, m8)
export OPENAI_API_KEY=sk-...      # OpenAI provider (可选)
```

---

## 模块详解

### m1: Zotero Connector (`/litmind-zotero`)

从 Zotero 本地 SQLite 数据库读取期刊论文元数据。

```bash
python scripts/cli.py export -o papers.json
python scripts/cli.py stats
```

```python
from litmind_zotero import discover_database, export_all
papers = export_all(discover_database())
```

**输出：** `PaperMetadata` — key, title, authors, year, doi, journal, pdfPath, tags, collections

---

### m2: Paper Parser (`/litmind-parser`)

从 PDF 提取全文 → 自动清洗（页眉/页脚/页码/重复）→ 识别标准章节。

```bash
python scripts/parse.py single paper.pdf -o parsed.json
python scripts/parse.py batch --from-zotero papers.json -o parsed/
```

```python
from litmind_parser import parse_pdf
result = parse_pdf("paper.pdf")
print(result.sections.abstract[:200])
```

**输出：** `PaperContent` — fullText + sections (abstract/intro/methods/results/discussion/conclusion)

---

### m3: Paper Analyzer (`/litmind-analyzer`)

将论文全文通过 LLM 提取为结构化科研知识。

```bash
litmind-analyze parsed.json -o analysis.json
litmind-analyze paper.json --provider openai --model gpt-4o
```

```python
from litmind_analyzer import analyze_paper
from litmind_analyzer.providers import AnthropicProvider

provider = AnthropicProvider()
result = analyze_paper(paper_content, provider)
print(f"研究问题: {result.researchQuestion}")
print(f"方法: {result.methods}")
```

**输出：** `PaperAnalysis` — researchQuestion, studyDesign, participants, methods, statistics, variables, claims, limitations, keywords

---

### m4: Knowledge Base (`/litmind-knowledge`)

基于 SQLite + ChromaDB 的本地科研知识库，存储论文分析结果，支持语义检索和结构化查询。

```bash
litmind-knowledge add analysis.json
litmind-knowledge search "flatfoot kinematics"
litmind-knowledge stats
```

```python
from litmind_knowledge.service import KnowledgeBase

kb = KnowledgeBase()
kb.add_paper(analysis_dict)
results = kb.semantic_search("MTP ROM flatfoot", top_k=10)
```

---

### m5: Research Chat (`/litmind-chat`)

面向知识库的自然语言问答。自动分类问题类型、检索相关证据、生成带引用的回答。

```bash
litmind-chat "What studies support the link between flatfoot and MTP ROM?"
litmind-chat "Show me papers using SPM analysis"
```

```python
from litmind_chat.service import ResearchChatService

chat = ResearchChatService(kb=kb, llm_provider=provider)
response = chat.ask("Does flatfoot increase forefoot motion?")
print(f"Answer: {response.answer}")
print(f"Sources: {len(response.supportingPapers)} papers")
```

---

### m6: Evidence Finder (`/litmind-evidence`)

输入一个科学观点，自动检索知识库中的支持证据、反对证据和中性证据，评估证据强度。

```bash
python scripts/evidence.py "Flatfoot increases MTP ROM"
python scripts/evidence.py "Carbon plate shoes improve jump performance" --json
```

```python
from litmind_evidence import EvidenceFinderService

ev_service = EvidenceFinderService(kb=kb, llm_provider=provider)
result = ev_service.find_evidence("SPM is more sensitive than peak-value analysis")
print(f"Strength: {result.evidenceStrength}")  # Strongly / Moderately / Weakly Supported
print(f"Support: {len(result.support)} papers")
print(f"Oppose: {len(result.oppose)} papers")
```

**证据强度分级：** Strongly Supported | Moderately Supported | Weakly Supported | Mixed Evidence | Insufficient Evidence

---

### m7: Discussion Generator (`/litmind-discussion`)

输入研究结果，自动检索相关文献，生成 7 节结构化 Discussion 草稿。

```bash
python scripts/discussion.py \
  --topic "Footwear stiffness effects on biomechanics" \
  --results "High stiffness shoes increased MTP ROM" \
  --results "No significant difference in ankle sagittal ROM"
```

```python
from litmind_discussion import DiscussionGeneratorService, DiscussionInput

service = DiscussionGeneratorService(evidence_service=ev_service, llm_provider=provider)
inp = DiscussionInput(studyTopic="Footwear stiffness", results=["...", "..."])
result = service.generate_discussion(inp)
print(result.discussionDraft)
```

**7 个 Section：**
1. Main Finding Interpretation
2. Supporting Evidence
3. Contradictory Evidence
4. Potential Mechanisms
5. Practical Implications
6. Study Limitations
7. Future Directions

---

### m8: Review Generator (`/litmind-review`)

输入一个研究主题，自动完成文献发现、主题聚类、趋势分析、共识与争议识别、研究空白发现，生成结构化综述全文。

```bash
python scripts/review.py "Flatfoot Biomechanics"
python scripts/review.py "SPM in Biomechanics" --json
```

```python
from litmind_review import ReviewGeneratorService, ReviewInput

service = ReviewGeneratorService(kb=kb, evidence_service=ev_service, llm_provider=provider)
inp = ReviewInput(topic="Flatfoot Biomechanics", max_papers=50)
result = service.generate_review(inp)

print(f"Themes: {len(result.researchThemes)}")
print(f"Consensus: {len(result.researchConsensus)}")
print(f"Controversies: {len(result.researchControversies)}")
print(f"Gaps: {len(result.researchGaps)}")
print(result.reviewDraft)
```

**核心功能：**
- **ThemeDiscoveryEngine** — LLM 自动聚类，提炼 3-7 个研究主题
- **TrendAnalyzer** — 统计高频变量、统计方法、研究设计、年份分布
- **ConsensusAnalyzer** — 识别多篇文献一致支持的结论
- **ControversyAnalyzer** — 发现支持和反对证据并存的争议点
- **GapAnalyzer** — 找出低频研究方向和空白领域
- **ReviewComposer** — 逐节生成 8 个 Section 的综述全文

**8 个 Section：**
1. Introduction
2. Current Research Landscape
3. Major Research Themes
4. Evidence Consensus
5. Research Controversies
6. Research Gaps
7. Future Directions
8. Conclusion

---

## 引用安全

所有模块的 LLM 生成内容均遵循严格的白名单引用机制：

- LLM 只能引用 Knowledge Base 中的真实 paperId
- 所有引用在后处理阶段校验，未通过的自动丢弃
- 禁止虚构作者、年份、DOI、期刊

---

## Claude Code Skill

在 Claude Code 中可直接调用以下命令：

```
/litmind-zotero      Zotero 连接器
/litmind-parser      PDF 解析
/litmind-analyzer    论文知识提取
/litmind-knowledge   知识库
/litmind-chat        科研问答
/litmind-evidence    证据检索
/litmind-discussion  Discussion 生成
/litmind-review      综述生成
```

---

## 项目结构

```
litmind/
├── src/
│   ├── litmind_zotero/         # m1
│   ├── litmind_parser/         # m2
│   ├── litmind_analyzer/       # m3
│   ├── litmind_knowledge/      # m4
│   ├── litmind_chat/           # m5
│   ├── litmind_evidence/       # m6
│   ├── litmind_discussion/     # m7
│   └── litmind_review/         # m8
├── scripts/
├── tests/
├── .claude/skills/
├── pyproject.toml
└── README.md
```

---

## License

MIT
