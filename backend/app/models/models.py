"""
All database models in one file — follows full-stack-fastapi-template pattern.

Python 3.13 + SQLModel note: field names cannot shadow their own type imports.
e.g. `date: date` fails because `date` (field) shadows `date` (type).
Fix: use `import datetime` and qualify as `datetime.date`.
"""

import datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    color: str = Field(default="#6366f1")
    icon: str = Field(default="tag")
    is_user_defined: bool = Field(default=False)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    rules: List["CategoryRule"] = Relationship(back_populates="category")


class CategoryRule(SQLModel, table=True):
    __tablename__ = "category_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="categories.id", index=True)
    pattern: str
    is_regex: bool = Field(default=False)
    priority: int = Field(default=100)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    category: Optional[Category] = Relationship(back_populates="rules")


class Statement(SQLModel, table=True):
    __tablename__ = "statements"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    storage_path: str
    file_format: str
    account_name: Optional[str] = Field(default=None)
    period_start: Optional[datetime.date] = Field(default=None)
    period_end: Optional[datetime.date] = Field(default=None)
    parse_status: str = Field(default="pending")
    parse_error: Optional[str] = Field(default=None)
    uploaded_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    statement_id: int = Field(foreign_key="statements.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", index=True)
    date: datetime.date = Field(index=True)
    description: str
    merchant: Optional[str] = Field(default=None)
    amount: Decimal = Field(decimal_places=2, max_digits=12)
    currency: str = Field(default="USD")
    categorization_source: str = Field(default="uncategorized")
    raw_text: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
