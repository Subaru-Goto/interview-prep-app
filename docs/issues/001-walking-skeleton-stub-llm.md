## Parent PRD

`docs/prd.md`

## What to build

The walking skeleton: a thin end-to-end path from the Next.js UI through a FastAPI endpoint to the **LLM client** and back to the screen — with the LLM client in **stub mode** (`USE_FAKE_LLM`) returning a canned response, so the whole loop works at zero API cost. Establishes the repo structure, the centralized config object (`pydantic-settings` / `.env`), and the deep `LLM client` seam everything else builds on. See PRD → Implementation Decisions (Architecture, Configuration & cost-control) and the LLM-client module sketch.

## Acceptance criteria

- [ ] Repo has `/backend` (FastAPI) and `/frontend` (Next.js) that run locally and can talk to each other (CORS configured for local dev).
- [ ] A single config object holds all tunables (model id, per-role temperatures, active interviewer-prompt variant, `USE_FAKE_LLM`) and loads from `.env`; nothing reads secrets/model ids directly elsewhere.
- [ ] `.env.example` documents every required variable; real `.env` is git-ignored.
- [ ] An `LLM client` function exposes a stable interface (`complete(messages, temperature, schema?)`) and, when `USE_FAKE_LLM=true`, returns a deterministic canned response without any network call.
- [ ] The frontend has a trivial UI action that POSTs to a FastAPI endpoint, which calls the stubbed LLM client and renders the returned text on screen.
- [ ] App runs with no OpenRouter key set (stub mode is the default for development).
- [ ] README documents how to install deps and run both servers.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 22
- User story 23
