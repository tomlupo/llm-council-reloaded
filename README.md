# LLM Council Plus

Multi-LLM council with Ask, Debate, Decide, Minmax, and Brainstorm modes. Each model responds independently; peer review and chairman synthesis produce a final answer.

## Quick start

### 1. Install and run backend

```bash
# From project root
uv sync   # or: pip install -e .
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Install and run frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown (e.g. http://localhost:5173).

### 3. Configure models

- **Settings** (gear icon): add/edit models, enable/disable, set API keys.
- Council needs **at least 2 enabled models**.

## Using the council

1. Pick a **mode**: Ask, Debate, Decide, Minmax, Brainstorm.
2. For **Decide** and **Minmax**: enter options (comma-separated) and optionally criteria.
3. For **Debate**: optionally set rounds.
4. For **Brainstorm**: optionally set style (wild / practical / balanced).
5. Type your question/topic and send. The council runs in the background; the final synthesis appears when done.

## Models: CLI vs API (no API key with CLI)

For **OpenAI**, **Google**, and **Anthropic** the app tries the **CLI first** (no API key needed). If the CLI is missing or fails, it falls back to the **HTTP API** (API key required).

| Provider   | CLI (no key) | Fallback API (key)   |
|-----------|--------------|----------------------|
| OpenAI    | `codex`      | `OPENAI_API_KEY`     |
| Google    | `gemini`     | `GOOGLE_API_KEY`     |
| Anthropic | `claude`     | `ANTHROPIC_API_KEY`  |
| DeepSeek  | —            | `DEEPSEEK_API_KEY`   |

**Using CLIs (no API key):**

1. Install the CLI and ensure it’s on your PATH:
   - **Codex**: [Codex CLI](https://github.com/openai/codex-cli) — `codex exec ...`
   - **Gemini**: [Gemini CLI](https://github.com/google-gemini/gemini-cli) — `gemini ...`
   - **Claude**: [Claude Code CLI](https://docs.anthropic.com/en/docs/build-with-claude/claude-code) — `claude ...`
2. Do **not** set the corresponding API key in Settings (or leave it empty).
3. When you run a council, the app will call the CLI for that provider; no key is used.

**Using APIs (API key):**

1. Put keys in `.env` or in Settings:
   - `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`
2. If the CLI is not installed or fails, the app automatically uses the API with these keys.

So: **use the CLIs for no API key**, or **set the env vars** to use the APIs (and as fallback when CLI fails).

## Modes

- **Ask**: Each model answers; peer review; chairman synthesis. (Execution mode can limit to chat-only or ranking.)
- **Debate**: Opening statements, rebuttals, peer evaluation, chairman verdict.
- **Decide**: Options + criteria → per-model scores and recommendation → chairman recommendation.
- **Minmax**: Same options/criteria as Decide; models score under worst-case assumptions → chairman picks the option that maximizes the minimum outcome.
- **Brainstorm**: Rounds of ideas and cross-pollination → chairman synthesis into themes and next steps.

## Config and settings

- **Settings file**: By default, settings are loaded and saved from `backend/data/settings.json` (created on first run). You can edit models and defaults there or via the Settings UI.
- **Custom config path**: Set `COUNCIL_SETTINGS_PATH` in `.env` to use a different file (e.g. `config/settings.json`). Same idea as `.env` for env vars: one place to point to the config file. Copy `config/settings.json.example` to `config/settings.json` and set `COUNCIL_SETTINGS_PATH=config/settings.json` in `.env` to keep config in `config/`.
- **Secrets**: API keys go in `.env` (see `.env.example`) or are entered in the Settings UI; the settings JSON only stores the env var names (e.g. `OPENAI_API_KEY`), not the keys themselves.

## Development

- Backend: `uv run uvicorn backend.main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`

## Inspirations

- **Idea**: [karpathy/llm-council](https://github.com/karpathy/llm-council) — multi-LLM council that collects first opinions, peer review, and chairman synthesis.
- **Frontend**: [jacob-bd/llm-council-plus](https://github.com/jacob-bd/llm-council-plus) — multi-LLM council with Ask, Debate, Decide, Minmax, and Brainstorm modes.
