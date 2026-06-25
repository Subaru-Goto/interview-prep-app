## Parent PRD

`docs/prd.md`

## What to build

Per-session cost metering: fetch per-model pricing from OpenRouter's `/models` endpoint, combine with the `usage` captured on every call (issue 002) via the deep **cost calculator** module, accumulate a per-session total, and surface it without polluting the candidate flow. The backend always computes/logs/returns cost; the UI shows a **muted footer on the results page only** (after the interview is over, so no immersion cost), with richer/live detail gated behind a `DEV_MODE` flag. Satisfies the cost-calculation medium bonus. See PRD → Implementation Decisions (Cost) and the cost-calculator module sketch.

## Acceptance criteria

- [ ] Per-model pricing is retrieved from OpenRouter's `/models` endpoint.
- [ ] The cost calculator is a pure function: given a usage record + pricing, it returns the correct cost (tested in isolation, including zero/edge cases).
- [ ] Cost accumulates across all calls within a session; the backend logs it and returns it in the API payload on every call.
- [ ] No cost appears anywhere in the candidate interview flow (upload / JD / Q&A screens).
- [ ] The results/feedback page shows a single muted "session info" footer (e.g. turns · tokens · ~$cost) once the interview is finished.
- [ ] A `DEV_MODE` env flag (off by default) can reveal richer detail (e.g. live running total / per-call breakdown); when off, candidates never see it.
- [ ] Cost works with the real model; in stub mode it shows zero or a clearly-marked placeholder.

## Blocked by

- Blocked by `docs/issues/002-real-openrouter-call-usage.md`

## User stories addressed

- User story 20
