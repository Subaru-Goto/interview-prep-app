## Parent PRD

`docs/prd.md`

## What to build

The mandatory prompt experiment: fill the **prompt registry** with three interviewer system-prompt variants (zero-shot, few-shot, role-play persona), make the active variant selectable via config, run a controlled bake-off across 2–3 fixed `(CV, JD)` fixtures, pick the winner, and write up each technique + observations for submission. See PRD → Prompt engineering and Further Notes (reflection deliverables).

**Scoped down from 5 to 4 to 3 variants** — two deliberate cuts, both
recorded rather than silent:

1. **Structured-rubric** (5→4): never built. With 4 variants, the registry
   still covered a clearly distinct technique per entry.
2. **Chain-of-thought** (4→3): built, tested, then removed. The bake-off
   (`backend/bakeoff/run.py`) showed it scored *worst* of the 4 (0.10 on the
   `SingleFocusedQuestion` metric — see
   [docs/problems/001-interviewer-mega-questions-persist.md](../problems/001-interviewer-mega-questions-persist.md)),
   and closer inspection showed why it was never a fair fourth technique to
   begin with: `InterviewerTurn.reasoning`'s schema field description
   (`app/schemas.py`) already instructs "think here first, then choose the
   action" — a chain-of-thought instruction baked into the **schema**,
   applying to *every* variant regardless of which prompt is active. The
   dedicated CoT *prompt* variant wasn't testing a technique the others
   lacked; it restated something already universal, and without specifying
   *where* that reasoning should go, its enumeration leaked directly into
   the visible `question` field — which is exactly why it scored worst.
   Fixed by tightening the schema descriptions themselves (both `reasoning`
   and `question`) so the separation is explicit and applies to all
   remaining variants at once, rather than keeping a redundant variant
   around. Chain-of-thought as a *technique* is still represented in the
   project — the **planner** already runs its own dedicated CoT pass
   (`INTERVIEW_PLAN_SYSTEM_PROMPT`), unrelated to the interviewer bake-off.

`docs/prd.md`'s "mandatory requirement" wording was updated to say three,
so the docs and the code agree.

## Acceptance criteria

- [ ] Three distinct interviewer prompt variants exist in the prompt registry, each using a clearly different technique.
- [ ] The active variant is chosen from config (one place), with no code edits to switch.
- [ ] 2–3 fixed `(CV, JD)` test fixtures exist and are reused across variants.
- [ ] Each variant is run against the fixtures and outputs are recorded.
- [ ] A README comparison table documents: technique → what was observed → kept/rejected, and names the chosen winner with rationale.
- [ ] The writeup also notes which techniques the planner (CoT) and judge (structured) use.

## Early observations (seed data, before the formal bake-off)

- **The zero-shot interviewer prompt produces overloaded, multi-part "mega-questions."** Observed on `gpt-5-nano` in both the 005 opener smoke test and the 006 `/reply` loop smoke test: despite the prompt instructing "a single, clear question answerable in a few minutes," the model emits walls of 5–10 bundled sub-questions ("cover: 1)… 2)… 3)…"). No human could answer these in an interview. This is a prompt-quality problem (the engine/state machine is correct), and it's the primary thing the bake-off should fix.
  - Candidate fixes to test as variants: a hard "ask exactly ONE focused question, no sub-parts or enumerated lists" constraint; a **few-shot** example showing a good short question vs. a bad overloaded one; an explicit length/format cap folded into whichever variant needs it — now applied at the schema level (`InterviewerTurn.question`'s field description) rather than per-variant, since the bake-off in
    [docs/problems/001-interviewer-mega-questions-persist.md](../problems/001-interviewer-mega-questions-persist.md)
    showed every variant needed it, not just one.
  - The follow-up/advance mechanism itself works — topic pairs (probe then move on) and clean termination at the turn cap were both observed.

## Blocked by

- Blocked by `docs/issues/006-answer-loop-bounded-followup.md`

## User stories addressed

- User story 24
