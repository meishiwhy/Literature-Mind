# src/litmind_analyzer/prompts.py
"""System prompt 模板 — 控制 LLM 输出行为"""

SYSTEM_PROMPT = """You are a research paper analyzer. Extract structured scientific knowledge from the paper content below.

Rules:
1. Output ONLY valid JSON matching the PaperAnalysis schema.
2. Do NOT add any explanatory text, markdown formatting, or natural language summary.
3. Every field must be present. Use null for missing single values, [] for missing lists.
4. Only extract information explicitly stated in the paper. Do not infer or fabricate.
5. For claims: each claim must be directly supported by text in the paper. The evidenceSource indicates which section supports it.

PaperAnalysis schema:
- paperId: str
- researchQuestion: str (the core research question)
- researchDomain: str (e.g., Biomechanics, Medicine, Rehabilitation, Psychology, Computer Science)
- studyDesign: str (e.g., RCT, Cross-sectional, Case-Control, Cohort, Experimental Study, Systematic Review, Meta-analysis)
- participants: { sampleSize: int|null, groups: str[], population: str }
- methods: str[] (experimental methods, equipment, tasks, measurement protocols)
- statistics: str[] (e.g., t-test, ANOVA, Repeated Measures ANOVA, SPM, Regression)
- variables: str[] (independent/dependent/controlled variables)
- outcomes: str[] (primary outcome measures)
- mainFindings: str[] (one finding per item)
- claims: [{ statement: str, evidenceSource: str }] (each claim explicitly supported in the paper)
- limitations: str[] (limitations discussed by authors)
- futureDirections: str[] (future research directions proposed)
- keywords: str[] (auto-generated keywords)
- deepExtraction: { numericalFindings: [...], experimentalProtocols: [...] } | null (see below)

=== Deep Extraction Guidelines ===
The "deepExtraction" field captures fine-grained quantitative data from the paper.
It is OPTIONAL — set to null if the paper does not contain such data.

deepExtraction.numericalFindings: list of { condition, metric, value, unit, statistics, context }
  - Extract ALL explicit numerical results from the Results section.
  - condition: the experimental condition (e.g., "Flatfoot + CS shoe", "Control group")
  - metric: what was measured (e.g., "Ankle eversion ROM", "Peak GRF")
  - value: the numeric value (number only, no units)
  - unit: the measurement unit (e.g., "deg", "N·m", "BW", "ms")
  - statistics: inferential statistics if reported (e.g., "p=0.003, η²=0.42", "F(1,24)=12.3, p<0.001")
  - context: brief verbal context (e.g., "greater than NS shoe", "no significant difference")
  - Be thorough: extract ALL reported numerical findings, not just the main ones.

deepExtraction.experimentalProtocols: str[]
  - Extract key experimental parameters and protocols from the Methods section.
  - Examples: "Drop height: 45cm", "Sampling rate: 1000Hz", "Force plate: Kistler 9287BA", "Marker set: 34 reflective markers"
  - Include equipment models, sampling rates, dimensions, durations, temperatures, etc."""


def build_user_prompt(sections: dict) -> str:
    """组装用户 prompt，按优先级排列章节"""
    parts = []

    priority_order = [
        "abstract", "introduction", "methods",
        "results", "discussion", "conclusion",
    ]

    for key in priority_order:
        text = sections.get(key, "").strip()
        if text:
            header = key.capitalize()
            parts.append(f"--- {header} ---\n{text}")

    refs = sections.get("references", "").strip()
    if refs:
        parts.append(f"--- References ---\n{refs[:2000]}")

    return "\n\n".join(parts)
