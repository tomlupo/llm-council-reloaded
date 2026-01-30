# TASKS.md

Proposed and tracked improvements for LLM Council Plus. Pick items as needed; order is rough priority.

---

## Testing

- [ ] **Backend tests** – Add pytest (or similar), test API endpoints (conversations CRUD, settings, model catalog), mock LLM calls for pipeline tests.
- [ ] **Frontend tests** – Add Vitest (or Jest) and test critical flows: create conversation, send message, mode switch, settings load/save.
- [ ] **E2E** – Optional Playwright (or similar) for: start council, send message, see synthesis.

---

## API and error handling

- [ ] **Frontend API** – In `api.js`, check `response.ok` before `response.json()`; surface HTTP errors (e.g. 404, 500) to the user instead of failing silently or throwing on parse.
- [ ] **Structured API errors** – Backend: return consistent error payloads (e.g. `{ "error": "code", "message": "..." }`) for 4xx/5xx so the frontend can show them.
- [ ] **Settings validation** – Validate `PUT /api/settings` (required fields, model IDs, env var names) and return 400 with clear messages on invalid input.

---

## Security and production readiness

- [ ] **CORS** – Replace `allow_origins=["*"]` with a configurable list (e.g. from env) for production.
- [ ] **Secrets** – Ensure API keys from Settings UI are never logged or echoed in API responses.
- [ ] **Rate limiting** – Optional: add rate limiting on `/api/conversations/.../messages` to avoid abuse.

---

## Data and repo hygiene

- [ ] **Runtime data** – Either add `backend/data/` (or `backend/data/conversations/`) to `.gitignore` so local conversations/settings aren’t committed, or document that `backend/data/` is local-only and should not be committed.
- [ ] **Settings path** – Align README and code: README mentions `backend/data/settings.json` and `COUNCIL_SETTINGS_PATH`; ensure one source of truth and document it.

---

## UX and frontend

- [ ] **Loading and errors** – Clear loading state while council is running; show stream/API errors in the UI (toast or inline) with retry where it makes sense.
- [ ] **Stream retry** – On SSE disconnect or error, offer “Retry” instead of only showing a generic error.
- [ ] **Keyboard shortcuts** – e.g. Send on Enter (with Shift+Enter for newline), focus search in Settings.
- [ ] **Accessibility** – Basic a11y: focus management, aria labels for mode selector and main actions, sufficient contrast.

---

## Developer experience

- [ ] **Run script** – In `run_app.sh`, optional flag to skip `uv sync` / `npm install` for faster restarts when deps are already installed.
- [ ] **Env check** – Optional: script or startup check that required env (or CLI) is available and at least two models are enabled, with a clear message if not.
- [ ] **API docs** – Document in README that OpenAPI is at `/docs` (FastAPI); optionally add a short “API” section with main endpoints and request/response shapes.

---

## Code quality and consistency

- [ ] **TypeScript** – Consider migrating frontend to TypeScript (or adding JSDoc types) for safer refactors and better editor support.
- [ ] **Backend types** – Ensure Pydantic models and function signatures are strict; add type hints where still missing.
- [ ] **Logging** – Structured logging (e.g. per request or per conversation) for debugging and optional production monitoring.

---

## Features (optional)

- [ ] **Export** – Export a conversation (or thread) as Markdown or JSON.
- [ ] **Conversation title** – Auto-generate or let user set a title so the sidebar is easier to scan.
- [ ] **Web search** – `web_search` is in the request model; wire it through pipelines and UI if desired.

---

*Edit this file as items are done or new ideas are added.*
