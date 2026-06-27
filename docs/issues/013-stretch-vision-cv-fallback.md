## Parent PRD

`docs/prd.md`

## What to build

Stretch / future enhancement (out of scope for the MVP): a **fallback path for CVs that fail text extraction**. Today (issue 003) intake is text-layer-only — `parse_cv` extracts the PDF's embedded text and `looks_like_real_text` rejects anything empty or garbled (scans, heavy multi-column layouts, per-glyph-spaced design-tool exports). This issue adds the *second half* of the industry-standard hybrid pattern: when the cheap deterministic extraction is judged low-quality, **escalate** instead of rejecting.

Two escalation options, in increasing capability:

1. **OCR** (e.g. Tesseract / a cloud OCR API) — converts scanned page images to text. Handles scans, not layout garble.
2. **Vision / multimodal LLM** — render each page to an image and send it to a vision-capable model (reuses the existing OpenRouter LLM seam). The model *reads the rendered page*, sidestepping the broken text layer entirely; handles scans, columns, and per-glyph spacing in one shot.

The `looks_like_real_text` heuristic from issue 003 is already the trigger that decides when to escalate — this issue consumes that signal.

## Acceptance criteria

- [ ] When `parse_cv` yields `is_usable=False`, the upload path attempts a configured fallback (OCR or vision-LLM) before reporting failure.
- [ ] The fallback is **config-gated and off by default** (cost control) — text-first extraction remains the default, free path.
- [ ] A previously-rejected fixture (scanned PDF and/or per-glyph-spaced PDF) is successfully read via the fallback.
- [ ] Token/cost impact of the vision path is measured and noted (images are token-expensive); fallback respects the input caps.
- [ ] Not all OpenRouter models support vision — model support is verified and the fallback model is curated to a supporting one.
- [ ] README reflection notes the cost-vs-robustness tradeoff and the text-first / vision-fallback architecture.

## Blocked by

- Blocked by `docs/issues/003-cv-upload-parse-preview.md`
- Relies on the LLM seam from `docs/issues/002-real-openrouter-call-usage.md`

## User stories addressed

- User story 1 (upload CV as PDF — extends to hard-to-parse PDFs)
- User story 3 (clear handling when a PDF has no usable text — extends "reject" to "recover")
