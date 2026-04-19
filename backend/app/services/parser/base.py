"""
Abstract parser interface — each file format (PDF, CSV, OFX) implements this.
Returns a list of raw transaction dicts ready to be inserted into the DB.
Following felgru/bank-statement-parser's modular plugin pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional


@dataclass
class ParsedTransaction:
    """Normalized transaction row returned by every parser."""
    date: date
    description: str
    amount: Decimal         # positive = debit/expense, negative = credit/refund
    currency: str = "USD"
    merchant: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class ParseResult:
    transactions: list[ParsedTransaction]
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    account_hint: Optional[str] = None   # account name/number if found in file


class AbstractParser(ABC):
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Return True if this parser can handle the given file."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """Parse the file and return structured transactions."""
