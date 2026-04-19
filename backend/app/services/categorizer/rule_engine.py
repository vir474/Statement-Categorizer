"""
Rule-based categorizer — Firefly III-style rules engine.

Rules are stored in the DB (CategoryRule table) and evaluated in priority order.
Each rule is either a plain keyword substring match or a full regex pattern.
This runs first, before any LLM call, and is the only categorizer used in offline mode.

Also ships a set of sensible default rules seeded on first startup.
"""

import re
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.category import Category, CategoryRule
from app.services.categorizer.base import AbstractCategorizer, CategorySuggestion

# Default seed rules — (pattern, is_regex, category_name, priority)
# These cover the most common transaction descriptions across US banks
DEFAULT_RULES: list[tuple[str, bool, str, int]] = [
    # Food & Drink
    ("GROCERY|SAFEWAY|KROGER|WHOLE FOODS|TRADER JOE|PUBLIX|ALDI|WEGMANS|HEB|SPROUTS", True, "Groceries", 10),
    ("RESTAURANT|DOORDASH|UBER EATS|GRUBHUB|SEAMLESS|POSTMATES|INSTACART", True, "Dining & Delivery", 10),
    ("STARBUCKS|DUNKIN|COFFEE|CAFE|PANERA|CHIPOTLE|MCDONALD|SUBWAY|PIZZA|TACO BELL|WENDY|BURGER", True, "Restaurants & Cafes", 10),
    # Transportation
    ("UBER|LYFT|TAXI|LIME|BIRD|METRO|TRANSIT|PARKING|TOLL|EZ.?PASS", True, "Rideshare & Transit", 20),
    ("GAS|GASOLINE|SHELL|EXXON|BP|CHEVRON|SUNOCO|MARATHON|SPEEDWAY|CIRCLE K|WAWA", True, "Gas", 20),
    # Shopping
    ("AMAZON|AMZN", True, "Amazon", 30),
    ("WALMART|TARGET|COSTCO|SAM.?S CLUB|BJ.?S", True, "Big Box Retail", 30),
    ("APPLE|BEST BUY|NEWEGG|B&H|MICRO CENTER", True, "Electronics", 30),
    # Utilities & Bills
    ("ELECTRIC|GAS COMPANY|WATER|SEWAGE|UTILITY|PG&E|CON ED|DUKE ENERGY|NATIONAL GRID", True, "Utilities", 40),
    ("INTERNET|CABLE|AT&T|VERIZON|T-MOBILE|SPRINT|COMCAST|XFINITY|SPECTRUM", True, "Phone & Internet", 40),
    ("NETFLIX|SPOTIFY|HULU|DISNEY|HBO|AMAZON PRIME|APPLE TV|YOUTUBE", True, "Subscriptions", 40),
    # Health
    ("PHARMACY|CVS|WALGREENS|RITE AID|DOCTOR|HOSPITAL|MEDICAL|DENTAL|VISION|HEALTH", True, "Healthcare", 50),
    ("GYM|FITNESS|PLANET FITNESS|EQUINOX|PELOTON|CROSSFIT|YMCA", True, "Fitness", 50),
    # Finance
    ("TRANSFER|ZELLE|VENMO|PAYPAL|CASH APP|WIRE", True, "Transfers", 60),
    ("PAYMENT|AUTOPAY|MINIMUM PAYMENT", True, "Payments", 60),
    ("ATM|CASH WITHDRAWAL", True, "Cash & ATM", 60),
    # Travel
    ("HOTEL|MARRIOTT|HILTON|HYATT|AIRBNB|VRBO|BOOKING|EXPEDIA", True, "Hotels", 70),
    ("AIRLINE|DELTA|UNITED|AMERICAN|SOUTHWEST|JETBLUE|SPIRIT|FRONTIER|FLIGHT", True, "Flights", 70),
    # Income / Credits
    ("PAYROLL|SALARY|DIRECT DEPOSIT|EMPLOYER", True, "Income", 5),
    ("REFUND|RETURN|CASHBACK|CASH BACK|REWARD", True, "Refunds & Rewards", 5),
]


class RuleEngine(AbstractCategorizer):
    def __init__(self, rules: list[CategoryRule], categories: dict[int, str]) -> None:
        # Pre-compile all regex patterns at construction time for performance
        self._compiled: list[tuple[re.Pattern, int, str]] = []
        for rule in sorted(rules, key=lambda r: r.priority):
            flags = re.IGNORECASE
            try:
                if rule.is_regex:
                    pattern = re.compile(rule.pattern, flags)
                else:
                    # Plain keyword — escape and wrap in word boundary
                    pattern = re.compile(re.escape(rule.pattern), flags)
                cat_name = categories.get(rule.category_id, "")
                if cat_name:
                    self._compiled.append((pattern, rule.category_id, cat_name))
            except re.error:
                pass  # Skip malformed regex patterns gracefully

    async def categorize(
        self,
        description: str,
        merchant: Optional[str],
        available_categories: list[str],
    ) -> Optional[CategorySuggestion]:
        text = f"{merchant or ''} {description}".strip()
        for pattern, _cat_id, cat_name in self._compiled:
            if pattern.search(text):
                return CategorySuggestion(
                    category_name=cat_name,
                    confidence=1.0,
                    source="rule",
                )
        return None


async def load_rule_engine(session: AsyncSession) -> RuleEngine:
    """Load all active rules and categories from DB and return a RuleEngine instance."""
    rules = (await session.exec(select(CategoryRule))).all()
    categories_result = (await session.exec(select(Category))).all()
    cat_map = {c.id: c.name for c in categories_result if c.id is not None}
    return RuleEngine(list(rules), cat_map)
