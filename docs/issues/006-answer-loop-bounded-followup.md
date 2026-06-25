## Parent PRD

`docs/prd.md`

## What to build

The interview conversation loop: a `/reply` endpoint takes the candidate's answer, appends it to the server-side transcript, runs the **interviewer** role, and returns either the next planned question or a single adaptive follow-up — enforcing the turn cap (~8–12) and the one-follow-up-per-topic rule. The UI shows the running conversation. This is the heart of the **interview engine** state machine. See PRD → Agent design (interviewer), core-loop decisions, and the interview-engine module sketch.

## Acceptance criteria

- [ ] `/reply` accepts `{session_id, answer}` and returns the next question (or follow-up), advancing server-side state.
- [ ] At most one adaptive follow-up is asked per topic; the engine then moves to the next planned topic.
- [ ] The interview is bounded: it will not exceed the configured turn cap, after which the next call signals the interview is ready to finish.
- [ ] The interviewer uses its per-role temperature (≈0.6) from config.
- [ ] The full conversation so far is visible in the UI, one exchange at a time.
- [ ] The candidate's answer is treated as untrusted data (same delimiting/guard posture as CV/JD).
- [ ] The state-machine transitions (ask → reply → probe-or-advance → finish, cap enforcement, follow-up limit) are tested against the stubbed LLM client.

## Blocked by

- Blocked by `docs/issues/005-start-classify-plan-first-question.md`

## User stories addressed

- User story 6
- User story 8
- User story 9
- User story 11
