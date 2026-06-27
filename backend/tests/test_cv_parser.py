from pathlib import Path

import pytest
from pypdf.errors import PdfReadError
from app.cv_parser import parse_cv, looks_like_real_text

from app.config import settings

FIXTURES = Path(__file__).parent / "fixtures"

def test_text_pdf_is_usable():
    pdf_bytes = (FIXTURES / "sample_cv.pdf").read_bytes()
    result = parse_cv(pdf_bytes)
    assert result.is_usable is True
    assert "Jordan A. Mercer" in result.text

def test_multipage_pdf_extracts_all_pages():
    pdf_bytes = (FIXTURES / "multipage_cv.pdf").read_bytes()
    result = parse_cv(pdf_bytes)
    assert result.is_usable is True
    assert "Dr. Alex P. Rivera" in result.text  
    assert "Awards" in result.text

def test_blank_pdf_is_flagged():
    pdf_bytes = (FIXTURES / "blank_cv.pdf").read_bytes()
    result = parse_cv(pdf_bytes)
    assert result.is_usable is False


def test_scanned_pdf_is_flagged():
    pdf_bytes = (FIXTURES / "scanned_cv.pdf").read_bytes()
    result = parse_cv(pdf_bytes)
    assert result.is_usable is False

def test_garbage_bytes_raises():
    with pytest.raises(PdfReadError):
        parse_cv(b"this is not a pdf")


def test_encrypted_pdf_raises():
    pdf_bytes = (FIXTURES / "protected_cv.pdf").read_bytes()
    with pytest.raises(PdfReadError):
        parse_cv(pdf_bytes)

def test_usability_threshold_flips_with_min_chars(monkeypatch):
    monkeypatch.setattr(settings, "min_cv_chars", 100_000)
    result = parse_cv((FIXTURES / "sample_cv.pdf").read_bytes())
    assert result.is_usable is False


def test_long_text_is_truncated_to_max_chars(monkeypatch):
    monkeypatch.setattr(settings, "max_cv_chars", 200)
    result = parse_cv((FIXTURES / "sample_cv.pdf").read_bytes())
    assert result.is_usable is True
    assert len(result.text) == 200

def test_real_text_passes():
    assert looks_like_real_text("I am a senior software engineer " * 5) is True

def test_no_space_garble_is_rejected():
    assert looks_like_real_text("JordanMercerSeniorEngineer" * 10) is False

def test_symbol_garble_is_rejected():
    assert looks_like_real_text("!@#$%^&*()_+{}|<>?" * 20) is False

def test_too_short_is_rejected():
    assert looks_like_real_text("hi there") is False
