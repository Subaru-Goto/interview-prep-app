import html

from app.config import settings
from app.cv_parser import looks_like_real_text


class InvalidInput(Exception):
    pass

def validate_inputs(cv_text: str, jd_text: str) -> str:
    """Validate the CV/JD pair at interview start. Returns the trimmed JD
    text. Raises InvalidInput if the CV doesn't look like usable text or the
    JD is outside the configured length bounds."""
    if not looks_like_real_text(cv_text):
        raise InvalidInput("No usable CV found — upload your CV first.")
    stripped_jd_text = jd_text.strip()
    if len(stripped_jd_text) < settings.min_jd_chars:
        raise InvalidInput(
            f"Job description is too short. "
            f"It must be at least {settings.min_jd_chars} characters."
        )
    if len(stripped_jd_text) > settings.max_jd_chars:
        raise InvalidInput(
            f"Job description is too long. "
            f"It must be at most {settings.max_jd_chars} characters."
        )
    return stripped_jd_text

# Security layer
def wrap_untrusted(label: str, text: str) -> str:
    """Escape the delimiter characters in untrusted text and wrap it in
    named <label>...</label> tags, so the model treats the content as data
    and it cannot forge or break out of the delimiters."""

    # quote=False escapes &, <, > but leaves quotes untouched
    escaped = html.escape(text, quote=False)
    return f"<{label}>{escaped}</{label}>"

def validate_answer(answer: str) -> str:
    """Validate a candidate's reply. Returns the trimmed answer. Raises
    InvalidInput if it's empty or exceeds max_answer_chars."""
    strip_answer = answer.strip()
    if len(strip_answer) == 0:
        raise InvalidInput("Answer cannot be empty")
    if len(strip_answer) > settings.max_answer_chars:
        raise InvalidInput(
            f"It must be at most {settings.max_answer_chars} characters."
        )
    return strip_answer