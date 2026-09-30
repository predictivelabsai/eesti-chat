# eesti.chat

Conversational AI portal to Estonia (e-Residency, taxes, digital ID, moving, services).
Python: FastHTML UI, LangGraph + xAI Grok/OpenAI, Exa grounding, optional PostgreSQL.

## Global workflow

## Delegate to Codex by default
I plan and write prompts. Codex executes. This applies to all task types, not just code: writing, editing, analysis, refactoring, docs, config, data files, and anything that lives in the repo working directory.

When the user gives a task:
1. I turn it into a scoped prompt. I do not show the prompt.
2. I delegate it to Codex via the codex MCP tool spawn_agent (or spawn_agents_parallel for independent tasks).
3. Codex does the work in the repo. I review its result and re-delegate if it is wrong.
4. I report a short summary. I do not do the work myself unless it is out of Codex's reach.

## When I keep a task instead of delegating
Codex runs only in the repo directory and only has local tools. It cannot use web search, Gmail, Drive, Calendar, Canva, image generation, or create artifacts. If a task needs any of those, I do it myself and say why I did not delegate.

## No AI attribution
Never add AI attribution anywhere in repos or docs: no "Co-Authored-By: Claude" (or any other AI) trailer on commits, no "Generated with Claude Code" (or similar) in PR descriptions, commits, or docs, and no AI tools listed as contributors anywhere. This applies to all task types, including work done by Codex on my behalf.

## Notes
- Serve locally with `python main.py` (port 5011); needs `.env` with `XAI_API_KEY` (or `OPENAI_API_KEY` + `LLM_PROVIDER=openai`), `EXA_API_KEY`, optional `DB_URL`.
- JS/UI changes are cache-busted via `?v=` query strings in templates (see recent commits) — bump those when editing frontend JS.