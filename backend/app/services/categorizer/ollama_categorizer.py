"""
Ollama LLM categorizer — fully offline fallback.
Sends a structured prompt to a locally running Ollama daemon (default: llama3.2).
Used when LLM_BACKEND=ollama and the rule engine returns no match.
"""

import json
from typing import Optional

import httpx

from app.core.config import settings
from app.services.categorizer.base import AbstractCategorizer, CategorySuggestion


class OllamaCategorizer(AbstractCategorizer):
    def __init__(self) -> None:
        self._url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        self._model = settings.ollama_model

    async def categorize(
        self,
        description: str,
        merchant: Optional[str],
        available_categories: list[str],
    ) -> Optional[CategorySuggestion]:
        categories_str = ", ".join(available_categories)
        merchant_str = f"Merchant: {merchant}\n" if merchant else ""

        prompt = (
            f"You are a bank transaction categorizer.\n"
            f"Classify the following transaction into exactly one of these categories:\n"
            f"{categories_str}\n\n"
            f"{merchant_str}"
            f"Description: {description}\n\n"
            f'Respond with a JSON object only, no explanation. Example: {{"category": "Groceries"}}'
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._url,
                    json={"model": self._model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                data = response.json()
                raw = data.get("response", "").strip()

                # Extract JSON from response (model may add extra text)
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start == -1 or end == 0:
                    return None

                parsed = json.loads(raw[start:end])
                category = parsed.get("category", "").strip()

                # Only return suggestion if it matches one of the available categories
                if category in available_categories:
                    return CategorySuggestion(
                        category_name=category,
                        confidence=0.75,
                        source="ollama",
                    )
        except (httpx.HTTPError, json.JSONDecodeError, KeyError):
            # Ollama not running or returned bad JSON — fail silently
            pass

        return None
