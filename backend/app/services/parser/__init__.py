"""
Parser registry — tries each parser in order, returns the first that can handle the file.
Add new parsers here to extend format support without changing any other code.
"""

from pathlib import Path

from app.services.parser.base import AbstractParser, ParseResult
from app.services.parser.csv_parser import CSVParser
from app.services.parser.ofx_parser import OFXParser
from app.services.parser.pdf_parser import PDFParser

_PARSERS: list[AbstractParser] = [
    OFXParser(),   # Most reliable — try first
    CSVParser(),
    PDFParser(),   # Least reliable — try last
]


def parse_statement(file_path: Path) -> ParseResult:
    """
    Find the right parser for a file and return parsed transactions.
    Raises ValueError if no parser recognises the file format.
    """
    for parser in _PARSERS:
        if parser.can_parse(file_path):
            return parser.parse(file_path)
    raise ValueError(f"No parser available for file: {file_path.name}")
