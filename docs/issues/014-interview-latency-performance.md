## Parent PRD

`docs/prd.md`

## What to build

Reduce the real-model latency of the interview flow, which is currently slow at two points: **starting an interview** and **each reply**. This is deferred performance work — the flow is functionally complete (005/006); this issue makes it feel fast with a real model. To be picked up once the core feature set is done.

Root causes (observed during 006 real-model smoke testing):

- **`/start` — three sequential LLM calls.** `start_interview` runs classify → plan → first-question one after another. Classify and plan are **independent** (the plan does not consume the classification result), so they can run concurrently; only the first-question call needs both. Running the two independent calls in parallel should cut roughly a third off the start time.
- **`/reply` — very long model outputs.** `gpt-5-nano` emits sprawling, multi-part "mega-questions" (see the early observations in `010-prompt-bakeoff-writeup.md`). Output length is the dominant latency cost, so the same prompt fix that improves question quality (issue 010) also reduces reply latency. These two issues share a fix.

## Already done (out of scope here)

- Responsive / full-viewport layout (mobile fills the screen, desktop is a sized panel).
- Perceived-latency UI: an "Interviewer is thinking…" indicator, disabled/loading button states on start and reply.

## Acceptance criteria

- [x] `/start` runs the classifier and planner calls **concurrently** (independent calls), with the first-question call after both; measured start latency is meaningfully lower than the sequential version. (Done via `perf/parallel-interview-setup`, merged in PR #13 — `ThreadPoolExecutor` around the two sync client calls, per the "keep it simple" note below.)
- [ ] Interviewer questions are concise — a single focused question, not multi-part walls — reducing output tokens per turn (coordinate with `010-prompt-bakeoff-writeup.md`; the winning prompt should enforce this).
- [ ] No behavioural regressions: the `resolve_transition` rules, turn cap, follow-up limit, and hidden-state guarantees are unchanged (existing tests still pass).
- [ ] (Stretch) Stream the interviewer's response so it appears progressively for better perceived latency. Note: the reply turn uses structured output (`InterviewerTurn`), which complicates token streaming — evaluate streaming only the `question` field, or a separate lightweight text call.
- [ ] (Investigate) Confirm model choice/latency trade-offs on OpenRouter; document whether a faster model or fewer reasoning tokens helps.

## Relates to

- Builds on `docs/issues/005-start-classify-plan-first-question.md` and `docs/issues/006-answer-loop-bounded-followup.md` (both complete).
- Shares a fix with `docs/issues/010-prompt-bakeoff-writeup.md` (concise questions reduce both output sprawl and latency).

## Notes

- This is UX/performance polish, not a new user-facing capability — no new user story. It supports the general goal of a usable, responsive practice tool.
- Keep the parallelization simple (e.g. a thread pool around the two sync client calls); do not over-engineer into full async unless it proves necessary.
