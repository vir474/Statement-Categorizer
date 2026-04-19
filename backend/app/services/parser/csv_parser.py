"""
CSV statement parser using pandas.
Auto-detects column layout by looking for date, description, and amount columns.
Handles common bank CSV exports (Chase, Bank of America, Capital One, etc.).
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.services.parser.base import AbstractParser, ParseResult, ParsedTransaction

# Column name patterns to search for (case-insensitive)
_DATE_COLS = ["date", "transaction date", "posted date", "trans date", "posting date"]
_DESC_COLS = ["description", "memo", "transaction description", "details", "payee", "name"]
_AMOUNT_COLS = ["amount", "transaction amount", "debit", "credit", "charge"]
_DEBIT_COLS = ["debit", "withdrawals", "debit amount"]
_CREDIT_COLS = ["credit", "deposits", "credit amount", "payment"]


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first DataFrame column that matches any candidate name."""
    lower_map = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


class CSVParser(AbstractParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".csv", ".tsv")

    def parse(self, file_path: Path) -> ParseResult:
        # Try comma first, then tab
        for sep in (",", "\t"):
            try:
                df = pd.read_csv(file_path, sep=sep, dtype=str, skip_blank_lines=True)
                if len(df.columns) >= 3:
                    break
            except Exception:
                continue
        else:
            return ParseResult(transactions=[])

        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")

        transactions = self._extract_transactions(df)

        period_start = min((t.date for t in transactions), default=None)
        period_end = max((t.date for t in transactions), default=None)

        return ParseResult(
            transactions=transactions,
            period_start=period_start,
            period_end=period_end,
        )

    def _extract_transactions(self, df: pd.DataFrame) -> list[ParsedTransaction]:
        date_col = _find_col(df, _DATE_COLS)
        desc_col = _find_col(df, _DESC_COLS)
        amount_col = _find_col(df, _AMOUNT_COLS)
        debit_col = _find_col(df, _DEBIT_COLS)
        credit_col = _find_col(df, _CREDIT_COLS)

        if not date_col or not desc_col:
            return []
        # Need either a combined amount column or separate debit/credit columns
        if not amount_col and not (debit_col or credit_col):
            return []

        results = []
        for _, row in df.iterrows():
            txn_date = self._to_date(str(row.get(date_col, "")))
            if not txn_date:
                continue

            description = str(row.get(desc_col, "")).strip()
            if not description:
                continue

            amount = self._resolve_amount(row, amount_col, debit_col, credit_col)
            if amount is None:
                continue

            results.append(ParsedTransaction(
                date=txn_date,
                description=description,
                amount=amount,
                raw_text=",".join(str(v) for v in row.values),
            ))
        return results

    def _to_date(self, raw: str) -> Optional[date]:
        if not raw or raw.lower() in ("nan", "none", ""):
            return None
        try:
            return pd.to_datetime(raw, dayfirst=False).date()
        except Exception:
            return None

    def _resolve_amount(
        self,
        row: pd.Series,
        amount_col: Optional[str],
        debit_col: Optional[str],
        credit_col: Optional[str],
    ) -> Optional[Decimal]:
        """
        Normalize to: positive = expense/debit, negative = income/credit.
        Handles both combined and split debit/credit column layouts.
        """
        def clean(val: str) -> Optional[Decimal]:
            val = str(val).strip().replace(",", "").replace("$", "").replace("(", "-").replace(")", "")
            try:
                return Decimal(val)
            except Exception:
                return None

        if amount_col:
            return clean(str(row.get(amount_col, "")))

        debit = clean(str(row.get(debit_col, ""))) if debit_col else None
        credit = clean(str(row.get(credit_col, ""))) if credit_col else None

        if debit and debit != Decimal(0):
            return debit          # debit = expense = positive
        if credit and credit != Decimal(0):
            return -abs(credit)   # credit = income = negative
        return None
