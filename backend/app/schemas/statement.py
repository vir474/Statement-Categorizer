from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class StatementRead(BaseModel):
    id: int
    filename: str
    file_format: str
    account_name: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    parse_status: str
    parse_error: Optional[str]
    uploaded_at: datetime
    transaction_count: int = 0   # populated by query, not stored in DB

    model_config = {"from_attributes": True}


class StatementUpdate(BaseModel):
    account_name: Optional[str] = None
