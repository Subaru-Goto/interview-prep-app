from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def _upload(filename: str, content: bytes, content_type: str):
    """POST a fake file to /upload-cv. The 3-tuple is (name, bytes, MIME type)."""
    return client.post("/upload-cv", files={"file": (filename, content, content_type)})


def test_text_pdf_upload_succeeds():
    content = (FIXTURES / "sample_cv.pdf").read_bytes()
    res = _upload("cv.pdf", content, "application/pdf")
    assert res.status_code == 200
    assert res.json()["is_usable"] is True


def test_scanned_pdf_upload_is_not_usable():
    # Valid PDF, no text -> 200 (NOT an error) but is_usable False.
    content = (FIXTURES / "scanned_cv.pdf").read_bytes()
    res = _upload("scan.pdf", content, "application/pdf")
    assert res.status_code == 200
    assert res.json()["is_usable"] is False


def test_non_pdf_is_rejected_400():
    res = _upload("resume.txt", b"hello, I am not a pdf", "text/plain")
    assert res.status_code == 400


def test_oversized_file_is_rejected_413(monkeypatch):
    monkeypatch.setattr(settings, "max_cv_bytes", 10)
    res = _upload("big.pdf", b"%PDF-1.4 plenty of bytes here", "application/pdf")
    assert res.status_code == 413


def test_unreadable_pdf_returns_422():
    res = _upload("fake.pdf", b"this is not really a pdf", "application/pdf")
    assert res.status_code == 422
