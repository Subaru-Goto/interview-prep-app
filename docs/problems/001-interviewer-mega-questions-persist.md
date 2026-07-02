# All four interviewer prompt variants still produce bundled, multi-part questions

## What

The prompt bake-off (`backend/bakeoff/run.py`, scored by DeepEval's custom
`SingleFocusedQuestion` `GEval` metric in `backend/bakeoff/metrics.py`) shows
that **none of the 4 interviewer prompt variants** (zero-shot, few-shot,
chain-of-thought, role-play) reliably produce a single, focused question.
Every variant still bundles multiple sub-questions or enumerated lists into
one turn — the exact "mega-question" bug first observed back in issues
005/006, which this bake-off (issue 010) was supposed to fix.

All 4 scored well below the metric's `threshold=0.7` (see Reference below).

## Why

- The shared closing instruction every variant carries ("decide follow-up or
  advance, then ask a single, clear question... answerable in a few
  minutes") is evidently not a strong enough constraint on its own — the
  model defaults to being thorough and covers multiple angles of the
  candidate's answer rather than picking one.
- **Chain-of-thought made it worse, not better.** Explicitly asking the model
  to "think step by step about what to probe" seems to invite it to
  enumerate more angles worth asking about, and those angles leak directly
  into the output as a numbered list instead of staying in its internal
  reasoning. This is a real, evidence-backed finding, not a guess — see the
  scores below.
- Few-shot's contrastive good/bad example (`app/prompts.py`,
  `INTERVIEWER_PROMPT_FEW_SHOT`) helped somewhat (tied for the best score)
  but didn't fully solve it — one worked example wasn't a strong enough
  signal to override the model's default of being comprehensive.
- None of the 4 variants carry a **hard, unambiguous format constraint** —
  something like "output exactly one sentence, ending in exactly one
  question mark, no lists, no 'and'/'also'" — which is a different kind of
  instruction than the technique-specific framing each variant currently
  varies on.

## How should it be if the problem is solved

- At least one variant should reliably score above the `0.7` threshold on
  `SingleFocusedQuestion` across multiple fixtures (issue 010 AC3 wants 2-3
  fixed CV/JD fixtures — this bake-off has so far only tested one), not just
  on a single lucky run.
- The generated question should read as a single sentence a candidate could
  answer out loud in under a minute, with no enumerated sub-parts and no
  "and"/"also"-joined compound asks.
- Concretely, this likely means layering an explicit hard format constraint
  (see above) onto whichever variant is closest to working, independent of
  that variant's underlying technique (few-shot's examples, CoT's reasoning
  step, or role-play's persona) — the technique and the format constraint
  are solving different problems and probably both need to be present at
  once.

## Reference: real bake-off results

From one real run of `backend/bakeoff/run.py` (fixture: "System design" topic,
one prior candidate answer about caching + a queue in front of the payment
provider), model + judge both real (not stub):

| Variant | Action | Score | Judge's reasoning |
|---|---|---|---|
| zero_shot | follow_up | 0.20 | Enumerated (1)-(4) sub-questions in one prompt; broad scope unlikely answerable quickly. |
| few_shot | follow_up | 0.30 | Still bundles 4-5 sub-asks joined by "and", despite the good/bad worked examples. |
| chain_of_thought | follow_up | **0.10 (worst)** | Enumerated (1)-(5); the "think step by step" framing appears to have produced *more* sub-aspects, not fewer. |
| role_play | follow_up | 0.30 | Enumerated (1)-(3); persona framing had no effect on question structure. |

Example output (zero-shot, for concreteness):

> "Could you walk me through the end-to-end flow of that checkout service
> during peak load, including (1) what data you cached and how you
> invalidate it, (2) the queue design (which system, at-least-once vs
> exactly-once semantics, how you scale consumers), (3) how you ensured
> idempotency and correct retries with the payment provider, and (4) what
> instrumentation and tests you used to validate correctness under load?"

Only one fixture has been tested so far — per issue 010's AC3, this should
be re-run against 2-3 fixed CV/JD fixtures before drawing a final conclusion
or picking a winner.
