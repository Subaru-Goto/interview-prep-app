# Streaming the interviewer's question drops the strongest anti-mega-question lever

## What

Issue 010/problem 001 established that the **schema field description** on
`InterviewerTurn.question` (`app/schemas.py`) — not prompt wording — was the
dominant fix for the mega-question bug, pushing zero-shot from 0.20 to
0.93+ on `SingleFocusedQuestion`. To stream the interviewer's question
token-by-token (this session's latency work: `stream_first_question()` and
`stream_reply_question()` in `app/interview_engine.py`), those calls had to
drop `response_schema` entirely — plain text doesn't support the JSON-schema
mechanism that field description relies on. A `SINGLE_QUESTION_GUARD` prompt
fragment (`app/prompts.py`) was added to compensate, appended directly into
the system prompt text for both streaming calls.

One real-API test of `stream_reply_question()` (not the bake-off's
multi-fixture methodology — a single sample) produced this question:

> "What specific consistency model and fault-tolerance strategy did you
> choose for the checkout service during the traffic spike, **and** how did
> you reason about the trade-offs between availability, latency, **and**
> correctness?"

This is a mega-question — two questions joined by "and", the exact pattern
`SINGLE_QUESTION_GUARD` explicitly calls out as "the single most common
mistake, avoid it above all else."

## Why

- The schema field description and the plain-text guard carry the same
  words, but they aren't equally effective levers — problem 001's own
  bake-off data showed prompt-text-only instructions (zero-shot, few-shot,
  role-play, all pre-schema-fix) topped out at 0.10-0.30, while the
  schema-description fix alone pushed zero-shot to 0.93+. Moving the
  instruction from schema back into prompt text is moving back toward the
  weaker mechanism, for the calls that had to give up structured output.
- `decide_and_advance()` still uses `response_schema=InterviewerDecision`
  (fast, non-streamed) and keeps full schema enforcement — only the actual
  question-generation calls (`stream_first_question`,
  `stream_reply_question`) lost it, since those are the ones that had to
  become plain-text to stream cleanly.
- This is a single observed sample, not a scored multi-fixture result — it's
  evidence the risk is real, not proof of how often it happens.

## How should it be if the problem is solved

- The streamed question-generation calls should score comparably to the
  pre-streaming, schema-enforced `InterviewerTurn.question` on
  `SingleFocusedQuestion` (bake-off's own metric), not just pass a single
  manual eyeball check.
- Concretely, this likely needs the same kind of empirical iteration problem
  001 went through: run `stream_first_question`/`stream_reply_question`'s
  output through the bake-off's scoring across 2-3 fixtures, see how often
  "and"-joined compounds recur, and strengthen `SINGLE_QUESTION_GUARD`
  accordingly (e.g. an explicit bad-example the way few-shot's prompt has
  one) rather than assuming the schema-derived wording carries over as-is.
- Alternative worth evaluating: whether OpenAI/OpenRouter's streaming API
  supports any structured-output-compatible streaming mode that could
  restore the schema mechanism without losing token-by-token delivery —
  this wasn't investigated before choosing the split-call, schema-free
  approach (Option B in the original streaming design discussion).

## Reference: real sample

Real API call (`gpt-5-nano`, `reasoning_effort=minimal`), via
`stream_reply_question()` after a candidate answer describing a checkout
service using caching and a queue in front of a payment provider:

- First token: 0.668s, full generation: 1.02s (the latency fix worked as
  intended — this problem is specifically about question *quality*, not
  speed).
- Output: "What specific consistency model and fault-tolerance strategy did
  you choose for the checkout service during the traffic spike, and how did
  you reason about the trade-offs between availability, latency, and
  correctness?" — two questions joined by "and", twice.

Not yet re-run across multiple fixtures or scored against the bake-off's
`SingleFocusedQuestion` metric — that's the natural next step before
concluding how serious this is in practice.
