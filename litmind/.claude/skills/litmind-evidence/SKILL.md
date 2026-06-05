---
name: litmind-evidence
description: LitMind Evidence Finder — 科研证据检索与归纳系统
---

# LitMind Evidence Finder

输入一个科学观点，系统自动在 Knowledge Base 中寻找支持证据、反对证据和中性证据，并生成证据总结。

## 工作流程

1. 用户输入研究观点
2. ClaimRetriever 多路检索（语义 + LIKE）
3. ClaimClassifier 判断关系（support/oppose/neutral）
4. Evaluator 评估证据强度
5. 输出结构化证据汇总

## 调用方式

```bash
# CLI
python scripts/evidence.py "Flatfoot increases MTP ROM"

# JSON 输出
python scripts/evidence.py "query" --json

# 不使用 LLM 分类
python scripts/evidence.py "query" --no-llm
```

## Python API

```python
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_analyzer.providers import AnthropicProvider

kb = KnowledgeBase()
provider = AnthropicProvider()
service = EvidenceFinderService(kb=kb, llm_provider=provider)

result = service.find_evidence("Flatfoot increases MTP ROM")
print(f"Strength: {result.evidenceStrength}")
print(f"Support: {len(result.support)} papers")
print(f"Oppose: {len(result.oppose)} papers")
```

## 输出字段

| 字段 | 说明 |
|---|---|
| evidenceStrength | Strongly/Moderately/Weakly Supported, Mixed/Insufficient Evidence |
| confidence | 置信度 0.0-1.0 |
| support | 支持证据列表 |
| oppose | 反对证据列表 |
| neutral | 中性证据列表 |
