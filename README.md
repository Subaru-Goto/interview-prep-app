# Interview Prep App

An **automated screening-interview** web app. A candidate uploads their CV and pastes a job description; an AI agent runs a written, multi-turn role-play interview grounded in both, then returns a structured feedback report.

> **Status:** early development. The walking skeleton (frontend ⇄ backend ⇄ a swappable LLM client) is in place and runs entirely in **fake-LLM mode** — no API key required. The interview features (CV parsing, the interview agent, scoring) are being built issue-by-issue; see [`docs/`](docs/).

## Architecture

```
Next.js (React 19, Tailwind)            FastAPI (Python 3.13)
  CV upload · JD paste · chat UI  ──HTTP──►  interview endpoints
                                             └─ LLMClient (a seam):
                                                  FakeLLMClient   (canned, free, for dev/tests)
                                                  OpenRouterClient (real, via OpenRouter)  ← coming
```

The backend never calls the LLM provider directly. Everything goes through an `LLMClient` interface, and a factory picks the implementation from config — so the whole app runs offline against a fake client during development, and swapping models/providers is a localized change.

## Tech stack

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4
- **Backend:** FastAPI, Pydantic / pydantic-settings, managed with **uv**
- **LLM access:** OpenRouter (OpenAI-compatible API)

## Prerequisites

- **Python 3.13** and [**uv**](https://docs.astral.sh/uv/)
- **Node 22** and **npm**

## Setup & run

The app runs in fake-LLM mode by default, so you can start it with **no API key**.

### Backend (`http://localhost:8000`)

```bash
cd backend
uv sync                              # install dependencies
uv run fastapi dev app/main.py       # start dev server
```

- API docs (Swagger UI): http://localhost:8000/docs

### Frontend (`http://localhost:3000`)

```bash
cd frontend
npm install
cp .env.example .env.local     
npm run dev
```

Open http://localhost:3000, type a message, and you'll get a `[FAKE LLM] …` reply — confirming the full round trip through the client seam.

## Configuration

Configuration is read from the environment (with sensible code defaults). Copy each `.env.example` and override only what you need. For the backend, there is also a config.py file.

## Project structure

```
interview-prep-app/
├── backend/            # FastAPI app (uv)
│   └── app/
│       ├── main.py     # endpoints
│       ├── config.py   # typed settings (pydantic-settings)
│       └── llm.py      # LLMClient seam: interface, fake client, factory
├── frontend/           # Next.js app (React 19 + Tailwind)
│   └── app/page.tsx
└── docs/               # PRD and the issue backlog
    ├── prd.md
    └── issues/
```

## Security

Untrusted input (CV text, job description, candidate answers) can never be
trusted to behave — a candidate could try to inject instructions into their
CV, ask the interviewer to do something unrelated, or try to extract the
hidden question plan. The app defends against this in layers, on the
assumption that any single layer could fail:

1. **Data/instruction separation.** Untrusted text is wrapped in named tags
   (`<cv>`, `<job_description>`, `<candidate_answer>`) with special
   characters escaped (`app/input_guard.py::wrap_untrusted`), and every
   system prompt explicitly tells the model to treat content inside those
   tags as data, never as instructions. Putting a candidate's text in a
   `user`-role message would not by itself make it trusted — the tags plus
   the system-prompt rule are what mark it as data.
2. **Stay-on-task role adherence.** The interviewer's system prompt
   (`INTERVIEWER_TURN_SYSTEM_PROMPT`) explicitly instructs the model to stay
   in its interviewer role regardless of what a candidate's answer asks for
   — refusing off-topic requests (e.g. "write me code"), refusing to reveal
   the interview topics or scoring rubric, and refusing to follow embedded
   instructions ("ignore the above") — then redirect back to the current
   question. The judge's prompt carries an equivalent rule so injected
   content can't shift a score or leak into the report's wording.
3. **Input caps.** CV upload is PDF-only with a size limit; JD and answer
   text have length caps (`app/config.py`); the interview itself is bounded
   to a max number of turns and follow-ups — all enforced in code, not left
   to the model to self-limit.
4. **Server-side secrets.** The interview plan, topic list, and
   classification are held only in server-side session state and are never
   included in any API response — `/start`, `/reply`, and `/finish` return
   only what the candidate is meant to see (tested explicitly in
   `test_start_endpoint.py::test_start_response_hides_plan_and_classification`).
   The judge is only ever shown the topics that were actually discussed, not
   the full plan, so it has nothing to leak about topics never reached.
5. **Output-side validation.** Every structured model response (
   classification, interview plan, interviewer turn, scorecard) is parsed
   through a Pydantic schema with field-level constraints (e.g. scores
   bounded 1-5, a fixed set of topics). A response that fails validation
   raises loudly and is caught at the API boundary as a clean error (400/502)
   — it is never rendered to the candidate as garbage.

**Known limitation:** this is prompt-based defense-in-depth, not a provable
guarantee — a sufficiently adversarial input could still get partway past
layer 2. The architecture is designed so that even if the model's behavior
is imperfect, the things that actually matter (hard turn limits, hidden
plan/rubric, structural output validity) are enforced in code, not by asking
the model nicely.

## Roadmap

Work is tracked as an issue backlog in [`docs/issues/`](docs/issues/), built as thin end-to-end slices: walking skeleton → real OpenRouter client → CV upload → JD input → interview start → answer loop → feedback report, plus security, cost metering, and a prompt bake-off. The full product spec lives in [`docs/prd.md`](docs/prd.md).
```
