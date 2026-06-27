## Parent PRD

`docs/prd.md`

## What to build

End-to-end CV intake: the candidate uploads a PDF, the backend extracts text with `pypdf` (the deep **CV parser** module) and validates the upload (file type + size). The candidate is shown **only whether the upload succeeded or failed, and why** — the extracted text is **never displayed and is not editable**; it is used as-parsed and carried server-side for downstream use. CV input is **PDF-only — there is no copy-paste fallback** (the job description is the paste-only input, in issue 004). Includes the input-guard checks for file type and size. See PRD → Implementation Decisions (Security: input validation) and the CV-parser module sketch.

## Acceptance criteria

- [ ] Candidate can upload a PDF; non-PDF files and oversized files are rejected with a clear message before any parsing.
- [ ] A text-based PDF is parsed to text server-side; the candidate sees a clear **"upload succeeded"** confirmation (the extracted text is **not** shown).
- [ ] A PDF with no usable text (e.g. a scan, below a character threshold) is reported as a **failed upload with a clear reason** — the candidate is told to upload a different, text-based PDF (not to paste).
- [ ] The CV parser is a standalone function tested in isolation with small fixture PDFs (text-based → returns text; empty/garbage → flagged).
- [ ] The UI surfaces only upload **status** (success, or failure + reason), never the parsed contents.
- [ ] No OCR, no `.docx` handling, and no copy-paste CV fallback (out of scope per PRD).

## Design notes / known limitation

- The extracted text is **not shown or editable**. The `is_usable` character threshold catches *total* extraction failures (e.g. scans → ~0 chars), but a **partially garbled** parse (multi-column layouts, tables) can reach the interview unseen. Accepted tradeoff for a simpler intake UX; recorded as a README known-limitation.
- The raw parsed CV text is the source of truth downstream; how it is persisted into session state for the interview is issue 005's concern.

## Blocked by

- Blocked by `docs/issues/001-walking-skeleton-stub-llm.md`

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 19