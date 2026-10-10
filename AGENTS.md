# Repository Guidelines

Rules for any coding agent in this repo. `CLAUDE.md` adds the Claude Code workflow. Setup detail is in `SKILLS.md` and `README.md`. Product intent is `PRODUCT.md`. Visual tokens are `DESIGN.md`.

eesti.chat is an independent conversational front door to Estonian public services. It is not a government service. Do not imply an official affiliation or imitate the Brand Estonia logo. The wordmark stays lowercase.

## Project Structure & Module Organization

`main.py` is the FastHTML entry (port `PORT`, default 5011). It registers public pages (`pages/`), chat (`chat/`), auth (`auth/`), and admin (`admin/`), mounts `/static`, and mounts `/api/v1` when FastAPI imports. `python -m api.app` runs that API alone; mounted docs are `/api/v1/docs`.

Specialist assistants live under `agents/`. `agents/registry.py` is the catalog. `agents/router.py` picks a slug. Each assistant is `agents/{category}/{slug}.py` and must export `build()`. System prompts are `prompts/shared/estonia_context.md` plus `prompts/system/{slug}.md`. Shared tools are `tools/` (Exa search; the elections assistant also charts).

`db.py` and `sql/` own Postgres (schema `DB_SCHEMA`, default `eesti`). The app runs without `DB_URL`: anonymous chat works, saved history and login do not. UI strings are `utils/i18n.py` (English and Estonian inline; other languages in `locales/*.json`). Browser assets are `static/`. Tests are `tests/`.

Voice is a separate path from the typed agents. `static/voice.js` captures the mic and talks to `/ws/voice`. `voice.py` proxies that socket to xAI speech-to-speech (`grok-voice-latest`) with `XAI_API_KEY`. The voice name defaults to `eve` (`XAI_VOICE`). Do not put the API key in the browser.

## Build, Test, and Development Commands

```bash
uv venv && uv pip install -r requirements.txt   # or: pip install -r requirements.txt
cp .env.example .env                             # XAI_API_KEY or OPENAI_API_KEY + LLM_PROVIDER=openai; EXA_API_KEY
python main.py                                   # http://localhost:5011
pytest -q                                        # offline tests
pytest tests/test_legal_pages.py -q              # one file
pytest tests/test_api.py -q                     # needs a running API and PostgreSQL; API_BASE overrides the URL
pytest -q --run-integration                      # Postmark and DB tests; email ones also need POSTMARK_API_TOKEN
python -m compileall -q .                        # syntax check without importing the app
docker compose up --build                        # container on 5011; health at /health
```

## Coding Style & Naming Conventions

Python, four-space indentation, `snake_case` for modules and functions, `PascalCase` for classes. No formatter or linter is configured; match the surrounding file. Keep route handlers thin and page markup in `pages/` or `chat/`. Add a specialist by registering an `AgentSpec`, adding `agents/{category}/{slug}.py` with `build()`, adding `prompts/system/{slug}.md`, and adding router keywords. The import path is `agents.{category}.{slug}`.

## Testing Guidelines

Pytest discovers `tests/test_*.py`. `tests/conftest.py` puts the repo root on `sys.path` and loads `.env`. Prefer offline tests. Integration tests are opt-in via `--run-integration`. API tests expect a live server and database. New behavior gets a focused test in an existing file when one already covers that surface.

## Commit & Pull Request Guidelines

History uses short imperative subjects (`Add message feedback…`, `Release v1.0.3: …`). One concern per commit. Do not commit or push unless asked.

Every change that gets pushed bumps `VERSION` (line 1 semver, line 2 ISO date) and prepends `docs/change_log.md` in the same commit. Newest first: `## vX.Y.Z — YYYY-MM-DD`, a bold one-line summary, then bullets. Stamp with `date -u +%Y-%m-%d`. `utils/version.py` reads that file. `chat.js` and `app.css` load with `?v={app_version()}`. `marked.min.js` is pinned at `?v=1`; change that string when that file changes.

## Security & Configuration

Copy variable names from `.env.example`. Never commit or log secret values. Required for a grounded chat: `XAI_API_KEY` (or `OPENAI_API_KEY` with `LLM_PROVIDER=openai`) and `EXA_API_KEY`. `APP_SECRET` signs the session cookie. `DB_URL` is optional.

`LOGIN` only shows or hides the public nav sign-in link. Anonymous visitors still hit the free-question gate (`FREE_QUERIES`, default 5) on `POST /app/chat`. The rate limit and that gate run before the SSE stream starts.

Routing order is prefix (`business:`, `move:`, `tax:`, `gov:`, `id:`, `estonia:`, `vote:`), then keyword scores, then an LLM classifier. A failed classify falls through to `explore`.
