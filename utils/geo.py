"""IP → country-code geolocation (adapted from the CityTicker pattern).

Layered and best-effort, pure stdlib, no API key:
  1. CDN/proxy country headers (instant, free)
  2. Free HTTP geolocation APIs (ipapi.co, then ip-api.com) — cached per IP
  3. Emergency hand-curated IP-prefix list (offline last resort)
Returns a lowercase 2-letter ISO country code, or None if undetermined.
Never raises; keep the timeout short so a slow API can't block page render.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request

log = logging.getLogger(__name__)

_LOOKUP_ENABLED = os.getenv("GEO_IP_LOOKUP", "1") == "1"
_PREFIX_FALLBACK = os.getenv("GEO_IP_PREFIX_FALLBACK", "1") == "1"
_TIMEOUT = float(os.getenv("GEO_IP_TIMEOUT", "1.5"))
_CACHE_TTL = int(os.getenv("GEO_IP_CACHE_TTL", "86400"))  # 24h

# Emergency offline prefixes (only EE — our primary non-English audience).
_EMERGENCY_PREFIXES: dict[str, tuple[str, ...]] = {
    "ee": ("85.253.", "90.190.", "84.50.", "213.168.", "195.50.",
           "62.65.", "88.196.", "86.43.", "193.40.", "194.126.", "213.35."),
}

_CDN_COUNTRY_HEADERS = (
    "cf-ipcountry",            # Cloudflare
    "x-vercel-ip-country",     # Vercel
    "cloudfront-viewer-country",  # AWS CloudFront
    "x-country-code",
)

# ip -> (timestamp, country_code|None)
_CACHE: dict[str, tuple[float, str | None]] = {}
_CACHE_MAX = 4096


def get_client_ip(request) -> str | None:
    if request is None:
        return None
    try:
        headers = getattr(request, "headers", {}) or {}
        fwd = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For") or ""
        if fwd:
            return fwd.split(",")[0].strip()
        real = headers.get("x-real-ip") or headers.get("X-Real-IP") or ""
        if real:
            return real.strip()
        client = getattr(request, "client", None)
        return client.host if client else None
    except Exception:
        return None


def _is_private(ip: str) -> bool:
    return (not ip or ip.startswith(("127.", "10.", "192.168.", "169.254.", "::1", "fc", "fd"))
            or ip.startswith("172.") and ip.split(".")[1:2] and 16 <= int(ip.split(".")[1]) <= 31)


def _http_get_text(url: str) -> str | None:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "eesti.chat-geo/1.0 (+https://eesti.chat)"}, method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace").strip()
    except Exception as e:
        log.debug("geo http get failed (%s): %s", url, e)
        return None


def _country_from_headers(headers) -> str | None:
    try:
        for key in _CDN_COUNTRY_HEADERS:
            raw = headers.get(key) or headers.get(key.upper()) or headers.get(key.title())
            if not raw:
                continue
            code = raw.strip().lower()
            if len(code) == 2 and code.isalpha() and code not in ("xx", "t1"):
                return code
    except Exception:
        pass
    return None


def _lookup_country_api(ip: str) -> str | None:
    now = time.time()
    hit = _CACHE.get(ip)
    if hit and (now - hit[0]) < _CACHE_TTL:
        return hit[1]

    country: str | None = None
    if _LOOKUP_ENABLED and not _is_private(ip):
        text = _http_get_text(f"https://ipapi.co/{ip}/country_code/")
        if text and len(text) == 2 and text.isalpha():
            country = text.lower()
        if country is None:
            text = _http_get_text(f"http://ip-api.com/json/{ip}?fields=status,countryCode")
            if text:
                try:
                    data = json.loads(text)
                    if data.get("status") == "success" and data.get("countryCode"):
                        country = str(data["countryCode"]).lower()
                except Exception:
                    pass

    # Cache the result (including None) to avoid re-hitting the APIs.
    if len(_CACHE) >= _CACHE_MAX:
        for k in list(_CACHE.keys())[:1024]:
            _CACHE.pop(k, None)
    _CACHE[ip] = (now, country)
    return country


def _country_from_prefixes(ip: str) -> str | None:
    if not _PREFIX_FALLBACK or not ip:
        return None
    for code, prefixes in _EMERGENCY_PREFIXES.items():
        if any(ip.startswith(p) for p in prefixes):
            return code
    return None


def country_from_request(request) -> str | None:
    """Best-effort lowercase ISO country code for the request, or None."""
    try:
        headers = getattr(request, "headers", {}) or {}
        code = _country_from_headers(headers)
        if code:
            return code
        ip = get_client_ip(request)
        if not ip or _is_private(ip):
            return _country_from_prefixes(ip or "")
        return _lookup_country_api(ip) or _country_from_prefixes(ip)
    except Exception:
        return None
