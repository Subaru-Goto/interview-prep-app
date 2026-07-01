## Parent PRD

`docs/prd.md`

## What to build

The mandatory 5-prompt experiment: fill the **prompt registry** with all five interviewer system-prompt variants (zero-shot, few-shot, chain-of-thought, role-play persona, structured-rubric), make the active variant selectable via config, run a controlled bake-off across 2–3 fixed `(CV, JD)` fixtures, pick the winner, and write up each technique + observations for submission. See PRD → Prompt engineering and Further Notes (reflection deliverables).

## Acceptance criteria

- [ ] Five distinct interviewer prompt variants exist in the prompt registry, each using a clearly different technique.
- [ ] The active variant is chosen from config (one place), with no code edits to switch.
- [ ] 2–3 fixed `(CV, JD)` test fixtures exist and are reused across variants.
- [ ] Each variant is run against the fixtures and outputs are recorded.
- [ ] A README comparison table documents: technique → what was observed → kept/rejected, and names the chosen winner with rationale.
- [ ] The writeup also notes which techniques the planner (CoT) and judge (structured) use.

## Early observations (seed data, before the formal bake-off)

- **The zero-shot interviewer prompt produces overloaded, multi-part "mega-questions."** Observed on `gpt-5-nano` in both the 005 opener smoke test and the 006 `/reply` loop smoke test: despite the prompt instructing "a single, clear question answerable in a few minutes," the model emits walls of 5–10 bundled sub-questions ("cover: 1)… 2)… 3)…"). No human could answer these in an interview. This is a prompt-quality problem (the engine/state machine is correct), and it's the primary thing the bake-off should fix.
  - Candidate fixes to test as variants: a hard "ask exactly ONE focused question, no sub-parts or enumerated lists" constraint; a **few-shot** example showing a good short question vs. a bad overloaded one; an explicit length/format cap; the **structured-rubric** variant (which may naturally discourage sprawl).
  - The follow-up/advance mechanism itself works — topic pairs (probe then move on) and clean termination at the turn cap were both observed.

## Blocked by

- Blocked by `docs/issues/006-answer-loop-bounded-followup.md`

## User stories addressed

- User story 24
