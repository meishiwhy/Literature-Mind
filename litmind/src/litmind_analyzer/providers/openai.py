"""OpenAI provider — uses function calling / structured output"""

import json
import os
from typing import Any

from ..models import PaperAnalysis
from ..provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI structured output provider"""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("pip install openai")
            api_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def analyze(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        schema = PaperAnalysis.model_json_schema()

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "paper_analysis",
                    "schema": schema,
                },
            },
        )

        content = response.choices[0].message.content
        if content:
            return json.loads(content)

        raise ValueError("No structured output returned from OpenAI")
