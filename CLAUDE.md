# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Generic repository rules for every coding agent are in `AGENTS.md`. This file adds the Claude Code workflow and a fuller picture of the request path.

# eesti.chat

Conversational front door to Estonian public services (e-Residency, taxes, digital ID, moving, services, the 2027 Riigikogu election). Independent project, not a government service. FastHTML UI, LangGraph ReAct agents, xAI Grok or OpenAI, Exa grounding, optional PostgreSQL.

Longer setup notes live in `SKILLS.md` and `README.md`. Product intent is `PRODUCT.md`. Visual tokens are `DESIGN.md`.

## Commands

```bash
uv venv && uv pip install -r requirements.txt   # or: pip install -r requirements.txt
cp .env.example .env                             # XAI_API_KEY (or OPENAI_API_KEY + LLM_PROVIDER=openai), EXA_API_KEY
python main.py                                   # http://localhost:5011
pytest -q                                        # offline tests
pytest tests/test_legal_pages.py -q              # one file
pytest tests/test_api.py -q                     # needs a running API + PostgreSQL; API_BASE overrides the default URL
pytest -q --run-integration                      # Postmark/DB tests; email ones also need POSTMARK_API_TOKEN
python -m compileall -q .                        # syntax check without importing the app
docker compose up --build                        # container on 5011, health at /health
```

`python -m api.app` runs the FastAPI layer alone. When mounted by `main.py`, docs are at `/api/v1/docs`.

## Architecture

`main.py` builds one FastHTML app (port `PORT`, default 5011) and registers four route groups: public pages (`pages/`), chat (`chat/routes.py`), auth (`auth/routes.py`), admin (`admin/routes.py`). It mounts `/static` and, if FastAPI imports, `/api/v1`. Startup calls `db.init_db()`, which is a no-op without `DB_URL`. Anonymous chat works with no database.

A question posted to `POST /app/chat` is streamed back as SSE.

1. Rate limit (per IP, 60s window: `RATE_LIMIT_ANON` / `RATE_LIMIT_AUTH`) and a free-question gate (`FREE_QUERIES`, default 5) run before the stream starts, so the session cookie can still be written.
2. `agents/router.py` picks a slug: `prefix:` on the message, then keyword scores, then an LLM classifier. Unknown or failed classification falls through to `explore`. `strip_prefix` removes the prefix before the agent sees the text.
3. `agents.base.cached_agent` imports `agents.{category}.{slug}` and calls `build()`. The module path comes from `AgentSpec.category` and `AgentSpec.slug` in `agents/registry.py`. Adding an assistant means a registry entry, a module at that path with `build()`, a prompt file, and router keywords.
4. `build_agent` loads `prompts/shared/estonia_context.md` plus `prompts/system/{slug}.md` and calls `create_react_agent`. Every assistant gets `tools/search.py` (`web_search`, Exa, `OFFICIAL_DOMAINS`). The elections assistant also gets `tools/charts.py` (`make_chart`).
5. `utils/llm.py` uses `langchain_openai.ChatOpenAI`. Default provider is xAI (`XAI_BASE_URL`, `GROK_MODEL`). `LLM_PROVIDER=openai` switches `build_llm`. Agent calls prefer `XAI_AGENT_MODEL` when set.

Voice is separate from that stack. The composer mic opens `/ws/voice` (`voice.py`), a server-side proxy to `wss://api.x.ai/v1/realtime` that reuses `XAI_API_KEY` and speaks with `XAI_VOICE` (default `eve`). `static/voice.js` sends PCM16 at 24 kHz. The voice prompt is short and spoken; it is not the typed system prompts.

The same agent stack backs `POST /api/v1/chat`. Web session state is a FastHTML session cookie (`APP_SECRET`). Saved users, sessions, messages, feedback, profiles, and invites live in the Postgres schema `DB_SCHEMA` (default `eesti`) — see `db.py` and `sql/schema.sql`. Auth is email/password plus Google OAuth (`auth/`) and JWT on the API (`api/auth.py`). Email goes through Postmark (`utils/email.py`).

UI copy is `utils/i18n.py`. English and Estonian are inline; `ru`, `de`, `fr`, `sv`, `lv`, `fi`, `lt` merge from `locales/*.json` at import, and missing keys fall back to English. First visit sets the language from IP country (`utils/geo.py`). `/set-lang/{code}` overrides it.

Public pages and the `/app` workspace are server-rendered FastHTML. `static/chat.js` drives the chat client (streaming, panes, share). `static/app.css` and `static/tw.css` are the styles. Brand assets are `static/brand/`. The wordmark stays lowercase. Do not imitate the official Brand Estonia logo.

`LOGIN` only toggles the public nav's sign-in affordance (`components/layout.py`). The free-question gate is separate and always on for anonymous visitors.

## Versioning and cache bust

`VERSION` is the source of truth: line 1 semver, line 2 ISO date (`utils/version.py`). `chat.js` and `app.css` load with `?v={app_version()}`. `marked.min.js` is still pinned at `?v=1`; bump that string when that file changes.

Every change that gets pushed must bump `VERSION` and prepend `docs/change_log.md` in the same commit. Format: newest first, `## vX.Y.Z — YYYY-MM-DD`, a bold one-line summary, then bullets. Stamp with today's UTC date (`date -u +%Y-%m-%d`). The version is shown near sign-in and in the home footer, linking to `/changelog`.

## Workflow

Delegate repo work to Codex by default. This applies to writing, editing, analysis, refactoring, docs, config, and data files in the working tree.

When the user gives a task:

1. Turn it into a scoped prompt. Do not show the prompt.
2. Delegate via the Codex MCP tool `spawn_agent` (or `spawn_agents_parallel` for independent tasks).
3. Codex does the work. Review the result and re-delegate if it is wrong.
4. Report a short summary. Do the work yourself only when it is out of Codex's reach, and say why.

Codex runs only in the repo and only has local tools. It cannot use web search, Gmail, Drive, Calendar, Canva, image generation, or create artifacts. Keep those tasks.

Never add AI attribution anywhere: no `Co-Authored-By` trailer on commits, no "Generated with" lines in PRs, commits, or docs, and no AI tools listed as contributors.
