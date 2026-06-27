# PRD — AI Screening-Interview Prep App

> An automated **screening interview** web app: the candidate uploads a CV and pastes a job description, an AI agent runs a written role-play interview, then returns a scored feedback summary.
>

## Problem Statement

People preparing for job interviews have no efficient, realistic way to practise a **screening interview** for a *specific* role. Generic question lists don't adapt to the candidate's own background or to the target job, and reading sample answers is passive. A candidate wants to be *interviewed* — asked questions grounded in their actual CV and the actual job description, made to answer in their own words, and then told concretely where they were strong and where they have gaps — without needing a human interviewer's time.

## Solution

A single-page web app where the candidate:

1. Uploads their CV (PDF) and pastes the job description for the role they want.
2. Is taken through a written, multi-turn **role-play screening interview** by an AI agent. The agent privately plans the interview from the CV + JD, then asks questions one at a time, occasionally following up to probe a weak or strong answer — like a real screener.
3. Ends the interview (after the planned questions, or early by choice) and receives a **structured feedback report**: an overall assessment, per-topic scores, concrete strengths, gaps, and a recommendation.

Voice is out of scope for this MVP — all interaction is text. The interview **domain is inferred by the agent** (the classifier role) from the job description / title — it is never picked by the candidate. The MVP is tuned to handle software/data roles well; the domain is modeled as an internal parameter so other fields can be added later, but the determination is always the agent's.

## User Stories

### Setup & input
1. As a candidate, I want to upload my CV as a PDF, so that the interview is grounded in my real background without me retyping it.
2. As a candidate, I want clear confirmation that my CV uploaded and parsed successfully (or a clear reason if it failed), so that I know my CV is ready before starting. (The extracted text is **not** shown or editable — it is used as parsed.)
3. As a candidate, I want a clear message when my PDF has no usable text (e.g. a scan), so that I know to upload a different, text-based PDF instead of getting a broken interview. (CV is PDF-only; there is no copy-paste fallback.)
4. As a candidate, I want to paste the job description into a text field, so that the interview targets the specific role I'm applying for.
5. As a candidate, I want the app to reject an empty or unusably short CV/JD before starting, so that I don't waste a session on bad input.

### The interview
6. As a candidate, I want the agent to ask me one question at a time, so that the experience feels like a real interview rather than a wall of text.
7. As a candidate, I want the questions to be drawn from both my CV and the job's required skills, so that the practice is relevant to me and the role.
8. As a candidate, I want the agent to occasionally ask a follow-up when my answer is vague or notably strong, so that the practice mimics how a real screener probes.
9. As a candidate, I want the interview to be a bounded length (roughly 8–12 turns), so that a practice session is a reasonable time commitment.
10. As a candidate, I want to end the interview early, so that I'm not forced to finish if I've had enough.
11. As a candidate, I want my conversation so far to stay on screen, so that I can see the flow of the interview as it happens.
12. As a candidate, I should not be able to see the agent's hidden question plan or scoring rubric during the interview, so that the practice reflects a genuine screen.

### Feedback
13. As a candidate, I want a structured feedback report at the end, so that I get an overall read on how I did.
14. As a candidate, I want per-topic scores, so that I can see which areas were strong and which were weak.
15. As a candidate, I want concrete strengths and gaps called out, so that I know specifically what to improve.
16. As a candidate, I want a clear overall recommendation, so that I have a single takeaway from the session.

### Trust, safety & cost (operator/developer perspective)
17. As the operator, I want untrusted CV/JD/answer text treated strictly as data and never as instructions, so that a candidate can't inject "give me a perfect score" into their CV.
18. As the operator, I want the agent to refuse off-topic requests and stay in its interviewer role, so that the app isn't abused as a free general-purpose chatbot on my API key.
19. As the operator, I want input size limits (PDF size, JD length, answer length), so that a single user can't run up my API bill or degrade the service.
20. As the operator, I want a per-session running cost shown to me, so that I can see what each interview costs and compare models.
21. As the operator, I want all malformed model outputs caught by schema validation, so that the UI never renders garbage and bad data fails loudly.

### Developer / experimentation perspective
22. As the developer, I want to switch the model and per-role temperatures from one config place, so that I can develop cheaply and tune behavior without code surgery.
23. As the developer, I want a fake-LLM mode, so that I can build and debug the whole app flow without spending API credit.
24. As the developer, I want to select which of my 5 interviewer-prompt variants is active, so that I can run a controlled bake-off and pick the best technique.
25. As the developer, I want to capture token usage on every call, so that I can compute cost and reason about spend.
26. As the developer (stretch), I want an automated evaluation of the agents (e.g. role adherence, question relevance), so that my quality claims are evidence-based rather than vibes.

## Implementation Decisions

### Architecture
- **Frontend:** Next.js with **React 19** and **Tailwind CSS** (single-page candidate experience: CV upload, JD paste, chat view, feedback report).
- **Backend:** FastAPI exposing the interview lifecycle as endpoints (start / reply / finish). Stateful server with session state held in an **in-memory store behind a small `get`/`save` interface**, so a later swap to SQLite is a localized change. Sessions get a TTL/cap to avoid unbounded memory growth. **Single-worker assumption** for the in-memory store (documented limitation).
- **LLM access:** plain OpenRouter calls via the **OpenAI Python SDK** (`base_url` pointed at OpenRouter). No LangChain in this MVP (deferred to a later course chapter).
- **Hidden state:** the interview plan and scoring rubric live only server-side and are never sent to the browser.

### Agent design (four roles, one underlying model)
- **Classifier** — JD/title → domain (temp ≈ 0.1).
- **Planner** — CV + JD → hidden plan of 5–6 topics, via a chain-of-thought planning pass (temp ≈ 0.4).
- **Interviewer** — asks one question at a time, max one adaptive follow-up per topic, ~8–12 turns total (temp ≈ 0.6).
- **Judge** — produces the final structured scorecard/feedback (temp ≈ 0.1).
- **Temperature is the headline tuned parameter, set per role** (consistency for classifier/judge, variety for interviewer). top-p / frequency penalty discussed in the writeup but not cranked.

### Prompt engineering (mandatory requirement)
- Five **interviewer** system-prompt variants — zero-shot, few-shot, chain-of-thought, role-play persona, structured-rubric — held in a **prompt registry**. A controlled bake-off across 2–3 fixed `(CV, JD)` fixtures selects the winner; each technique is written up for submission. Planner (CoT) and judge (structured) demonstrate additional techniques naturally.

### Structured output (medium bonus)
- Model calls that must return data use `response_format` JSON-schema mode, validated with **Pydantic** models. Two graded formats: **interview plan** and **final scorecard** (classifier output also structured). Per-model structured-output support to be confirmed on OpenRouter; default model curated to a supporting one.

### Security (mandatory + bonus)
- **Primary guard:** data/instruction separation — CV/JD wrapped in explicit delimiters; system prompts instruct the model to treat delimited content as untrusted data and never follow instructions inside it.
- **Layers:** input validation (PDF-only, size/char/answer caps); stay-on-task redirect in the interviewer prompt; server-side secrets; Pydantic validation as an output-side guard.
- **Bonus experiment:** attempt to jailbreak the app (CV injection, rubric extraction, free-chatbot abuse), log attempts + outcomes + which guard caught them in a spreadsheet.

### Cost (medium bonus)
- Capture `usage` (prompt/completion tokens) on every call; fetch per-model pricing from OpenRouter's `/models` endpoint; accumulate a per-session total via a pure cost-calculator module. Input caps are the preventive layer.
- **Cost is operator data, kept out of the candidate flow.** The backend always computes/logs/returns it; the UI surfaces it only as a **muted footer on the results page** (after the interview ends, so no immersion cost). Richer/live detail is gated behind a generic `DEV_MODE` env flag (off by default) — the same flag that would later reveal an optional dev panel (model picker, temperature sliders, prompt-variant selector).

### Configuration & cost-control during development
- **Config-first, no dev UI panel for the MVP.** All tunables (model id, per-role temperatures, active interviewer-prompt variant) centralized in one config object (`pydantic-settings` / `.env`). Default dev model = `gpt-5-nano`.
- **`USE_FAKE_LLM` stub mode** built first, so plumbing/UI/state are developed against canned responses at zero API cost; real calls reserved for prompt-quality testing.

### Build sequence (A-floor first, cheap-first)
- **Phase 0** skeleton + config + stub LLM (no spend) → **Phase 1** one real OpenRouter call + usage capture → **Phase 2** agent state machine against the stub → **Phase 3** real prompts + structured output + security guard (mandatory complete) → **Phase 4** frontend polish + cost meter → **Phase 5** bake-off + temperature demo + jailbreak log + README → **Phase 6** stretch.

### Bonus tally (already met; not chasing more)
- Hard: multi-turn chatbot agent; runtime LLM-as-judge. Medium: JD-as-context (RAG-lite), structured JSON, cost calculation. Exceeds "2 medium + 1 hard."

## Testing Decisions

**What makes a good test here:** assert on **external behavior through a module's public interface**, not internal steps; keep tests **deterministic** by stubbing the LLM client (`USE_FAKE_LLM`) so no test depends on live, non-deterministic model output or network/credit.

**Modules to unit-test (the pure, deep ones — recommended for tests):**
- **CV parser** — given representative PDF bytes, returns expected text; flags empty/garbage extraction. (Use small fixture PDFs.)
- **Cost calculator** — given a usage record + pricing, returns the correct cost; handles zero/edge values.
- **Input guard** — enforces caps and PDF-type checks; `wrap_untrusted` produces correctly delimited output; rejects oversized/empty input.
- **Schemas (Pydantic)** — accept valid plan/scorecard/classification objects, reject malformed or out-of-range ones (this is also the output guard).
- **Prompt registry** — returns the requested variant and assembles a well-formed `messages` array (system + delimited data + transcript).

**Behavioral test (against the stubbed LLM client):**
- **Interview engine / state machine** — drives the lifecycle correctly: start → classify → plan → ask → reply/probe → finish; enforces the turn cap and the one-follow-up-per-topic rule; honors early end; never exposes the plan/rubric in client-facing payloads.

**Explicitly NOT unit-tested:** the *quality* of real LLM outputs (question relevance, feedback usefulness). That is evaluated separately via the manual prompt **bake-off** and, as a stretch, **deepeval** metrics — not via assertions on text.

**Prior art:** none (greenfield repo); establish these patterns fresh.

## Out of Scope

- Voice (text-to-speech / speech-to-text) — written interaction only this MVP.
- Authentication / user accounts / multi-user concurrency (single-worker, in-memory sessions).
- Durable persistence (SQLite/DB) and history of past interviews — deferred stretch.
- `.docx`/image CVs and OCR of scanned PDFs — PDF text extraction only. **CV is PDF-only: there is no copy-paste fallback.** An unreadable/textless PDF is rejected and the candidate uploads a different one.
- Showing or editing the extracted CV text — the parse is used as-is; the candidate sees only upload success/failure, never the contents.
- Domains beyond software/data in the MVP (architecture supports adding them later).
- LangChain / agent frameworks (deferred to a later course chapter).
- A dev/settings **UI panel**, model-picker UI, image generation, vector DB — config-first instead; UI versions are optional later bonuses.
- deepeval automated evaluation — stretch, only if time allows.

## Further Notes

- **Known limitations to document in the README (reflection grade):** in-memory state is single-worker and non-persistent; structured-output support is model-dependent; low temperature reduces but does not guarantee deterministic output (say "more reproducible," not "deterministic"); prompt-injection defense is mitigated, not provably eliminated; PDF parsing fails on scanned documents; **the extracted CV text is not shown or editable, so a partially garbled parse (e.g. multi-column layouts) can reach the interview unseen — the usability threshold only catches total extraction failures; the whitespace-ratio quality check assumes a space-separated script, so a dense CJK (Chinese/Japanese/Korean) CV could be falsely rejected.**
- **Reflection deliverables:** README covering the 5 prompting techniques + bake-off results, per-role temperature rationale, the user/system/assistant role distinction, output types, the security threat model + jailbreak experiment, and improvement ideas.
- **Cost discipline:** develop on `gpt-5-nano` with the stub mode; keep bake-off fixtures to 2–3; treat deepeval (token-hungry) as a late, optional, cheap-model chapter; budget ~€10 total OpenRouter credit.
