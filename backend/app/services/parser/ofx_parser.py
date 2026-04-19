"""
OFX / QFX parser using ofxparse.
Most major US banks support OFX export from their "Download Transactions" feature.
This is the most reliable format — structured XML-like data, no column guessing needed.
"""

from decimal import Decimal
from pathlib import Path
from typing import Optional

import ofxparse

from app.services.parser.base import AbstractParser, ParseResult, ParsedTransaction


class OFXParser(AbstractParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".ofx", ".qfx")

    def parse(self, file_path: Path) -> ParseResult:
        with open(file_path, "rb") as f:
            ofx = ofxparse.OfxParser.parse(f)

        transactions = []
        for account in ofx.accounts:
            for txn in account.statement.transactions:
                transactions.append(ParsedTransaction(
                    date=txn.date.date() if hasattr(txn.date, "date") else txn.date,
                    description=str(txn.memo or txn.payee or "Unknown").strip(),
                    merchant=str(txn.payee or "").strip() or None,
                    # OFX uses signed amounts: negative = debit, positive = credit
                    # Flip sign so our convention is: positive = expense
                    amount=-Decimal(str(txn.amount)),
                    currency=getattr(account.statement, "currency", "USD"),
                    raw_text=f"{txn.id}|{txn.type}|{txn.memo}",
                ))

        period_start = min((t.date for t in transactions), default=None)
        period_end = max((t.date for t in transactions), default=None)

        account_hint: Optional[str] = None
        if ofx.accounts:
            acct = ofx.accounts[0]
            account_hint = getattr(acct, "account_id", None)

        return ParseResult(
            transactions=transactions,
            period_start=period_start,
            period_end=period_end,
            account_hint=account_hint,
        )
