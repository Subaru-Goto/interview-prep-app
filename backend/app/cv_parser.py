from pydantic import BaseModel
from pypdf import PdfReader
from app.config import settings
from io import BytesIO


class CVParseResult(BaseModel):
    text: str
    is_usable: bool


def looks_like_real_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < settings.min_cv_chars:
        return False
    whitespace_ratio = sum(c.isspace() for c in text) / len(text)
    alpha_ratio = sum(c.isalpha() for c in text) / len(text)
    return (
        whitespace_ratio >= settings.min_whitespace_ratio
        and alpha_ratio >= settings.min_alpha_ratio
    )


def parse_cv(data: bytes) -> CVParseResult:
    reader = PdfReader(BytesIO(data))
    full_text = "\n".join([t for page in reader.pages if (t := page.extract_text())])
    full_text = full_text[: settings.max_cv_chars]
    return CVParseResult(text=full_text, is_usable=looks_like_real_text(full_text))
