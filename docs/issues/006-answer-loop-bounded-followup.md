## Parent PRD

`docs/prd.md`

## What to build

The interview conversation loop: a `/reply` endpoint takes the candidate's answer, appends it to the server-side transcript, runs the **interviewer** role, and returns either the next planned question or a single adaptive follow-up — enforcing the turn cap (~8–12) and the one-follow-up-per-topic rule. The UI shows the running conversation. This is the heart of the **interview engine** state machine. See PRD → Agent design (interviewer), core-loop decisions, and the interview-engine module sketch.

## Design decisions (resolved)

The control architecture is **"the model proposes, the engine enforces"** — the LLM makes a bounded *local* decision per turn, while all hard limits and termination live in deterministic code (an LLM is never trusted to end its own loop). This mirrors the mature state-machine-with-LLM-router pattern (e.g. LangGraph, Intercom Fin's guardrail harness).

- **Action space:** the interviewer call returns a structured `InterviewerTurn { reasoning, action, question }` where `action ∈ {follow_up, advance}`. `finish` is **never** the model's choice — the engine declares the interview over purely from state (advanced past the last topic, or hit `max_turns`).
- **Field order = CoT:** `reasoning → action → question`, so the decision and the question are both conditioned on the analysis (strict-JSON fields generate top-to-bottom).
- **One LLM call per reply:** the engine computes what is legal *before* the call and writes it into the prompt ("you've used your follow-up — move to topic X"), so the question always matches the action. The engine's override is a defense-in-depth backstop, not the primary mechanism.
- **State:** `current_topic_index` (which topic's opening question) and `followups_asked` (follow-ups used on the *current* topic, reset to 0 on advance). `follow_up` is legal iff `followups_asked < max_followups_per_topic`.
- **Three structural bounds:** topic count (5–6, from the plan) caps opening questions; `max_followups_per_topic` caps probes per topic; `max_turns` (=12) is a total-length safety net counting **all** assistant questions in the transcript (follow-ups included).
- **Untrusted answer:** sent to the model as a real `user`-role turn, but its content is wrapped in `<candidate_answer>` via `wrap_untrusted` (role is *addressing*, not a trust grant). New `validate_answer()` guard: strip, reject empty (400), cap at `max_answer_chars` (=5000). Unknown `session_id` → 404.
- **Response:** `ReplyResponse { done: bool, next_question: str | None }` via `response_model`; `reasoning`/`action`/plan/topic-index never cross the HTTP boundary. The **frontend owns the display transcript** (appends each exchange locally); the server transcript stays the engine's source of truth.
- **Testability:** the budget rules are extracted into a pure `resolve_transition(...)` function (proposed action + counts → `follow_up`/`advance`/`finish`), tested exhaustively without an LLM, plus a few stub-level `reply()` integration tests.

## Acceptance criteria

- [ ] `/reply` accepts `{session_id, answer}` and returns `{done, next_question}`, advancing server-side state. Unknown `session_id` → 404; empty/oversized answer → 400.
- [ ] At most `max_followups_per_topic` (config, default 1) adaptive follow-ups are asked per topic; the engine then moves to the next planned topic. The limit is enforced by the engine, not the model.
- [ ] The interview is bounded: it will not exceed the configured turn cap (`max_turns`, counting all assistant questions), after which the response signals `done` and returns no further question.
- [ ] The interviewer uses its per-role temperature (≈0.6) from config.
- [ ] The full conversation so far is visible in the UI, one exchange at a time (frontend-owned transcript).
- [ ] The candidate's answer is treated as untrusted data — wrapped in `<candidate_answer>` delimiters (same posture as CV/JD) and length-capped via `validate_answer`.
- [ ] The state-machine transitions are tested against the stub: the pure `resolve_transition` rules exhaustively (cap enforcement, follow-up limit, advance, finish) plus `reply()`-level happy-path integration tests.

## Blocked by

- Blocked by `docs/issues/005-start-classify-plan-first-question.md`

## User stories addressed

- User story 6
- User story 8
- User story 9
- User story 11
