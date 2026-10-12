"""FastMCP server exposing Estonian government open data.

Run:
    python -m mcp_server --transport http   # streamable HTTP on :8000/mcp (+ /health)
    python -m mcp_server --transport stdio  # local clients (Claude Desktop, Cursor, ...)
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server import __version__, bulk, sources
from mcp_server.config import mcp_settings

log = logging.getLogger("eesti_mcp")

INSTRUCTIONS = """Estonian government open data (eesti.chat). Tools return JSON envelopes with
source_name, source_url, licence, retrieved_at and data. Always cite source_url when you use a result.
Covers: e-Business Register companies, EMTA tax data, Riigi Teataja legislation, In-ADS addresses,
Statistics Estonia tables, public procurement notices, weather, ECB/Eesti Pank euro rates,
the Sõnaveeb dictionary, the national open data portal and official-site web search."""

mcp = FastMCP(
    "eesti-gov",
    instructions=INSTRUCTIONS,
    website_url="https://eesti.chat",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    # Public server behind Traefik, no cookies/ambient credentials -> DNS-rebinding guard not needed.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

RO = {"readOnlyHint": True, "openWorldHint": True}
Env = dict[str, Any]


# ---- Business ----
@mcp.tool(annotations=RO)
async def company_search(
    query: Annotated[str, Field(description="Company name or part of it, or a registry code", min_length=2)],
    limit: Annotated[int, Field(ge=1, le=25)] = 10,
) -> Env:
    """Search the Estonian e-Business Register (Äriregister) by company name or registry code."""
    return await sources.company_search(query, limit)


@mcp.tool(annotations=RO)
async def company_details(
    reg_code: Annotated[str, Field(description="8-digit Estonian registry code, e.g. 16469147")],
) -> Env:
    """Company details from the e-Business Register open data: legal form, status, VAT number,
    registration date and registered address."""
    return await sources.company_details(reg_code)


@mcp.tool(annotations=RO)
async def company_tax_data(
    reg_code: Annotated[str, Field(description="8-digit Estonian registry code")],
) -> Env:
    """Quarterly taxes paid, labour taxes, taxable turnover and number of employees published
    by the Estonian Tax and Customs Board (EMTA) for a company."""
    return await sources.company_tax_data(reg_code)


# ---- Law ----
@mcp.tool(annotations=RO)
async def law_search(
    query: Annotated[str, Field(description="Words from the act title in Estonian, e.g. 'tulumaksuseadus'")],
    in_force_on: Annotated[str | None, Field(description="Only acts in force on this date, YYYY-MM-DD")] = None,
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
) -> Env:
    """Search Estonian legislation in Riigi Teataja (State Gazette) by title."""
    return await sources.law_search(query, in_force_on, limit)


# ---- Location ----
@mcp.tool(annotations=RO)
async def address_lookup(
    address: Annotated[str, Field(description="Free-text Estonian address, e.g. 'Vabaduse väljak 7 Tallinn'")],
    limit: Annotated[int, Field(ge=1, le=20)] = 5,
) -> Env:
    """Geocode/normalise an Estonian address with the official In-ADS address system
    (Maa- ja Ruumiamet): full address, ADS ids, EHAK code and WGS84 coordinates."""
    return await sources.address_lookup(address, limit)


# ---- Statistics ----
@mcp.tool(annotations=RO)
async def stat_search(
    query: Annotated[str, Field(description="Topic keywords, e.g. 'population', 'average wage'")],
    lang: Annotated[str, Field(description="'en' or 'et'")] = "en",
    limit: Annotated[int, Field(ge=1, le=30)] = 10,
) -> Env:
    """Find Statistics Estonia (andmed.stat.ee) tables by keyword. Returns table ids."""
    return await sources.stat_search(query, lang, limit)


@mcp.tool(annotations=RO)
async def stat_table_meta(
    table_id: Annotated[str, Field(description="Table id, e.g. 'RV021'")],
    lang: str = "en",
) -> Env:
    """List the variables and value codes of a Statistics Estonia table (needed for stat_query)."""
    return await sources.stat_table_meta(table_id, lang)


@mcp.tool(annotations=RO)
async def stat_query(
    table_id: Annotated[str, Field(description="Table id, e.g. 'RV021'")],
    filters: Annotated[dict[str, list[str]], Field(
        description="Variable code -> value codes, e.g. {'Sugu': ['1'], 'Aasta': ['top:3']}. "
                    "Use ['*'] for all values and ['top:N'] for the latest N periods.")],
    lang: str = "en",
) -> Env:
    """Query a Statistics Estonia table and get rows (max 500 cells shown)."""
    return await sources.stat_query(table_id, filters, lang)


# ---- Procurement ----
@mcp.tool(annotations=RO)
async def procurement_search(
    query: Annotated[str | None, Field(description="Words in title/description/buyer (Estonian)")] = None,
    buyer_reg_code: Annotated[str | None, Field(description="Buyer registry code")] = None,
    cpv_prefix: Annotated[str | None, Field(description="CPV code prefix, e.g. '72' for IT services")] = None,
    from_date: Annotated[str | None, Field(description="Issued on/after YYYY-MM-DD")] = None,
    limit: Annotated[int, Field(ge=1, le=100)] = 20,
) -> Env:
    """Search recent Estonian public procurement notices (Riigihangete register open data, last ~3 months)."""
    return await sources.procurement_search(query, buyer_reg_code, cpv_prefix, from_date, limit)


# ---- Weather / money / language / catalogue / web ----
@mcp.tool(annotations=RO)
async def weather_now(
    station: Annotated[str | None, Field(description="Station name filter, e.g. 'Tallinn', 'Tartu'")] = None,
) -> Env:
    """Latest weather observations from Estonian weather stations (ilmateenistus.ee)."""
    return await sources.weather_now(station)


@mcp.tool(annotations=RO)
async def weather_forecast(lang: Annotated[str, Field(description="'eng', 'est' or 'rus'")] = "eng") -> Env:
    """4-day national weather forecast for Estonia (ilmateenistus.ee)."""
    return await sources.weather_forecast(lang)


@mcp.tool(annotations=RO)
async def exchange_rate(
    currency: Annotated[str | None, Field(description="ISO code, e.g. 'USD'. Omit for all rates.")] = None,
) -> Env:
    """Latest euro reference exchange rates (ECB, as published by Eesti Pank)."""
    return await sources.exchange_rate(currency)


@mcp.tool(annotations=RO)
async def word_lookup(word: Annotated[str, Field(description="Estonian word, e.g. 'tere'")]) -> Env:
    """Look up an Estonian word in EKI Sõnaveeb: meanings, forms, examples and translations."""
    return await sources.word_lookup(word)


@mcp.tool(annotations=RO)
async def open_data_search(
    query: Annotated[str, Field(description="Keywords (Estonian works best), e.g. 'ujumisvesi'")],
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
) -> Env:
    """Search the Estonian national open data portal (andmed.eesti.ee) for datasets."""
    return await sources.open_data_search(query, limit)


@mcp.tool(annotations=RO)
async def gov_web_search(
    query: str,
    max_results: Annotated[int, Field(ge=1, le=15)] = 6,
    official_only: bool = True,
) -> Env:
    """Web search over official Estonian government websites (Exa). Use when no structured tool fits."""
    return await sources.gov_web_search(query, max_results, official_only)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "version": __version__, "bulk": bulk.status()})


@mcp.custom_route("/", methods=["GET"])
async def index(_: Request) -> JSONResponse:
    return JSONResponse({"name": "eesti-gov MCP server", "version": __version__, "mcp_endpoint": "/mcp",
                         "docs": "https://github.com/predictivelabsai/eesti-chat/blob/main/docs/mcp_server.md"})


def http_app():
    from mcp_server.auth import AuthRateLimitMiddleware
    return AuthRateLimitMiddleware(mcp.streamable_http_app(), mcp_settings())


def run(transport: str = "http") -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = mcp_settings()
    if s.bulk_autoload:
        bulk.start_background_refresh()
    if transport == "stdio":
        mcp.run("stdio")
        return
    import uvicorn
    uvicorn.run(http_app(), host=s.host, port=s.port, proxy_headers=True, forwarded_allow_ips="*")
