## Parent PRD

`docs/prd.md`

## What to build

Stretch (only if time allows): a development-time automated evaluation of the agents using deepeval — a small, real set of metrics rather than a large suite. Targets: `RoleAdherence` on the interviewer (does it stay in role — also measures jailbreak resistance) and a custom `GEval` for question relevance to the JD, plus a consistency check on the judge. This is the second hard-task evidence (assess prompt/model performance). See PRD → Out of Scope (stretch) and Further Notes.

## Acceptance criteria

- [ ] deepeval is wired to run its metrics through OpenRouter (custom-model config verified against current deepeval docs).
- [ ] At least two metrics run against a small set of test cases: interviewer RoleAdherence and a custom JD-relevance GEval.
- [ ] A judge-consistency check demonstrates that the same answer scores stably at low temperature.
- [ ] Results are summarized in the README as evidence for the evaluation/quality claims.
- [ ] Evaluation runs on the cheap model and on a small fixture set to control token spend.

## Blocked by

- Blocked by `docs/issues/007-finish-structured-scorecard.md`

## User stories addressed

- User story 26
