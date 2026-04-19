"""
Claude API categorizer — online fallback (LLM_BACKEND=claude).
Uses prompt caching on the system prompt to reduce cost when categorizing many transactions.
Requires ANTHROPIC_API_KEY env var.
"""

import json
from typing import Optional

import anthropic

from app.core.config import settings
from app.services.categorizer.base import AbstractCategorizer, CategorySuggestion

_SYSTEM_PROMPT = (
    "You are a bank transaction categorizer. "
    "You will receive a transaction description and a list of available categories. "
    "Respond with a JSON object only: {\"category\": \"<name>\"} — no explanation, no markdown."
)


class ClaudeCategorizer(AbstractCategorizer):
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def categorize(
        self,
        description: str,
        merchant: Optional[str],
        available_categories: list[str],
    ) -> Optional[CategorySuggestion]:
        categories_str = ", ".join(available_categories)
        merchant_str = f"Merchant: {merchant}\n" if merchant else ""
        user_content = (
            f"Available categories: {categories_str}\n\n"
            f"{merchant_str}"
            f"Transaction description: {description}"
        )

        try:
            message = await self._client.messages.create(
                model="claude-haiku-4-5-20251001",  # Fast and cheap for single-field classification
                max_tokens=64,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        # Cache the system prompt — it's the same for every transaction
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
            )
            raw = message.content[0].text.strip()
            parsed = json.loads(raw)
            category = parsed.get("category", "").strip()

            if category in available_categories:
                return CategorySuggestion(
                    category_name=category,
                    confidence=0.9,
                    source="claude",
                )
        except (anthropic.APIError, json.JSONDecodeError, IndexError):
            pass

        return None
