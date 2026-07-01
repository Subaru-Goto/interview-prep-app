## Parent PRD

`docs/prd.md`

## What to build

Per-session cost metering: accumulate the `usage` captured on every call (issue 002) into a per-session total, and surface it without polluting the candidate flow. The backend always computes/logs/returns cost; the UI shows a **muted footer on the results page only** (after the interview is over, so no immersion cost), with richer/live detail gated behind a `DEV_MODE` flag. Satisfies the cost-accounting medium bonus. See PRD → Implementation Decisions (Cost).

**Pivoted mid-implementation (from a self-computed calculator to a pass-through):**
the original plan (and the PRD text this issue was scoped against) was to fetch
per-model pricing from OpenRouter's `/models` endpoint and multiply it against
captured token counts via a pure **cost calculator** module. While building
that, we learned OpenRouter now returns the actual billed USD cost directly on
every response's `usage` object (`usage.cost` — automatic, no request flag
needed; the old `usage: {include: true}` param is deprecated/no-op). That's
strictly better than a self-computed estimate: it's authoritative (reflects
whatever OpenRouter actually charges, including prompt-caching discounts a
naive `tokens × list price` multiply would miss), and it closes a real gap the
`/models`-based design had — a genuinely free model and a failed pricing
lookup both silently collapsed to the same `$0.00`, with nothing to tell them
apart. We dropped the `/models` fetch and the calculator entirely (`app/cost.py`
and its tests were deleted) and instead capture `usage.cost` straight from
the LLM client response. The PRD's Cost and Testing Decisions sections were
updated to match — see `docs/prd.md`.

## Acceptance criteria

- [x] ~~Per-model pricing is retrieved from OpenRouter's `/models` endpoint.~~ Superseded — cost comes directly from `usage.cost` on every response; no separate pricing lookup.
- [x] ~~The cost calculator is a pure function: given a usage record + pricing, it returns the correct cost (tested in isolation, including zero/edge cases).~~ Superseded — nothing to calculate. Instead, `OpenRouterLLMClient` is tested in isolation to confirm it correctly reads `usage.cost` off the response (and defaults to `0.0` if a response ever omits it).
- [x] Cost accumulates across all calls within a session; the backend logs it and returns it in the API payload on every call.
- [x] No cost appears anywhere in the candidate interview flow (upload / JD / Q&A screens).
- [x] The results/feedback page shows a single muted "session info" footer (e.g. turns · tokens · ~$cost) once the interview is finished.
- [x] A `DEV_MODE` env flag (off by default) can reveal richer detail (e.g. live running total / per-call breakdown); when off, candidates never see it.
- [x] Cost works with the real model; in stub mode it shows zero or a clearly-marked placeholder.

## Blocked by

- Blocked by `docs/issues/002-real-openrouter-call-usage.md`

## User stories addressed

- User story 20
