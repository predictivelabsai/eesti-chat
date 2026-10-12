# eesti.chat MCP server (`mcp_server/`)

A public [Model Context Protocol](https://modelcontextprotocol.io) server that exposes free Estonian
government open data as tools. Production endpoint (once deployed): **`https://mcp.eesti.chat/mcp`**.

Every tool returns a JSON envelope:

```json
{
  "source_name": "e-Business Register (RIK)",
  "source_url": "https://…",          // cite this
  "licence": "CC BY 4.0 (RIK open data)",
  "retrieved_at": "2026-10-12T17:21:48+00:00",
  "cached": false,
  "data": { … }
}
```

## Tools

| Tool | Source | Upstream / method | Cache |
|---|---|---|---|
| `company_search(query, limit)` | e-Business Register | `ariregister.rik.ee/est/api/autocomplete` | 24 h |
| `company_details(reg_code)` | e-Business Register | daily open-data dump (SQLite); autocomplete fallback | daily reload |
| `company_tax_data(reg_code)` | EMTA | quarterly "tasutud maksud" CSV (SQLite) | daily check |
| `law_search(query, in_force_on?, limit)` | Riigi Teataja | `/api/oigusakt_otsing/1/otsi` | 24 h |
| `address_lookup(address, limit)` | Maa- ja Ruumiamet In-ADS | `inaadress.maaamet.ee/inaadress/gazetteer` | 30 d |
| `stat_search(query, lang, limit)` | Statistics Estonia | PxWeb v1 `?query=` across databases | 24 h |
| `stat_table_meta(table_id, lang)` | Statistics Estonia | PxWeb v1 GET | 7 d |
| `stat_query(table_id, filters, lang)` | Statistics Estonia | PxWeb v1 POST, json-stat2 (≤500 rows shown) | 24 h |
| `procurement_search(query?, buyer_reg_code?, cpv_prefix?, from_date?, limit)` | Riigihangete register | monthly eForms XML, last 3 months (SQLite) | daily reload |
| `weather_now(station?)` | Keskkonnaagentuur | `ilmateenistus.ee/ilma_andmed/xml/observations.php` | 10 min |
| `weather_forecast(lang)` | Keskkonnaagentuur | `…/forecast.php` | 30 min |
| `exchange_rate(currency?)` | ECB / Eesti Pank | `eurofxref-daily.xml` | 6 h |
| `word_lookup(word)` | EKI Sõnaveeb | `api.sonapi.ee/v2/{word}` | 7 d |
| `open_data_search(query, limit)` | Open data portal | `andmed.eesti.ee/api/datasets?search=` | 24 h |
| `gov_web_search(query, max_results, official_only)` | Exa | same domain list as the chat app (`tools/search.py`) | 6 h |

All tools are read-only (`readOnlyHint`). Input schemas are published through `tools/list`.

## Transports

```bash
python -m mcp_server --transport http    # streamable HTTP at :8000/mcp, plus GET /health and GET /
python -m mcp_server --transport stdio   # local clients
```

Claude Desktop / Cursor (stdio, from a checkout):

```json
{"mcpServers": {"eesti-gov": {"command": "python", "args": ["-m", "mcp_server", "--transport", "stdio"],
  "cwd": "/path/to/eesti-chat"}}}
```

Remote clients: `https://mcp.eesti.chat/mcp`, optionally with `Authorization: Bearer <key>`.

## Auth and limits

- **Anonymous tier:** no key; `MCP_ANON_RPM` (30/min) and `MCP_ANON_RPD` (500/day) per client IP (from `X-Forwarded-For`, set by Traefik).
- **Key tier:** `Authorization: Bearer ek_…` or `X-API-Key: ek_…`; `MCP_KEY_RPM` (300/min) and `MCP_KEY_RPD` (20 000/day) per key.
- An invalid key gets 401; going over the limit gets 429 with `Retry-After`. `/health` is never limited.
- To issue a key, run `python -m mcp_server.keys new`. Give the `key` to the client and add **only** the `hash` to `MCP_API_KEY_HASHES` (comma-separated), then redeploy.
- Limits are counted in memory per container, so run one replica, or move the counters to Redis before scaling out.

## Upstream protection

- Each source has a minimum interval between calls (`core.SOURCES[...].min_interval_s`, 0.1–1 s).
- Retries on 429/5xx with exponential backoff (2 retries).
- In-process TTL cache (see table). Bulk sources are mirrored into SQLite under `MCP_DATA_DIR`. A background thread reloads anything older than `MCP_BULK_MAX_AGE_H` (24 h) and checks every hour. Run it by hand with `python -m mcp_server.bulk [rik|emta|rhr|all]` (about 30 s and 100 MB of downloads).
- The first load runs at startup. Until it finishes, `company_details` falls back to autocomplete, and `company_tax_data` / `procurement_search` return a "not loaded yet" error.

## Environment

| Var | Default | Purpose |
|---|---|---|
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8000` | bind address |
| `MCP_DATA_DIR` | `./data` (`/data` in Docker) | SQLite mirror; mount a persistent volume |
| `MCP_API_KEY_HASHES` | empty | sha256 hashes of issued keys |
| `MCP_ANON_RPM` / `MCP_ANON_RPD` | 30 / 500 | anonymous limits |
| `MCP_KEY_RPM` / `MCP_KEY_RPD` | 300 / 20000 | key limits |
| `MCP_BULK_AUTOLOAD` | `1` | background bulk refresh |
| `MCP_BULK_MAX_AGE_H` | 24 | reload threshold |
| `MCP_TRUST_PROXY` | `1` | use `X-Forwarded-For` for the client IP |
| `EXA_API_KEY` | empty | enables `gov_web_search` |

## Chat app integration

`tools/mcp_tools.py` wraps MCP tools as LangChain tools. If `EESTI_MCP_URL` is set, they call the remote server, sending `EESTI_MCP_API_KEY` as the bearer token. Otherwise they call the same tools in-process.
The **e-Residency & Company** agent uses `company_search`, `company_details`, `company_tax_data`, `law_search`, `address_lookup` and `exchange_rate` before falling back to Exa `web_search` (see `prompts/system/eresidency.md`).

## Tests

```bash
python -m pytest tests/test_mcp_server.py -q                                   # recorded fixtures, no network
python -m pytest tests/test_mcp_server.py -q --run-integration -k live         # live upstream smoke test
```

CI runs both (`.github/workflows/test.yml`). The live job is allowed to fail, because government endpoints change without notice.
