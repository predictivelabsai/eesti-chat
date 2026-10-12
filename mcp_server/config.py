"""MCP server configuration (env vars, all optional)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class MCPSettings:
    host: str = field(default_factory=lambda: os.environ.get("MCP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _int("MCP_PORT", 8000))
    data_dir: str = field(default_factory=lambda: os.environ.get("MCP_DATA_DIR", "./data"))
    # Comma-separated sha256 hex digests of issued API keys (never store raw keys).
    api_key_hashes: frozenset[str] = field(default_factory=lambda: frozenset(
        h.strip().lower() for h in os.environ.get("MCP_API_KEY_HASHES", "").split(",") if h.strip()))
    anon_rpm: int = field(default_factory=lambda: _int("MCP_ANON_RPM", 30))
    anon_rpd: int = field(default_factory=lambda: _int("MCP_ANON_RPD", 500))
    key_rpm: int = field(default_factory=lambda: _int("MCP_KEY_RPM", 300))
    key_rpd: int = field(default_factory=lambda: _int("MCP_KEY_RPD", 20000))
    bulk_autoload: bool = field(default_factory=lambda: os.environ.get("MCP_BULK_AUTOLOAD", "1") == "1")
    bulk_max_age_h: int = field(default_factory=lambda: _int("MCP_BULK_MAX_AGE_H", 24))
    exa_api_key: str = field(default_factory=lambda: os.environ.get("EXA_API_KEY", ""))
    user_agent: str = field(default_factory=lambda: os.environ.get(
        "MCP_USER_AGENT", "eesti.chat-mcp/0.1 (+https://eesti.chat)"))
    trust_proxy: bool = field(default_factory=lambda: os.environ.get("MCP_TRUST_PROXY", "1") == "1")


@lru_cache(maxsize=1)
def mcp_settings() -> MCPSettings:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:  # pragma: no cover
        pass
    return MCPSettings()
