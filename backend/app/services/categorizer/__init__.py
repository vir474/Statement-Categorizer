"""
Categorization pipeline — runs rule engine first, falls back to LLM if no match.
The LLM backend is selected by LLM_BACKEND env var (ollama | claude | none).
"""

from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.services.categorizer.base import AbstractCategorizer, CategorySuggestion
from app.services.categorizer.rule_engine import load_rule_engine


def _get_llm_categorizer() -> Optional[AbstractCategorizer]:
    """Return LLM categorizer instance based on config, or None if disabled."""
    if settings.llm_backend == "ollama":
        from app.services.categorizer.ollama_categorizer import OllamaCategorizer
        return OllamaCategorizer()
    if settings.llm_backend == "claude":
        from app.services.categorizer.claude_categorizer import ClaudeCategorizer
        return ClaudeCategorizer()
    return None  # LLM_BACKEND=none


async def categorize_transaction(
    description: str,
    merchant: Optional[str],
    available_categories: list[str],
    session: AsyncSession,
) -> Optional[CategorySuggestion]:
    """
    Full categorization pipeline:
    1. Run rule engine (fast, offline, deterministic)
    2. If no match, fall back to configured LLM
    3. Return None if nothing matched (stays "uncategorized")
    """
    rule_engine = await load_rule_engine(session)
    result = await rule_engine.categorize(description, merchant, available_categories)
    if result:
        return result

    llm = _get_llm_categorizer()
    if llm:
        return await llm.categorize(description, merchant, available_categories)

    return None
