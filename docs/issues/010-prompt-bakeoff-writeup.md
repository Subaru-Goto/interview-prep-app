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

## Blocked by

- Blocked by `docs/issues/006-answer-loop-bounded-followup.md`

## User stories addressed

- User story 24
