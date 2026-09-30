"""Web search tool — Exa, biased to official Estonian government sources."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from utils.config import settings

log = logging.getLogger(__name__)

EXA_URL = "https://api.exa.ai/search"

# Official / authoritative Estonian domains, used when official_only=True.
OFFICIAL_DOMAINS: list[str] = [
    "eesti.ee",
    "e-resident.gov.ee",
    "eresident.politsei.ee",
    "politsei.ee",
    "emta.ee",
    "ria.ee",
    "id.ee",
    "rik.ee",
    "notar.ee",
    "riigiteataja.ee",
    "sotsiaalkindlustusamet.ee",
    "tervisekassa.ee",
    "haigekassa.ee",
    "valisministeerium.ee",
    "vm.ee",
    "kra.ee",
    "riigikogu.ee",
    "president.ee",
    "valitsus.ee",
    "stat.ee",
    "e-estonia.com",
    "investinestonia.com",
    "visitestonia.com",
    "workinestonia.com",
    "startupestonia.ee",
]


class SearchArgs(BaseModel):
    query: str = Field(
        description="Natural-language web search query about Estonian government services, "
                    "e-Residency, taxes, digital ID, moving to Estonia, or Estonia in general."
    )
    max_results: int = Field(default=6, ge=1, le=15)
    official_only: bool = Field(
        default=True,
        description="If true (default), restrict results to official/authoritative Estonian "
                    "domains (eesti.ee, ria.ee, emta.ee, e-resident.gov.ee, politsei.ee, etc.). "
                    "Set to false for broader topics like culture, tourism, or history.",
    )
    days: Optional[int] = Field(default=None, description="Recency window in days (optional).")


def _exa(query: str, max_results: int, official_only: bool, days: int | None) -> dict | None:
    key = settings().exa_api_key
    if not key:
        return None
    payload = {
        "query": query,
        "numResults": max_results,
        "type": "auto",
        "contents": {"text": {"maxCharacters": 1000}, "highlights": {"numSentences": 3}},
    }
    if official_only:
        payload["includeDomains"] = OFFICIAL_DOMAINS
    if days:
        from datetime import datetime, timedelta
        payload["startPublishedDate"] = (datetime.utcnow() - timedelta(days=days)).isoformat()
    headers = {"x-api-key": key, "content-type": "application/json"}
    try:
        r = httpx.post(EXA_URL, json=payload, headers=headers, timeout=20.0)
        r.raise_for_status()
        data = r.json()
        return {
            "provider": "exa",
            "results": [
                {"title": h.get("title"), "url": h.get("url"),
                 "snippet": (h.get("text") or "")[:1000],
                 "score": h.get("score")}
                for h in (data.get("results") or [])
            ],
        }
    except Exception as e:
        log.warning("exa failed: %s", e)
        return None


def _web_search(**kw) -> str:
    args = SearchArgs(**kw)
    data = _exa(args.query, args.max_results, args.official_only, args.days)
    # If an official-only search comes back empty, retry once across the open web.
    if data and not data["results"] and args.official_only:
        data = _exa(args.query, args.max_results, False, args.days)
    if not data:
        return "Search unavailable — no EXA_API_KEY configured or provider failed."

    items = data["results"]
    scope = "official Estonian sources" if args.official_only else "the web"
    lines = [f"Search over {scope}: {args.query} ({len(items)} results)\n"]
    for it in items:
        title = it.get("title") or "Untitled"
        url = it.get("url") or ""
        snippet = (it.get("snippet") or "")[:300]
        lines.append(f"- **{title}**\n  {url}\n  {snippet}\n")
    return "\n".join(lines)


web_search = StructuredTool.from_function(
    func=_web_search,
    name="web_search",
    description=(
        "Search the web for authoritative information about Estonia — e-Residency, company "
        "registration, taxes, digital ID (e-ID/Smart-ID/Mobiil-ID), residence permits, public "
        "services, and the e-Estonia digital society. By default it restricts results to official "
        "Estonian government and authoritative domains; set official_only=false for broader topics "
        "like culture, tourism, or history. Returns title + URL + snippet. ALWAYS cite the URLs you "
        "use so the user can verify the answer."
    ),
    args_schema=SearchArgs,
)
