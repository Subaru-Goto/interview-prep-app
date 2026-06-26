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

## Roadmap

Work is tracked as an issue backlog in [`docs/issues/`](docs/issues/), built as thin end-to-end slices: walking skeleton → real OpenRouter client → CV upload → JD input → interview start → answer loop → feedback report, plus security, cost metering, and a prompt bake-off. The full product spec lives in [`docs/prd.md`](docs/prd.md).
```
