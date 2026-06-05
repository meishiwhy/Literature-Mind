---
name: litmind-review
description: LitMind Review Generator — 基于科研知识库的综述生成系统
---

# LitMind Review Generator

输入研究主题，自动检索知识库相关文献，分析研究趋势、主题聚类、共识与争议，生成结构化综述框架和带引用的综述草稿。

## 工作流程

1. 检索 KB 获取相关论文
2. ThemeDiscoveryEngine 聚类主题
3. TrendAnalyzer 统计高频变量/方法/设计
4. ConsensusAnalyzer 识别研究共识
5. ControversyAnalyzer 识别研究争议
6. GapAnalyzer 发现研究空白
7. OutlineGenerator 生成综述框架
8. ReviewComposer 生成综述全文

## 输出结构

- researchThemes — 研究主题聚类
- researchConsensus — 研究共识
- researchControversies — 研究争议
- researchGaps — 研究空白
- reviewOutline — 综述框架
- reviewDraft — 综述全文

## 调用方式

```bash
python scripts/review.py "Flatfoot Biomechanics"
python scripts/review.py "MTP Joint Function" --max-papers 30
python scripts/review.py "SPM in Biomechanics" --json
```

## Python API

```python
from litmind_knowledge.service import KnowledgeBase
from litmind_evidence import EvidenceFinderService
from litmind_review import ReviewGeneratorService, ReviewInput
from litmind_analyzer.providers import AnthropicProvider

kb = KnowledgeBase()
provider = AnthropicProvider()
ev = EvidenceFinderService(kb=kb, llm_provider=provider)
service = ReviewGeneratorService(kb=kb, evidence_service=ev, llm_provider=provider)

result = service.generate_review(ReviewInput(topic="Flatfoot Biomechanics"))
print(f"Themes: {len(result.researchThemes)}")
print(f"Draft: {len(result.reviewDraft)} chars")
```
