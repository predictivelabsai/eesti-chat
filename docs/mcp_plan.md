# eesti.chat MCP server — plan

Status: **plan only, nothing implemented yet**. Author: Julian Kaljuvee. Written 2026-10-11.

## 1. Where the repo is today

- **Stack:** Python 3.12, FastHTML UI + optional FastAPI mobile API (`api/`), LangGraph multi-agent ReAct (6 specialist agents + router in `agents/`), xAI Grok via `langchain-openai` (OpenAI fallback), PostgreSQL via SQLAlchemy (optional), Postmark email, Google OAuth. Served by `main.py` on port 5011.
- **Deployment:** `Dockerfile` (python:3.12-slim, `/health` healthcheck) + `docker-compose.yaml` labelled `coolify.managed=true`. `.github/workflows/deploy.yml` calls a Coolify webhook on every push to `main`. Live domain: **https://eesti.chat** (README / `SERVICE_URL`).
- **Tools and data sources:** just one tool, `tools/search.py::web_search`. It runs Exa search, limited by default to about 25 official domains (eesti.ee, emta.ee, rik.ee, riigiteataja.ee, stat.ee …).
- **Gov APIs already used:** **none**. Every government fact comes from Exa web search over gov websites. The MCP server would add structured, citable government data for the first time.

## 2. Estonian government APIs and open data: what we found

Checked with `curl` from the box on 2026-10-11. "✅" = endpoint answered with the expected format. "⚠️" = reachable but the guessed path was wrong or it is download-only. "❌" = not reachable or not public.

| # | Source | Base URL | Auth | Format | Rate limits | Licence | Verified |
|---|---|---|---|---|---|---|---|
| 1 | Open data portal (avaandmed) | `https://avaandmed.eesti.ee/api/datasets` | none (key only for publishing) | JSON REST | not published; keep it modest | per dataset, mostly CC BY 4.0 | ✅ 200 JSON (`/api/dataset-search` 404, so we need to read the OpenAPI spec) |
| 2 | e-Business Register: autocomplete | `https://ariregister.rik.ee/est/api/autocomplete?q=` | none | JSON | undocumented, used by the website | RIK terms | ✅ 200 JSON |
| 3 | e-Business Register: open data dumps | `https://avaandmed.ariregister.rik.ee/sites/default/files/avaandmed/ettevotja_rekvisiidid__{lihtandmed.csv,yldandmed.json,registrikaardid.xml,…}.zip` | none | CSV/JSON/XML zip, updated daily | n/a (bulk) | CC BY 4.0 | ✅ 206 zip |
| 4 | e-Business Register XML/SOAP services (detail, persons, annual reports) | `https://ariregxmlv6.rik.ee/` | contract + username/password, **paid** per query | SOAP XML | contract based | commercial | not tested (paid) |
| 5 | Riigi Teataja (legislation) | `https://www.riigiteataja.ee/api/oigusakt_otsing/1/otsi` and `/akt/{id}.xml` | none | JSON search; act XML | not published | public legal texts | ✅ search JSON; `.xml` answered `text/html` (probably needs a header or a different path; to check) |
| 6 | Maa- ja Ruumiamet, address search (In-ADS gazetteer) | `https://inaadress.maaamet.ee/inaadress/gazetteer?address=` | none | JSON | fair use | CC BY 4.0 (ADS) | ✅ returns structured address and coordinates |
| 7 | Maa- ja Ruumiamet WMS/WFS | `https://kaart.maaamet.ee/wms/alus`, `https://gsavalik.envir.ee/geoserver/ows` | none | OGC WMS/WFS XML, GeoJSON | fair use | CC BY 4.0 | ✅ both GetCapabilities; `teenus.maaamet.ee/ows/wms-ky` gave an HTML error |
| 8 | X-GIS / Geoportal | `https://xgis.maaamet.ee/` | none | web app (it uses the WMS/WFS above) | n/a | — | ⚠️ 302 (UI only) |
| 9 | Statistics Estonia PxWeb | `https://andmed.stat.ee/api/v1/{en,et}/stat/...` | none | JSON / JSON-stat / CSV (PxWeb POST query) | PxWeb default, about 30 requests per 10 s and a cell cap per query | CC BY 4.0 | ✅ 200 JSON table tree |
| 10 | EMTA (tax board) open data | `https://www.emta.ee/.../statistika-ja-avaandmed` → files on `ncfailid.emta.ee/s/.../download/*.csv` | none | CSV/XLSX, quarterly (taxes paid, turnover, employees per company), tax-debtor list | n/a | open data | ✅ page plus CSV links; the old debtor zip path returns 404, so we need the new link |
| 11 | Public procurement register (RHR) open data | `https://riigihanked.riik.ee/rhr/api/public/v1/opendata/notice/{yyyy}/month/{m}/xml` | none | eForms XML | not published | open data | ✅ 200 (bare `/opendata` gives 500) |
| 12 | Ilmateenistus (weather) | `https://www.ilmateenistus.ee/ilma_andmed/xml/{observations.php,forecast.php?lang=eng}` | none | XML | fair use | CC BY 4.0 | ✅ both 200 XML |
| 13 | Transpordiamet / Tark Tee (traffic, road weather) | `https://tarktee.ee/`, DATEX II feeds | DATEX may need registration | HTML / DATEX II XML | — | — | ⚠️ website 200; guessed `tarktee.mnt.ee/api` timed out; vehicle and driving-licence queries go through X-tee or eesti.ee |
| 14 | Eesti Pank | statistics website and exchange rates | none | XML/CSV export | — | open | ⚠️ guessed export URLs 404; plan to use ECB `eurofxref-daily.xml` (✅ 200), which Eesti Pank mirrors |
| 15 | Rahvusraamatukogu (National Library) | DIGAR OAI-PMH, ESTER (Sierra) | none | OAI-PMH XML | — | per item | ❌ the OAI path we guessed returns 404 and ester.ee timed out; needs research |
| 16 | EKI language resources | `https://api.sonapi.ee/v2/{word}` (Sõnaveeb); Ekilex API `https://ekilex.ee/api/...` | Sõnaveeb none; Ekilex **API key** (free) | JSON | fair use | CC BY 4.0 | ✅ sonapi 200 JSON; Ekilex 403 without a key |
| 17 | eesti.ee | `https://www.eesti.ee/` | personal services need TARA/eID | HTML | — | — | ⚠️ no public API; keep using Exa search |
| 18 | X-tee (X-Road) | `https://www.x-tee.ee/catalogue/` | **X-tee membership** + security server | SOAP/REST | per service | — | ⚠️ catalogue only; out of scope for v1 |
| 19 | Terviseamet (Health Board) | open data on avaandmed (swimming water, pharmacies, etc.) | none | CSV/JSON through #1 | — | CC BY | ❌ `avalik.terviseamet.ee` not resolving; reach it through #1 |
| 20 | Tööinspektsioon (Labour Inspectorate) | `https://www.ti.ee/` plus avaandmed datasets (work accidents) | none | HTML / CSV | — | — | ⚠️ website 200; no API |
| 21 | Rahandusministeerium state budget | `https://riigiraha.fin.ee/` (state budget, money flows) plus avaandmed | none | web app with CSV export | — | open | ✅ 200 HTML; the backing API needs investigation |
| 22 | Health information (TAI) | `https://vtiav.sm.ee/` (PxWeb-like) | none | PxWeb | — | open | ✅ 200 |

## 3. MCP server design

- **Framework:** Python 3.12, `mcp` SDK **FastMCP**, `httpx` (async), `pydantic` v2 models for every tool's input and output (structured content plus a short text summary).
- **Transports:** `streamable-http` at `/mcp` (production) and `stdio` (local / Claude Desktop / Cursor), both chosen by `python -m eesti_mcp --transport {http,stdio}`.
- **Location:** a new package `mcp_server/` in this repo, sharing `utils/config.py`. It has its own `Dockerfile.mcp` and is deployed as its own Coolify app so the chat app keeps running if the MCP server has trouble. The LangGraph agents can later use it through `langchain-mcp-adapters`.
- **Every result carries:** `source_url`, `source_name`, `licence`, `retrieved_at`, and `cached: bool`, so the agents can always cite the source.

### Tools by domain (sketch of inputs → outputs)

**Business (Äriregister, EMTA)**
- `company_search(query: str, limit=10)` → `[{reg_code, name, status, legal_form, address}]` (RIK autocomplete).
- `company_details(reg_code: str)` → `{reg_code, name, status, founded, legal_form, address, capital, emtak, vat_no?, url}` (RIK open-data dump loaded into Postgres/SQLite every night).
- `company_tax_data(reg_code: str, quarters=4)` → `[{quarter, state_taxes, labour_taxes, turnover, employees}]` (EMTA quarterly CSV).
- `tax_debtor_check(reg_code: str)` → `{is_debtor, amount?, as_of}`.

**Law (Riigi Teataja)**
- `law_search(query: str, in_force=True, limit=10)` → `[{act_id, title, type, issuer, in_force_from, url}]`.
- `law_get(act_id: str, section?: str)` → `{title, text|sections[], url, version_date}` (cut down to a size limit).

**Location (Maa- ja Ruumiamet)**
- `address_lookup(address: str, limit=5)` → `[{full_address, ads_oid, lat, lon, ehak_code, cadastral_no?}]`.
- `cadastral_parcel(cadastral_no | lat,lon)` → `{cadastral_no, area_m2, purpose, address}` (WFS).
- `map_layers()` → list of the WMS/WFS layers we support.

**Statistics (andmed.stat.ee, TAI)**
- `stat_search(query: str, lang="en")` → `[{table_id, title, updated}]` (local index of the table tree).
- `stat_table_meta(table_id)` → `{variables:[{code, values}]}`.
- `stat_query(table_id, filters: dict, format="json-stat2")` → `{columns, rows, notes}` (cell cap enforced).

**Procurement (RHR)**
- `procurement_search(query?, buyer_reg_code?, cpv?, from_date?, to_date?)` → `[{notice_id, title, buyer, value, deadline, url}]` (monthly XML loaded into a local index).

**Weather and transport**
- `weather_now(station?: str)` → `{station, time, temp, wind, precip}`; `weather_forecast(lang)` → 4-day forecast.
- `road_conditions(region?)` (phase 3, once DATEX access is confirmed).

**Money**
- `exchange_rate(currency: str, date?)` → `{rate, base:"EUR", date}` (ECB/Eesti Pank).
- `state_budget(area?, year?)` (phase 3, riigiraha).

**Language and culture**
- `word_lookup(word: str)` → `{lemma, pos, definitions[], forms[]}` (Sõnaveeb; Ekilex with a key).
- `open_data_search(query: str, limit=10)` → `[{dataset_id, title, publisher, formats, licence, url}]` (avaandmed; covers Terviseamet, TI and others).
- `gov_web_search(query, official_only=True)`: wraps the existing Exa tool so MCP clients get the same grounded search.

### Caching
- Two layers: an in-process TTL LRU (`cachetools`) plus Postgres (or Redis if Coolify already runs one) keyed by `tool+normalised args`.
- How long data is kept: weather 10 min; exchange rates 6 h; RIK autocomplete 24 h; company and EMTA data until the next nightly/quarterly load; law text 24 h; stat metadata 7 d, stat queries 24 h; addresses 30 d.
- Bulk sources (RIK dumps, EMTA CSV, RHR monthly XML) are loaded by a scheduled job (Coolify scheduled task, nightly) into local tables, so queries don't hit the upstream servers.

### Rate limiting
- **Outbound:** an async limiter for each upstream (e.g. stat.ee ≤ 3 req/s, RIK ≤ 2 req/s, others ≤ 5 req/s), plus retry with backoff on 429/5xx and a circuit breaker. User-Agent: `eesti.chat-mcp/x (contact email)`.
- **Inbound:** a token bucket per API key / IP (e.g. 60 req/min, 5k/day), with a 429 that carries `Retry-After`.

### Auth for the MCP endpoint
- v1: bearer API keys (`Authorization: Bearer ek_...`), stored hashed in Postgres. An admin page in the existing `admin/` area issues and revokes them.
- Optional anonymous tier at a much lower rate limit, for the public directory listing.
- v2: OAuth 2.1 per the MCP authorization spec, reusing Google login for user-tied keys.
- CORS limited to known origins; there are no write tools, so there is no exposure to state-changing calls.

### Deployment ("this server")
- Coolify at `coolify.fastsme.com`, server `191.218.164.166`. A new application from the same repo, `Dockerfile.mcp`, port 8000, healthcheck `/health`.
- Domain **`mcp.eesti.chat`** (the main site is `eesti.chat`). Needs a DNS A record → 191.218.164.166; Coolify/Traefik issues the Let's Encrypt certificate.
- Environment: `MCP_DB_URL`, `EXA_API_KEY`, `EKILEX_API_KEY`, `MCP_ADMIN_TOKEN` (values only in Coolify, never in git).
- CI: extend `deploy.yml` with a second webhook (`COOLIFY_MCP_WEBHOOK_URL`) that fires only when files in `mcp_server/**` change.

### Testing
- Unit: pydantic schema tests and parsers run against recorded fixtures (`respx` / VCR cassettes) for each upstream.
- Contract: a nightly GitHub Action runs a live "canary" call per upstream and opens an issue when one breaks (these gov endpoints change without notice).
- MCP: in-memory tests with the `mcp` client (`list_tools`, `call_tool`) for both transports, plus MCP Inspector by hand.
- Load: a short `locust` run against `/mcp` before launch.

## 4. Phases

1. **P0 skeleton (1–2 d):** FastMCP app on both transports, auth, rate limiter, caching, `/health`, Coolify app on `mcp.eesti.chat`, plus `gov_web_search`, `weather_*`, `exchange_rate`, `address_lookup`.
2. **P1 core data (3–5 d):** Äriregister (autocomplete plus nightly dump), EMTA quarterly data and debtors, Riigi Teataja search/get, stat.ee search/meta/query, avaandmed search, word lookup.
3. **P2 integration (2–3 d):** connect the LangGraph agents to the MCP tools (tax/business agents first), with citations in the UI; public docs page at `eesti.chat/mcp`.
4. **P3 extras:** RHR procurement, cadastral WFS, state budget, road conditions, National Library; listing in MCP directories; OAuth.
5. **Later / maybe:** X-tee services (needs membership and a security server) and the paid RIK XML API.

## 5. Open questions for Julian

1. Should the MCP server be **public** (anonymous tier plus keys, listed in MCP directories), or for **eesti.chat agents and invited users only**?
2. Can we create the DNS record **`mcp.eesti.chat` → 191.218.164.166** and add a second Coolify app on that server? Does it already run Postgres/Redis we can reuse for caching and bulk tables?
3. Do you want to pay for the **RIK XML services** (board members, beneficial owners, annual reports), or stay with free open data only for now?
4. Should we **apply for X-tee membership** (through Predictive Labs OÜ) to get vehicle, population and other services later, or rule it out?
5. Monorepo (`mcp_server/` in eesti-chat, as proposed) or a separate `predictivelabsai/eesti-mcp` repo?
6. Should the chat agents switch from Exa-only to **MCP-tools-first** in P2, and which agent goes first (the Taxes or e-Residency & Company agent is suggested)?
