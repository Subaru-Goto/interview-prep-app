## Parent PRD

`docs/prd.md`

## What to build

The job-description input and pre-start validation: a JD textarea, plus the gate that prevents starting an interview with empty or unusably short CV/JD. Completes the input surface so issue 005 always receives valid CV + JD. See PRD → Implementation Decisions (Security: input validation) and the input-guard module sketch.

## Acceptance criteria

- [ ] Candidate can paste a job description into a textarea with a visible character cap.
- [ ] Attempting to start with an empty or too-short CV or JD is blocked with a clear, specific message (which field, why).
- [ ] JD length over the cap is rejected (or truncated with notice) before any model call.
- [ ] The input-guard validation logic is tested in isolation (valid passes; empty/short/oversized rejected).
- [ ] On valid input the UI enables the "Start interview" action.

## Blocked by

- Blocked by `docs/issues/003-cv-upload-parse-preview.md`

## User stories addressed

- User story 4
- User story 5
