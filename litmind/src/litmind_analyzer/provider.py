"""LLM Provider 抽象基类 — 各平台实现此接口"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """LLM 提供者抽象接口

    每个子类实现 analyze() 方法，返回符合 PaperAnalysis schema 的 dict。
    """

    def __init__(self, api_key: str | None = None, model: str = ""):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def analyze(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """分析论文，返回可转为 PaperAnalysis 的 dict

        Args:
            system_prompt: 系统指令（角色 + 输出约束）
            user_prompt: 论文全文 + 章节文本

        Returns:
            符合 PaperAnalysis schema 的 dict
        """
        ...
