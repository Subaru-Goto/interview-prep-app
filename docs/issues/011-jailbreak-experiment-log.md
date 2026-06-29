## Parent PRD

`docs/prd.md`

## What to build

The adversarial security experiment (medium bonus): deliberately attempt to break the app — inject instructions via the CV/JD/answers, try to extract the hidden rubric, and try to use it as a free general-purpose chatbot — and log each attempt with its outcome and which guard caught it, in a spreadsheet. Produces evidence that the guards from issues 005 and 008 actually work. See PRD → Implementation Decisions (Security: bonus experiment).

**Working log:** entries are captured in [`docs/security/jailbreak-log.md`](../security/jailbreak-log.md) as tests are run — this doubles as raw material for a planned public write-up (blog / LinkedIn) on how the app was hardened and red-teamed.

## Acceptance criteria

- [ ] A spreadsheet logs each attack attempt: the input used, the attack type, the observed result, and which guard (if any) caught it.
- [ ] Attack categories covered: CV/JD prompt injection, rubric/plan extraction, off-topic / free-chatbot abuse, oversized-input.
- [ ] For each category, the outcome (blocked / partially blocked / succeeded) is recorded honestly.
- [ ] Any successful or partial bypass is noted as a known limitation in the README, with a mitigation idea.

## Blocked by

- Blocked by `docs/issues/008-security-hardening-stay-on-task.md`

## User stories addressed

- User story 17
- User story 18
