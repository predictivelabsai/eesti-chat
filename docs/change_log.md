# Change Log

## v1.3.0 — 2026-10-13

**Public MCP server for Estonian open data, verified in Claude Code, Claude.ai and ChatGPT.**

- `mcp_server/` serves 15 read-only tools (companies, EMTA tax data, Riigi Teataja, In-ADS, Statistics Estonia, procurement, weather, exchange rates, Sõnaveeb, andmed.eesti.ee, official web search) at `https://mcp.eesti.chat/mcp`, with anonymous and API-key tiers. See `docs/mcp_server.md`.
- The home page Developers section documents the endpoint, a terminal-style install block, per-client setup tabs, the tool list and rate limits.
- Added `docs/linkedin_mcp.md`, the LinkedIn announcement draft for the MCP server, and `screenshots/` with the developers section, connector setup in Claude.ai and ChatGPT, live answers from both, a Claude Code run, and `mcp_tour.gif`.

## v1.2.2 — 2026-10-12

**Smaller database pool.**

- The engine keeps at most 2 connections plus 3 overflow (was 5 + 10), recycles them after 5 minutes, and names itself `eesti-chat` in Postgres (`DB_APPLICATION_NAME` overrides). The Postgres server is shared and was near its connection limit.

## v1.2.1 — 2026-10-10

**Footer link to Agentic State, and voice that answers after you speak.**

- The public footer and the chat sidebar now link to [Agentic State](https://agenticstate.org) under the Predictive Labs credit.
- Voice no longer waits on the model’s default high reasoning. If the server does not hear the end of a turn, the browser commits the microphone audio after a short silence so a reply still starts. The spoken line is shown in the voice panel as well as played.
- The home page prompt and the floating ask bar have a microphone. Tapping it starts the same voice conversation.

## v1.2.0 — 2026-10-10

**Talk to eesti.chat: a voice mode on the same xAI key.**

- A microphone button on the chat composer opens a live voice conversation. The browser streams PCM16 audio to `/ws/voice`, which proxies it to xAI speech-to-speech with `XAI_API_KEY`. The spoken voice is `eve` (override with `XAI_VOICE`).
- The voice agent uses a short spoken prompt for Estonian public services, searches the web for current figures, and writes the transcript into the chat. Typed chat is unchanged.
- Anonymous visitors who have already used their free questions cannot start voice. The privacy page notes that microphone audio goes to xAI.

## v1.1.0 — 2026-10-08

**New "Elections 2027" assistant plus on-demand charts of official Estonian statistics.**

- Added a seventh specialist assistant, **Elections 2027**, in its own sidebar category and
  home topic card. It is a neutral, non-partisan guide to the 7 March 2027 Riigikogu election:
  the main parliamentary parties (Reform, Eesti 200, EKRE, Centre, SDE, Isamaa), their AI /
  digital-state strategies, how they propose to balance the state budget, and the common
  patterns where platforms converge. Seeded starter questions cover all three themes.
- New system prompt (`prompts/system/elections.md`) enforces balance, source citation, and
  comparison tables; `web_search` grounding now allowlists the national election authority
  (valimised.ee) and the six parties' official sites.
- **On-demand data visualisation** (`make_chart` tool): the Elections assistant can chart live
  official data from Statistics Estonia (stat.ee PxWeb API) — government debt & surplus/deficit
  as % of GDP (`RR061`), GDP per capita (`RAA0013`), inflation (`IA001`), population (`RV021`)
  and unemployment (`TT0151`). Figures are built server-side with Plotly and streamed to the
  results panel via the existing `__ARTIFACT__` → `artifact_show` pipeline (Plotly.js on the CDN,
  `Plotly.newPlot` client-side), mirroring the kaljuvee-chat streaming pattern.
- New sidebar official links: Bank of Estonia (eestipank.ee), Statistics Estonia (stat.ee),
  and an "Elections 2027" block (valimised.ee + the six party sites).
- Localised the new assistant/category names and one-liners across all nine languages; home
  section heading updated to "Seven specialist assistants".
- Added `plotly` to requirements.

## v1.0.3 — 2026-10-01

**Add visitestonia.com to the official links in the chat sidebar.**

- New sidebar link: visitestonia.com (official tourism), alongside eesti.ee, eesti.ai,
  e-resident.gov.ee, rik.ee, emta.ee, ria.ee and err.ee.

## v1.0.2 — 2026-10-01

**Full UI localization for all nine languages — German, French, Swedish, Russian, Finnish, Latvian and Lithuanian now render natively (no more English fallback).**

- Translated the entire UI catalog (nav, hero, features, how-it-works, footer, chat,
  suggestions, the six assistant names/descriptions and four categories) into de, fr, sv,
  ru, fi, lv, lt — alongside the existing en and et.
- Translations now live in per-language `locales/<lang>.json` files, merged into the catalog
  at import by `_merge_locales()`; en + et remain inline. Easy to extend/edit going forward.
- Combined with IP geolocation (v1.0.1): a visitor from Sweden now sees Swedish, Germany
  German, etc., and the language switcher shows fully localized pages.

## v1.0.1 — 2026-10-01

**IP-based language defaulting — Estonian from an Estonian IP, each language from its own country, English everywhere else.**

- New `utils/geo.py`: layered IP→country detection (CDN country headers → ipapi.co / ip-api.com →
  emergency EE prefixes), stdlib-only, cached per IP, skips private IPs, short timeout, never blocks render.
- Country→language map: EE→et, RU→ru, DE/AT→de, FR→fr, SE→sv, LV→lv, FI→fi, LT→lt; anything else → English.
- A beforeware now sets the session language from the visitor's IP on first visit (a manual language
  choice always takes precedence). Previously the IP detection code never actually ran.

## v1.0.0 — 2026-10-01

**First versioned release of eesti.chat — the AI front door to Estonia.**

- AI chat portal with six specialist assistants (e-Residency & company, living & moving,
  taxes & finance, digital ID & e-services, public services, discover Estonia). Answers are
  grounded in official Estonian sources via live search and always cite their links, in the
  user's selected language.
- Access: 5 free questions, then Google SSO or email sign-up. Chat history persists for both
  guests and signed-in users (and recovers gracefully from stale sessions).
- Context-sensitive follow-up suggestion chips under the composer — starters by default and
  tailored follow-ups after each answer, so the user is never stuck.
- Working indicator rotates playful "thinking" synonyms per language; underlying tool calls
  (e.g. web search) are never surfaced in the UI.
- Official links in the sidebar: eesti.ee, eesti.ai, e-resident.gov.ee, rik.ee, emta.ee,
  ria.ee, err.ee.
- "Powered by Predictive Labs OÜ" and the app version shown near sign-in (version links here).
- White / black / Estonia-blue design in the Aino typeface; English + Estonian; live at
  https://eesti.chat. Inspired by america.gov and the U.S. State Department's ShareAmerica.
