"""Abstract categorizer interface — all backends (rule, Ollama, Claude) satisfy this."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CategorySuggestion:
    category_name: str          # matched or suggested category name
    confidence: float           # 0.0 – 1.0
    source: str                 # "rule" | "ollama" | "claude"


class AbstractCategorizer(ABC):
    @abstractmethod
    async def categorize(
        self,
        description: str,
        merchant: Optional[str],
        available_categories: list[str],
    ) -> Optional[CategorySuggestion]:
        """
        Suggest a category for a transaction.
        Returns None if the categorizer has no suggestion.
        """
