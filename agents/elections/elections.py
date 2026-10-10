from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.charts import make_chart

SPEC = AGENTS_BY_SLUG["elections"]
TOOLS = [web_search, make_chart]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
