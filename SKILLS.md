# eesti.chat development guide

eesti.chat is a FastHTML application that gives people a conversational front door to Estonian public services. Specialist LangGraph agents use the `tools/search.py` Exa integration to ground answers in official Estonian sources.

## Local development

Create an environment and install the pinned dependencies:

```bash
uv venv && uv pip install -r requirements.txt
# or: python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set the provider/search credentials you want to use. The important settings are:

- `XAI_API_KEY` or `OPENAI_API_KEY` with `LLM_PROVIDER=openai`
- `EXA_API_KEY` for grounded web search
- `DB_URL` for persisted chat history, authentication, profiles, and admin features
- `APP_SECRET` for FastHTML sessions; production should always set it
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for Google sign-in
- `POSTMARK_API_TOKEN`, `FROM_EMAIL`, `FROM_NAME`, and `SERVICE_URL` for account and contact email flows
- `PORT` (default `5011`) and `LOGIN` for local behavior

Run the app with:

```bash
python main.py
```

The web app is available at `http://localhost:5011`. The FastAPI surface is mounted at `/api/v1`; its interactive docs are at `/api/v1/docs` when the API dependencies and database are available.

## Repository map

- `main.py` — FastHTML entry point and port `5011` server
- `pages/` — public home, about, contact, privacy, and account-deletion pages
- `chat/` — chat page, session history, and SSE streaming routes
- `agents/` — specialist public-service agents and routing
- `tools/search.py` — Exa web search tool used by all agents
- `auth/` — email/password, verification, reset, Google OAuth, and profile routes
- `api/` — optional FastAPI auth, chat, session, profile, contact, and deletion endpoints
- `admin/` — invitation and user administration
- `db.py` — PostgreSQL connection and portal/chat table initialization
- `static/` — shared CSS, chat JavaScript, manifest, and favicon

## Tests

Run the full suite:

```bash
pytest -q
```

Useful focused runs:

```bash
pytest tests/test_legal_pages.py -q
pytest tests/test_account_deletion.py -q
pytest tests/test_email.py -q
pytest tests/test_api.py -q
```

The API tests expect a running API with a configured PostgreSQL database. Set `API_BASE` when it is not available at the default URL. Email delivery integration is skipped unless `POSTMARK_API_TOKEN` is set and the `--run-integration` option is supplied.

Before opening a review, compile every Python file without importing application dependencies:

```bash
python -m compileall -q .
```

## Docker and Coolify

Build and run locally with the supplied files:

```bash
docker compose up --build
```

The container listens on port `5011` and reads runtime settings from the environment. The compose file passes the database, LLM, Exa, auth, email, service URL, and port settings through to the web container. The health endpoint is `/health`.

For Coolify, deploy this repository as a Docker application using `Dockerfile`, expose container port `5011`, and configure the same variables from `.env.example` in the service environment. Set `APP_SECRET`, database credentials, OAuth secrets, and email credentials as production secrets. The container health check calls `/health`.

## Database

`DB_URL` is optional for anonymous, non-persisted chat. When configured, `init_db()` creates the `eesti` schema and the account, chat session, message, profile, and invitation tables. `sql/schema.sql` is the corresponding reference schema and `sql/schema.json` documents those tables.

Do not put secrets in source control. Keep `.env` and deployment credentials in the environment or the platform's secret store.

## Product behavior

The public chat supports English and the language choices exposed by the language switcher. Agents should use official `.ee` sources for factual or procedural answers and include the source links in their response. Keep prompts and user-facing copy aligned with Estonia's public-service portal; avoid introducing unrelated product domains or unsupported claims.
