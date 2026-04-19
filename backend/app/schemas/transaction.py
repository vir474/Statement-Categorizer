from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TransactionRead(BaseModel):
    id: int
    statement_id: int
    date: date
    description: str
    merchant: Optional[str] = None
    amount: Decimal
    currency: str
    category_id: Optional[int] = None
    categorization_source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    """Used when user manually changes a category or merchant name."""
    category_id: Optional[int] = None
    merchant: Optional[str] = None


class TransactionBulkCategorize(BaseModel):
    transaction_ids: list[int]
