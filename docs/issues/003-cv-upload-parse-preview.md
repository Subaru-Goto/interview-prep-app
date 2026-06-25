## Parent PRD

`docs/prd.md`

## What to build

End-to-end CV intake: the candidate uploads a PDF, the backend extracts text with `pypdf` (the deep **CV parser** module), the extracted text is returned and shown in an **editable** field for the candidate to correct, and unusable extractions are detected and reported. Includes the input-guard checks for file type and size. See PRD → Implementation Decisions (Security: input validation) and the CV-parser module sketch.

## Acceptance criteria

- [ ] Candidate can upload a PDF; non-PDF files and oversized files are rejected with a clear message before any parsing.
- [ ] A text-based PDF is parsed to text and displayed back in an editable text area.
- [ ] The candidate's edits to the extracted text are what get used downstream (not the raw parse).
- [ ] A PDF with no usable text (e.g. a scan) is detected (below a character threshold) and the candidate is told to paste their CV manually instead.
- [ ] The CV parser is a standalone function tested in isolation with small fixture PDFs (text-based → returns text; empty/garbage → flagged).
- [ ] No OCR and no `.docx` handling (out of scope per PRD).

## Blocked by

- Blocked by `docs/issues/001-walking-skeleton-stub-llm.md`

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 19
