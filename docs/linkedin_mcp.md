# 🔌 Your AI agent can now read the Estonian state. We shipped a free MCP server for Estonia's public data.

A few weeks ago we launched **eesti.chat**, an AI front door to Estonia (original post: `docs/linkedin.md`). Today we are opening the developer door: a free **Model Context Protocol (MCP) server** that plugs Estonia's official open data into any AI agent.

One URL: **https://mcp.eesti.chat/mcp**
No sign-up. No API key. **15 read-only tools, 11 official sources**, and every answer carries its source link.

We tested it this morning in **Claude Code**, **Claude.ai** and **ChatGPT**. Same server, nothing to configure beyond pasting the URL. Here is what came back, one question per tool group:

🏢 **Companies & tax** — "Who pays more labour taxes, Bolt or Wise?"
Bolt Technology OÜ: **€8.40M labour taxes, 629 employees** in Q3 2026. Wise Europe's Estonian branch: €0.93M and 93 employees. Pulled live from the e-Business Register and EMTA's quarterly open data, with the exact source URL under every number. (`company_search` → `company_tax_data` → `procurement_search`)

📍 **Places & everyday** — "I'm heading to Vabaduse väljak 7 tomorrow."
The official In-ADS address with coordinates (59.4326, 24.7441), **8.6 °C and overcast at Tallinn-Harku right now**, rain spreading from the islands tomorrow, 1 EUR = 1.1181 USD, and *vabadus* = freedom, so Vabaduse väljak is Freedom Square. Five tools, one question. (`address_lookup`, `weather_now`, `weather_forecast`, `exchange_rate`, `word_lookup`)

📊 **Data & search** — "Estonia's population, last three years."
The agent found Statistics Estonia table RV021, read its metadata and queried it: **1,374,687 → 1,369,995 → 1,360,745** (1 January 2024, 2025, 2026). Then it checked andmed.eesti.ee for EV-charging datasets (honest answer: there are none yet) and found the **€150 e-Residency state fee** on politsei.ee. (`stat_search` → `stat_table_meta` → `stat_query`, `open_data_search`, `gov_web_search`)

Every tool returns the same envelope:
`source_url` · `licence` · `retrieved_at` · `cached` · `data`
So the agent can cite, and you can check.

Connect in ten seconds:
▸ Claude Code: `claude mcp add --transport http eesti https://mcp.eesti.chat/mcp`
▸ Claude.ai: Customize → Connectors → Add → Add custom connector
▸ ChatGPT: Plugins → Add → Add custom MCP server → No authentication
▸ Cursor, xAI Responses API, anything that speaks MCP over HTTP: paste the URL

Behind it: e-Business Register (RIK), Tax and Customs Board (EMTA), Riigi Teataja, Maa- ja Ruumiamet In-ADS, Statistics Estonia, the Public Procurement Register, Keskkonnaagentuur, Eesti Pank / ECB, EKI Sõnaveeb and andmed.eesti.ee. All open data, all licensed for reuse, all read-only.

Estonia built the digital state. Now any AI agent can read it.

🔗 Docs: https://eesti.chat/#developers
⭐ Source (open): https://github.com/predictivelabsai/eesti-chat
🇪🇪 Try the chat: https://eesti.chat

#eEstonia #MCP #AIagents #OpenData #GovTech #eResidency #ClaudeCode #ChatGPT #OpenSource #Estonia

---

## Notes for posting (not part of the post)

- All figures above were returned live by the MCP server on 2026-10-13 and match the raw tool output (`company_tax_data` for reg codes 12417834 and 16681657, `stat_query` on RV021, `weather_now` for Tallinn-Harku, `exchange_rate` for USD dated 2026-10-12).
- Suggested media, in `screenshots/`: `mcp_tour.gif` (page tour plus the three clients), `mcp_14_claude_code_terminal.png` (Claude Code run), `mcp_08_chatgpt_answer_full.png` (ChatGPT answer), `mcp_13_claude_answer_full.png` (Claude.ai answer), `mcp_12_claude_connected.png` (15 tools detected as read-only).
- LinkedIn strips markdown. Paste as plain text and keep the bold by retyping it with the LinkedIn formatter, or drop it.
