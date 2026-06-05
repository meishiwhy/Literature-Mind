"""Anthropic Claude provider — uses structured output (tool use)"""

import os
from typing import Any

from ..models import PaperAnalysis
from ..provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """Claude structured output provider"""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError("pip install anthropic")
            api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def analyze(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        schema = PaperAnalysis.model_json_schema()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{
                "name": "output_paper_analysis",
                "description": "Output the structured paper analysis",
                "input_schema": schema,
            }],
            tool_choice={"type": "tool", "name": "output_paper_analysis"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "output_paper_analysis":
                return dict(block.input)

        raise ValueError("No structured output returned from Claude")
