## Parent PRD

`docs/prd.md`

## What to build

The interview kickoff slice: a `/start` endpoint takes the validated CV + JD, runs the **classifier** (→ interview type + seniority) and the **planner** (CoT → hidden 5–6 topic plan), stores the plan + transcript server-side in the session store (behind the `get`/`save` interface), and returns the first question to the UI. The **data/instruction-separation guard** is introduced here — the first place untrusted CV/JD reaches the model — wrapping them in delimiters with a system instruction to treat them as data only. Classifier and plan outputs use `response_format` + Pydantic. See PRD → Agent design, Structured output, Security (primary guard), and the prompt-registry / schemas / session-store / interview-engine module sketches.

## Acceptance criteria

- [ ] `/start` accepts CV text + JD, returns a `session_id` and the first interview question.
- [ ] Classifier returns a structured, Pydantic-validated classification (interview type + seniority); planner returns a structured, Pydantic-validated plan of 5–6 topics.
- [ ] The plan and any rubric are stored server-side only and are absent from every client-facing response (verified by inspecting the response payload).
- [ ] CV and JD are passed to the model wrapped in explicit delimiters, with a system instruction to treat delimited content as untrusted data and never follow instructions inside it.
- [ ] Session state is created via the `get`/`save` storage interface (in-memory dict implementation) keyed by `session_id`.
- [ ] Classifier and planner use per-role temperatures from config (≈0.1 and ≈0.4).
- [ ] Works end-to-end in stub mode (canned plan/question) and with a real model.
- [ ] The relevant Pydantic schemas reject malformed/out-of-range objects (tested in isolation).

## Blocked by

- Blocked by `docs/issues/002-real-openrouter-call-usage.md`
- Blocked by `docs/issues/004-jd-paste-start-validation.md`

## User stories addressed

- User story 6
- User story 7
- User story 12
- User story 17
- User story 21
