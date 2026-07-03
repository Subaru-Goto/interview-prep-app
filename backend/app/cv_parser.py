from io import BytesIO

from pydantic import BaseModel
from pypdf import PdfReader

from app.config import settings


class CVParseResult(BaseModel):
    text: str
    is_usable: bool


def looks_like_real_text(text: str) -> bool:
    """Heuristic quality gate for extracted CV text: rejects text that's too
    short or whose whitespace/alphabetic ratios suggest a garbled or scanned
    (non-text-layer) PDF rather than real prose."""
    stripped = text.strip()
    if len(stripped) < settings.min_cv_chars:
        return False
    whitespace_count = sum(c.isspace() for c in text)
    non_space = len(text) - whitespace_count
    whitespace_ratio = whitespace_count / len(text)
    alpha_ratio = sum(c.isalpha() for c in text) / non_space if non_space else 0.0

    return (
        whitespace_ratio >= settings.min_whitespace_ratio
        and alpha_ratio >= settings.min_alpha_ratio
    )


def parse_cv(data: bytes) -> CVParseResult:
    """Extract text from a PDF's text layer (truncated to max_cv_chars) and
    flag whether it looks usable. Does not raise on a garbled/scanned PDF —
    that's reflected in is_usable, not an exception; a genuinely unreadable
    PDF raises pypdf's own PdfReadError."""
    reader = PdfReader(BytesIO(data))
    full_text = "\n".join([t for page in reader.pages if (t := page.extract_text())])
    full_text = full_text[: settings.max_cv_chars]
    return CVParseResult(text=full_text, is_usable=looks_like_real_text(full_text))
