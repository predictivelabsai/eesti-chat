"""Shared plumbing: HTTP client, per-source rate limits, TTL cache, result envelope."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import httpx
from cachetools import TTLCache

from mcp_server.config import mcp_settings


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    licence: str
    min_interval_s: float  # outbound politeness: min seconds between calls to this upstream
    home: str


SOURCES: dict[str, Source] = {s.key: s for s in [
    Source("rik", "e-Business Register (RIK)", "CC BY 4.0 (RIK open data)", 0.5, "https://ariregister.rik.ee"),
    Source("riigiteataja", "Riigi Teataja", "Public legal texts (Riigi Teataja terms of use)", 0.3, "https://www.riigiteataja.ee"),
    Source("inads", "Maa- ja Ruumiamet In-ADS", "CC BY 4.0 (Estonian Address Data System)", 0.2, "https://inaadress.maaamet.ee"),
    Source("stat", "Statistics Estonia", "CC BY 4.0 (Statistics Estonia)", 0.35, "https://andmed.stat.ee"),
    Source("emta", "Estonian Tax and Customs Board (EMTA)", "Open data (EMTA)", 1.0, "https://www.emta.ee"),
    Source("rhr", "Public Procurement Register (RHR)", "Open data (Rahandusministeerium RHR)", 1.0, "https://riigihanked.riik.ee"),
    Source("ilm", "Estonian Environment Agency (ilmateenistus.ee)", "CC BY 4.0 (Keskkonnaagentuur)", 0.2, "https://www.ilmateenistus.ee"),
    Source("ecb", "European Central Bank euro reference rates", "ECB reuse policy (free reuse with attribution)", 0.2, "https://www.ecb.europa.eu"),
    Source("sonaveeb", "EKI Sõnaveeb (sonapi.ee)", "CC BY 4.0 (Eesti Keele Instituut)", 0.2, "https://sonaveeb.ee"),
    Source("avaandmed", "Estonian Open Data Portal (andmed.eesti.ee)", "Per dataset (mostly CC BY 4.0)", 0.2, "https://andmed.eesti.ee"),
    Source("exa", "Exa web search (official .ee domains)", "Third-party search results; see each URL", 0.1, "https://exa.ai"),
]}


class UpstreamError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def envelope(source: str, source_url: str, data: Any, *, cached: bool = False,
             retrieved_at: str | None = None, **extra: Any) -> dict:
    src = SOURCES[source]
    out = {
        "source_name": src.name,
        "source_url": source_url,
        "licence": src.licence,
        "retrieved_at": retrieved_at or now_iso(),
        "cached": cached,
        "data": data,
    }
    out.update(extra)
    return out


class _Limiter:
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._next = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._next > now:
                await asyncio.sleep(self._next - now)
            self._next = max(now, self._next) + self.min_interval


_limiters: dict[str, _Limiter] = {}


def limiter(source: str) -> _Limiter:
    lim = _limiters.get(source)
    if lim is None:
        lim = _limiters[source] = _Limiter(SOURCES[source].min_interval_s)
    return lim


_client: httpx.AsyncClient | None = None


def client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(25.0, connect=10.0),
            follow_redirects=True,
            headers={"User-Agent": mcp_settings().user_agent},
        )
    return _client


async def fetch(source: str, method: str, url: str, *, retries: int = 2, **kw) -> httpx.Response:
    """Rate-limited request with retry/backoff on 429/5xx and transport errors."""
    last: Exception | None = None
    for attempt in range(retries + 1):
        await limiter(source).wait()
        try:
            r = await client().request(method, url, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                last = UpstreamError(f"{SOURCES[source].name} returned HTTP {r.status_code}")
            elif r.status_code >= 400:
                raise UpstreamError(f"{SOURCES[source].name} returned HTTP {r.status_code}")
            else:
                return r
        except httpx.HTTPError as e:
            last = UpstreamError(f"{SOURCES[source].name} unreachable: {e.__class__.__name__}")
        if attempt < retries:
            await asyncio.sleep(0.5 * 2 ** attempt)
    raise last or UpstreamError("upstream error")


_cache: TTLCache = TTLCache(maxsize=4096, ttl=30 * 24 * 3600)
_cache_exp: dict[str, float] = {}


def cache_clear() -> None:
    _cache.clear()
    _cache_exp.clear()


async def cached(key_parts: tuple, ttl_s: int, producer: Callable[[], Awaitable[dict]]) -> dict:
    """Cache an envelope dict for ttl_s seconds; a cache hit flips cached=True."""
    key = hashlib.sha256(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()
    hit = _cache.get(key)
    if hit is not None and _cache_exp.get(key, 0) > time.time():
        return {**hit, "cached": True}
    val = await producer()
    _cache[key] = val
    _cache_exp[key] = time.time() + ttl_s
    return val
