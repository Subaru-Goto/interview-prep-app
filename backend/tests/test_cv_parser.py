# test_text_pdf_is_usable        → parse_cv(text_bytes)   → result.is_usable is True,  text non-empty
# test_no_text_pdf_is_flagged    → parse_cv(blank_bytes)  → result.is_usable is False
# test_garbage_bytes_raises      → parse_cv(b"not a pdf") → expects an exception
