"""LangChain tools backed by the eesti.chat MCP server (mcp_server/).

If EESTI_MCP_URL is set (e.g. https://mcp.eesti.chat/mcp) the tools call the remote server
over streamable HTTP, sending EESTI_MCP_API_KEY as a bearer token when present. Otherwise
they call the same MCP tools in-process (no extra deployment needed in dev).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

MAX_CHARS = 6000


def _compact(payload: Any) -> str:
    s = json.dumps(payload, ensure_ascii=False, default=str)
    return s if len(s) <= MAX_CHARS else s[:MAX_CHARS] + "… [truncated]"


async def call_mcp_tool(name: str, args: dict) -> dict:
    url = os.environ.get("EESTI_MCP_URL", "").strip()
    if url:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        key = os.environ.get("EESTI_MCP_API_KEY", "").strip()
        headers = {"Authorization": f"Bearer {key}"} if key else None
        async with streamablehttp_client(url, headers=headers, timeout=30) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(name, args)
    else:
        from mcp_server.server import mcp
        from mcp.types import CallToolResult, TextContent
        try:
            out = await mcp.call_tool(name, args)
            structured = out[1] if isinstance(out, tuple) else None
            res = CallToolResult(content=[], structuredContent=structured, isError=False)
        except Exception as e:  # noqa: BLE001
            res = CallToolResult(content=[TextContent(type="text", text=str(e))], isError=True)
    if res.isError:
        text = " ".join(getattr(c, "text", "") for c in res.content)
        return {"error": text or "tool failed"}
    if res.structuredContent is not None:
        sc = res.structuredContent
        return sc.get("result", sc) if isinstance(sc, dict) and set(sc) == {"result"} else sc
    text = " ".join(getattr(c, "text", "") for c in res.content)
    try:
        return json.loads(text)
    except ValueError:
        return {"text": text}


def _make(name: str, description: str, schema: type[BaseModel]) -> StructuredTool:
    async def _run(**kwargs) -> str:
        args = {k: v for k, v in kwargs.items() if v is not None}
        try:
            return _compact(await call_mcp_tool(name, args))
        except Exception as e:  # noqa: BLE001
            while isinstance(e, BaseExceptionGroup) and e.exceptions:
                e = e.exceptions[0]
            log.warning("MCP tool %s failed: %s", name, e)
            return _compact({"error": f"{name} unavailable: {e}. Fall back to web_search."})

    return StructuredTool.from_function(coroutine=_run, name=name, description=description, args_schema=schema)


class _CompanySearch(BaseModel):
    query: str = Field(description="Company name (or part) or 8-digit registry code")
    limit: int = Field(default=5, ge=1, le=25)


class _RegCode(BaseModel):
    reg_code: str = Field(description="8-digit Estonian registry code")


class _LawSearch(BaseModel):
    query: str = Field(description="Words from the act title in Estonian, e.g. 'äriseadustik', 'tulumaksuseadus'")
    in_force_on: Optional[str] = Field(default=None, description="YYYY-MM-DD; only acts in force that day")
    limit: int = Field(default=5, ge=1, le=20)


class _Address(BaseModel):
    address: str = Field(description="Estonian address to validate, e.g. 'Sakala 7-2 Tallinn'")
    limit: int = Field(default=3, ge=1, le=10)


class _Fx(BaseModel):
    currency: Optional[str] = Field(default=None, description="ISO currency code, e.g. USD")


company_search = _make(
    "company_search",
    "Search the official Estonian e-Business Register by company name or registry code. "
    "Use to check whether a company name is taken or to find a company's registry code.", _CompanySearch)
company_details = _make(
    "company_details",
    "Official e-Business Register details for a company: legal form, status, VAT number, "
    "registration date, registered address.", _RegCode)
company_tax_data = _make(
    "company_tax_data",
    "EMTA open data for a company: quarterly state taxes, labour taxes, turnover and employee count.", _RegCode)
law_search = _make(
    "law_search", "Search Estonian legislation in Riigi Teataja by act title (Estonian words).", _LawSearch)
address_lookup = _make(
    "address_lookup", "Validate/normalise an Estonian address with the official In-ADS address system.", _Address)
exchange_rate = _make(
    "exchange_rate", "Latest euro reference exchange rates (ECB / Eesti Pank).", _Fx)

BUSINESS_TOOLS = [company_search, company_details, company_tax_data, law_search, address_lookup, exchange_rate]
