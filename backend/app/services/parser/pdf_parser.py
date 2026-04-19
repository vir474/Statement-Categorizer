"""
PDF statement parser using pdfplumber.

Handles two extraction strategies:
  1. Table-based — used when pdfplumber detects structured tables
  2. Line-by-line text — used for text-only PDFs (e.g. Chase statements)

Chase and similar banks use MM/DD dates (no year) and include negative amounts
with a leading minus sign (-850.01). Both are handled explicitly.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pdfplumber
from dateutil import parser as dateutil_parser

from app.services.parser.base import AbstractParser, ParseResult, ParsedTransaction

# Date patterns — from most to least specific.
# MM/DD (no year) intentionally last — we infer year from context.
_DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",              # ISO: 2024-01-15
    r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",        # MM/DD/YYYY or MM/DD/YY
    r"\b(\d{1,2}-\d{1,2}-\d{4})\b",          # MM-DD-YYYY
    r"\b(\w{3}\s+\d{1,2},?\s+\d{4})\b",      # Jan 15, 2024
    r"\b(\d{1,2}/\d{1,2})\b",                # MM/DD — no year (Chase, Amex, etc.)
]
_DATE_RE = re.compile("|".join(_DATE_PATTERNS), re.IGNORECASE)

# Matches a signed dollar amount, capturing the sign separately.
# Handles: 700.00  -850.01  $1,234.56  (1,234.56)
_AMOUNT_RE = re.compile(r"(-?\s*\$?[\d,]+\.\d{2}|\(\$?[\d,]+\.\d{2}\))")

# Section headers in Chase PDFs that should not be parsed as transactions
_SKIP_PATTERNS = re.compile(
    r"^(PAYMENT|PURCHASE|CASH ADVANCE|FEE|INTEREST|BALANCE TRANSFER|"
    r"DATE OF TRANS|MERCHANT NAME|ACCOUNT ACTIVITY|TOTAL|YOUR|MINIMUM|"
    r"YEAR.TO.DATE|ANNUAL|APR|BILLING|PAGE|CONTINUED)",
    re.IGNORECASE,
)

# Keywords that identify bank (checking/savings) statements vs credit card statements.
# Bank statements list deposits as positive and withdrawals as negative —
# opposite to credit card convention (where positive = charge/expense).
_BANK_STATEMENT_RE = re.compile(
    r"(beginning balance|deposits and additions|electronic withdrawals|"
    r"checks paid|ending balance|daily ledger balance|total deposits|"
    r"total withdrawals|checking account|savings account)",
    re.IGNORECASE,
)


def _clean_doubled(text: str) -> str:
    """
    Chase PDFs sometimes render text twice (doubled characters like "CChhaassee").
    Detect and collapse: if every other character is repeated, deduplicate.
    """
    if len(text) < 4:
        return text
    # Check if the first 8 chars follow a doubled pattern
    sample = text[:min(16, len(text))]
    if all(sample[i] == sample[i + 1] for i in range(0, min(len(sample) - 1, 8), 2)):
        return text[::2]
    return text


def _parse_amount(raw: str) -> Optional[Decimal]:
    """Convert an amount string to Decimal. Preserves sign. Returns None if unparseable."""
    raw = raw.strip()
    is_negative = raw.startswith("(") and raw.endswith(")")
    raw = raw.strip("()").replace(",", "").replace("$", "").replace(" ", "")
    try:
        val = Decimal(raw)
        return -abs(val) if is_negative else val
    except InvalidOperation:
        return None


def _parse_date(raw: str, year_hint: Optional[int] = None) -> Optional[date]:
    """Parse a date string. For MM/DD patterns, uses year_hint (or current year) as fallback."""
    raw = raw.strip()
    try:
        parsed = dateutil_parser.parse(raw, dayfirst=False)
        # dateutil defaults to current year for MM/DD — use year_hint if provided
        if year_hint and re.match(r"^\d{1,2}/\d{1,2}$", raw):
            parsed = parsed.replace(year=year_hint)
        return parsed.date()
    except Exception:
        return None


class PDFParser(AbstractParser):
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Path) -> ParseResult:
        transactions: list[ParsedTransaction] = []

        # Try to extract a year hint from the statement period (e.g. "11/05/25 - 12/04/25")
        # Prefer "Opening/Closing Date" or "Statement Period" lines over random dates
        year_hint: Optional[int] = None
        full_year_re = re.compile(r"\b\d{1,2}/\d{1,2}/(\d{2,4})\b")
        period_line_re = re.compile(
            r"(opening|closing|statement|period|cycle|billing).{0,30}(\d{1,2}/\d{1,2}/(\d{2,4}))",
            re.IGNORECASE,
        )

        with pdfplumber.open(file_path) as pdf:
            first_text = pdf.pages[0].extract_text() or ""
            # Detect bank (checking/savings) vs credit card statement
            is_bank_statement = bool(_BANK_STATEMENT_RE.search(first_text))

            # First try: look for a period/closing date line
            period_match = period_line_re.search(first_text)
            if period_match:
                y = int(period_match.group(3))
                year_hint = 2000 + y if y < 100 else y
            else:
                # Fallback: use the first full date found
                m = full_year_re.search(first_text)
                if m:
                    y = int(m.group(1))
                    year_hint = 2000 + y if y < 100 else y

            for page in pdf.pages:
                tables = page.extract_tables()
                if tables and any(len(t) > 3 and len(t[0]) > 2 for t in tables):
                    # Only use table extraction when tables have meaningful structure
                    for table in tables:
                        transactions.extend(self._parse_table(table, year_hint, is_bank_statement))
                else:
                    text = page.extract_text() or ""
                    transactions.extend(self._parse_text_lines(text, year_hint, is_bank_statement))

        period_start = min((t.date for t in transactions), default=None)
        period_end = max((t.date for t in transactions), default=None)

        return ParseResult(
            transactions=transactions,
            period_start=period_start,
            period_end=period_end,
        )

    def _parse_text_lines(
        self, text: str, year_hint: Optional[int] = None, is_bank_statement: bool = False
    ) -> list[ParsedTransaction]:
        """
        Parse transaction lines from plain text.
        Expects lines like: "11/06 MERCHANT NAME  700.00"
        Bank statements have two amounts per line: transaction amount + running balance.
        For bank statements: take amounts[0] (transaction), skip amounts[1] (balance).
        Sign convention: bank positive=deposit (income→negative in our app),
        bank negative=withdrawal (expense→positive in our app), so flip sign for bank statements.
        """
        results = []
        for line in text.splitlines():
            line = line.strip()
            if not line or len(line) < 8:
                continue

            # Skip section headers and non-transaction lines
            if _SKIP_PATTERNS.match(line):
                continue

            # Clean doubled characters (Chase header text artifact)
            clean = _clean_doubled(line)

            # Line must start with or contain a date
            date_match = _DATE_RE.match(clean)
            if not date_match:
                continue

            # Extract the matched date string (first non-None group)
            date_str = next(g for g in date_match.groups() if g is not None)
            txn_date = _parse_date(date_str, year_hint)
            if not txn_date:
                continue

            # Find all amounts on the line
            amount_matches = _AMOUNT_RE.findall(clean)
            if not amount_matches:
                continue

            if is_bank_statement:
                # Bank format: DATE DESCRIPTION AMOUNT [BALANCE]
                # First amount = transaction amount, last amount = running balance
                raw_amount = amount_matches[0]
            else:
                # Credit card format: DATE DESCRIPTION AMOUNT
                # Usually only one amount; take the last to be safe
                raw_amount = amount_matches[-1]

            amount = _parse_amount(raw_amount)
            if amount is None:
                continue

            if is_bank_statement:
                # Flip sign: bank positive=deposit→income (negative), bank negative=withdrawal→expense (positive)
                amount = -amount

            # Everything between the date and amount is the description
            after_date = clean[date_match.end():].strip()
            # Remove all amounts from the description
            desc = _AMOUNT_RE.sub("", after_date).strip(" -|,.")
            if not desc:
                desc = "Unknown"

            results.append(ParsedTransaction(
                date=txn_date,
                description=desc,
                amount=amount,
                raw_text=line,
            ))

        return results

    def _parse_table(
        self, table: list[list], year_hint: Optional[int] = None, is_bank_statement: bool = False
    ) -> list[ParsedTransaction]:
        """Extract transactions from a pdfplumber-detected table."""
        results = []
        # Skip header row if first row contains no date
        rows = table
        if rows and not _DATE_RE.search(" ".join(str(c) for c in rows[0] if c)):
            rows = rows[1:]

        for row in rows:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            cells = [str(c).strip() if c else "" for c in row]
            txn = self._cells_to_transaction(cells, year_hint, is_bank_statement)
            if txn:
                results.append(txn)
        return results

    def _cells_to_transaction(
        self, cells: list[str], year_hint: Optional[int] = None, is_bank_statement: bool = False
    ) -> Optional[ParsedTransaction]:
        txn_date = None
        amount = None
        desc_parts = []

        for cell in cells:
            if not cell:
                continue
            if txn_date is None:
                m = _DATE_RE.search(cell)
                if m:
                    date_str = next(g for g in m.groups() if g is not None)
                    txn_date = _parse_date(date_str, year_hint)
                    if txn_date:
                        continue
            amt_matches = _AMOUNT_RE.findall(cell)
            if amt_matches and amount is None:
                amount = _parse_amount(amt_matches[-1])
                if amount is not None:
                    continue
            desc_parts.append(cell)

        if txn_date is None or amount is None:
            return None

        if is_bank_statement:
            amount = -amount

        return ParsedTransaction(
            date=txn_date,
            description=" ".join(desc_parts).strip() or "Unknown",
            amount=amount,
            raw_text=" | ".join(cells),
        )
