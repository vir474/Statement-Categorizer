from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CategorySpend(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    parent_category_name: Optional[str] = None
    total: Decimal
    transaction_count: int


class BudgetSummary(BaseModel):
    """Monthly spending summary returned by GET /budgets/summary."""
    month: str
    total_spend: Decimal
    total_income: Decimal
    net: Decimal
    by_category: list[CategorySpend]
