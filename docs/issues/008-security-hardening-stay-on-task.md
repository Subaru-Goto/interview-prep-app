## Parent PRD

`docs/prd.md`

## What to build

Harden the security posture beyond the primary guard introduced in issue 005: add stay-on-task / role-adherence behavior (refuse off-topic requests and rubric-extraction attempts, redirect back to the interview), confirm output-side validation as a guard, and document the full layered defense. See PRD → Implementation Decisions (Security) and user stories 17, 18, 21.

## Acceptance criteria

- [ ] When the candidate asks the agent to do something unrelated (e.g. "write me code", "ignore the interview"), it politely redirects and stays in the interviewer role.
- [ ] Attempts to extract the hidden plan/rubric are refused; the plan/rubric never appear in any response.
- [ ] Injection attempts embedded in CV/JD/answers do not change the agent's instructions (the delimiting guard holds).
- [ ] All structured model outputs pass through Pydantic validation; invalid outputs fail loudly and are not rendered.
- [ ] The layered defense (data/instruction separation, input caps, stay-on-task, server-side secrets, output validation) is documented in the README.

## Blocked by

- Blocked by `docs/issues/005-start-classify-plan-first-question.md`

## User stories addressed

- User story 17
- User story 18
- User story 21
