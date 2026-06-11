---
name: litmind-discussion
description: LitMind Discussion Generator — 基于证据的 Discussion 草稿生成
---

# LitMind Discussion Generator

输入研究主题和结果，自动检索 Knowledge Base 中的文献证据，生成具有科学依据和可追溯引用的 Discussion 草稿。

## 工作流程

1. 解析用户输入的研究结果
2. Evidence Finder 检索支持/反对证据
3. DiscussionComposer 逐步生成 7 个 Section
4. CitationManager 确保所有论述可追溯

## 输出结构

| Section | 内容 |
|---|---|
| Main Finding Interpretation | 主要发现解读 |
| Supporting Evidence | 支持证据对比 |
| Contradictory Evidence | 矛盾证据讨论 |
| Potential Mechanisms | 潜在机制解释 |
| Practical Implications | 实践意义 |
| Study Limitations | 研究局限性 |
| Future Directions | 未来方向 |

## 调用方式

### Python API

```python
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_discussion import DiscussionGeneratorService, DiscussionInput
from litmind_analyzer.providers import AnthropicProvider

kb = KnowledgeBase()
provider = AnthropicProvider()
ev_service = EvidenceFinderService(kb=kb, llm_provider=provider)
service = DiscussionGeneratorService(evidence_service=ev_service, llm_provider=provider)

inp = DiscussionInput(studyTopic="Footwear stiffness", results=["High stiffness increased MTP ROM"])
result = service.generate_discussion(inp)

print(result.discussionDraft)
print("Citations:", len(result.citations))
```

```python
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_discussion import DiscussionGeneratorService, DiscussionInput
from litmind_analyzer.providers import AnthropicProvider

kb = KnowledgeBase()
provider = AnthropicProvider()
ev_service = EvidenceFinderService(kb=kb, llm_provider=provider)
service = DiscussionGeneratorService(evidence_service=ev_service, llm_provider=provider)

inp = DiscussionInput(studyTopic="Footwear stiffness", results=["High stiffness increased MTP ROM"])
result = service.generate_discussion(inp)

print(result.discussionDraft)
print(f"Citations: {len(result.citations)}")
```

## 引用安全

所有引用均来自 Knowledge Base，LLM 只能引用白名单内的 paperId。
