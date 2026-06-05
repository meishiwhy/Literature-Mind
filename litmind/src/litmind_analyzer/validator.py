"""Schema validation + field completeness guarantee"""

from .models import PaperAnalysis


FIELD_DEFAULTS = {
    "paperId": "",
    "researchQuestion": "",
    "researchDomain": "",
    "studyDesign": "",
    "participants": {"sampleSize": None, "groups": [], "population": ""},
    "methods": [],
    "statistics": [],
    "variables": [],
    "outcomes": [],
    "mainFindings": [],
    "claims": [],
    "limitations": [],
    "futureDirections": [],
    "keywords": [],
}


def ensure_fields(data: dict) -> dict:
    """Recursively fill missing fields, guaranteeing all keys exist."""
    for field, default in FIELD_DEFAULTS.items():
        if field not in data or data[field] is None:
            if isinstance(default, dict):
                data[field] = dict(default)
            elif isinstance(default, list):
                data[field] = list(default)
            else:
                data[field] = default
        elif isinstance(default, dict) and isinstance(data[field], dict):
            for k, v in default.items():
                if k not in data[field] or data[field][k] is None:
                    data[field][k] = v
    return data


def validate_and_repair(raw: dict) -> PaperAnalysis:
    """Validate raw LLM output, fill missing fields, return PaperAnalysis."""
    repaired = ensure_fields(raw)
    return PaperAnalysis(**repaired)
