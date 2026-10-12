"""API-key auth + per-client rate limiting for the HTTP transport (pure ASGI middleware).

- No key  -> anonymous tier (MCP_ANON_RPM / MCP_ANON_RPD per client IP).
- Valid key (Authorization: Bearer <key> or X-API-Key: <key>) -> key tier (MCP_KEY_RPM / MCP_KEY_RPD).
- Invalid key -> 401. Over limit -> 429 with Retry-After.
Keys are configured as sha256 hex digests in MCP_API_KEY_HASHES; generate one with
`python -m mcp_server.keys new`.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque

from mcp_server.config import MCPSettings


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


class _Window:
    """Sliding-window counter for one client (minute + day)."""
    __slots__ = ("minute", "day")

    def __init__(self):
        self.minute: deque[float] = deque()
        self.day: deque[float] = deque()

    def hit(self, now: float, rpm: int, rpd: int) -> float | None:
        while self.minute and now - self.minute[0] >= 60:
            self.minute.popleft()
        while self.day and now - self.day[0] >= 86400:
            self.day.popleft()
        if len(self.minute) >= rpm:
            return 60 - (now - self.minute[0])
        if len(self.day) >= rpd:
            return 86400 - (now - self.day[0])
        self.minute.append(now)
        self.day.append(now)
        return None


class AuthRateLimitMiddleware:
    def __init__(self, app, settings: MCPSettings, protected_prefix: str = "/mcp"):
        self.app = app
        self.s = settings
        self.prefix = protected_prefix
        self.windows: dict[str, _Window] = {}

    def _client_ip(self, scope) -> str:
        headers = dict(scope.get("headers") or [])
        if self.s.trust_proxy:
            xff = headers.get(b"x-forwarded-for", b"").decode().split(",")[0].strip()
            if xff:
                return xff
        client = scope.get("client") or ("unknown", 0)
        return client[0]

    async def _reject(self, send, status: int, msg: str, retry_after: float | None = None):
        headers = [(b"content-type", b"application/json")]
        if retry_after is not None:
            headers.append((b"retry-after", str(int(retry_after) + 1).encode()))
        if status == 401:
            headers.append((b"www-authenticate", b'Bearer realm="eesti-mcp"'))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": json.dumps({"error": msg}).encode()})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith(self.prefix):
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers") or [])
        raw = headers.get(b"x-api-key", b"").decode().strip()
        auth = headers.get(b"authorization", b"").decode().strip()
        if not raw and auth.lower().startswith("bearer "):
            raw = auth[7:].strip()
        if raw:
            h = hash_key(raw)
            if h not in self.s.api_key_hashes:
                return await self._reject(send, 401, "invalid API key")
            ident, rpm, rpd, tier = f"key:{h[:16]}", self.s.key_rpm, self.s.key_rpd, "key"
        else:
            ident, rpm, rpd, tier = f"ip:{self._client_ip(scope)}", self.s.anon_rpm, self.s.anon_rpd, "anonymous"
        win = self.windows.setdefault(ident, _Window())
        wait = win.hit(time.time(), rpm, rpd)
        if wait is not None:
            return await self._reject(send, 429, f"rate limit exceeded ({tier} tier: {rpm}/min, {rpd}/day)", wait)
        if len(self.windows) > 50000:  # crude memory guard
            self.windows.clear()
        scope.setdefault("state", {})["mcp_tier"] = tier
        return await self.app(scope, receive, send)
