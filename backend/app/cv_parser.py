from pydantic import BaseModel
from pypdf import PdfReader
from app.config import settings
from io import BytesIO


class CVParseResult(BaseModel):
    text: str
    is_usable: bool


def parse_cv(data: bytes) -> CVParseResult:
    # Convert bytes to file-like object
    reader = PdfReader(BytesIO(data))
    full_text = "\n".join([t for page in reader.pages if (t := page.extract_text())])
    if len(full_text.strip()) < settings.min_cv_chars:
        return CVParseResult(text=full_text, is_usable=False)
    if len(full_text.strip()) > settings.max_cv_chars:
        # truncate to max_cv_chars
        full_text = full_text[: settings.max_cv_chars]

    return CVParseResult(text=full_text, is_usable=True)
