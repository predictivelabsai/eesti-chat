from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search

SPEC = AGENTS_BY_SLUG["services"]
TOOLS = [web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
