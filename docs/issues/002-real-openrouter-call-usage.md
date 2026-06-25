## Parent PRD

`docs/prd.md`

## What to build

Make the `LLM client` reach a real model through OpenRouter (OpenAI SDK with `base_url` pointed at OpenRouter) when `USE_FAKE_LLM=false`, and capture the `usage` (prompt/completion tokens) from every response. Same code path as issue 001 — only the client's backend changes. See PRD → Implementation Decisions (LLM access) and user story 25.

## Acceptance criteria

- [ ] With `USE_FAKE_LLM=false` and a valid OpenRouter key in `.env`, the skeleton action from issue 001 returns a genuine model response.
- [ ] The client uses the OpenAI Python SDK configured with OpenRouter's `base_url`; the API key is read from config only (never hard-coded).
- [ ] Every real call returns its `usage` (prompt_tokens, completion_tokens) to the caller alongside the content.
- [ ] Switching between stub and real is a single config/env change with no code edits.
- [ ] Default development model is `gpt-5-nano` (cheap); model id comes from config.
- [ ] Missing/invalid key produces a clear error message, not a silent failure or a stack trace leaking secrets.

## Blocked by

- Blocked by `docs/issues/001-walking-skeleton-stub-llm.md`

## User stories addressed

- User story 25
