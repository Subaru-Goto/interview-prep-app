## Parent PRD

`docs/prd.md`

## What to build

The end-of-interview slice: a finish path (triggered at the turn cap or by an explicit "End interview" button) runs the **judge** role over the full transcript and produces a Pydantic-validated **scorecard** (overall assessment, per-topic scores, strengths, gaps, recommendation), which the UI renders as a feedback report. This is the second graded structured-JSON format and the runtime LLM-as-judge feature. See PRD → Agent design (judge), Structured output, and core-loop (end early) decisions.

## Acceptance criteria

- [ ] An "End interview" button lets the candidate finish early at any point.
- [ ] Reaching the turn cap also leads to finishing.
- [ ] The judge produces a structured, Pydantic-validated scorecard with: overall assessment, per-topic scores, strengths, gaps, and a recommendation.
- [ ] The judge uses its per-role temperature (≈0.1) from config.
- [ ] The UI renders the scorecard as a readable feedback report.
- [ ] A malformed/out-of-range judge output is caught by validation and surfaced as a clear error rather than rendered as garbage.
- [ ] Works end-to-end in stub mode and with a real model.

## Blocked by

- Blocked by `docs/issues/006-answer-loop-bounded-followup.md`

## User stories addressed

- User story 10
- User story 13
- User story 14
- User story 15
- User story 16
