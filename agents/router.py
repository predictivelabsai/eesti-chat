"""3-tier agent routing: prefix match -> keyword heuristics -> LLM fallback."""

from __future__ import annotations

import logging
import re

from agents.registry import AGENTS, AGENTS_BY_SLUG

log = logging.getLogger(__name__)

_PREFIX_MAP: dict[str, str] = {a.prefix.rstrip(":"): a.slug for a in AGENTS if a.prefix}

_SLUG_KEYWORDS: dict[str, list[str]] = {
    "eresidency": ["e-residency", "e-resident", "eresidency", "company", "oü", "ou ",
                   "start a business", "register a company", "startup", "business bank",
                   "annual report", "invoice", "founder", "incorporat"],
    "tax": ["tax", "vat", "income tax", "corporate tax", "emta", "e-tax", "declaration",
            "declare", "social tax", "fie", "sole proprietor", "deduction", "refund"],
    "moving": ["move to estonia", "moving", "residence permit", "visa", "relocat",
               "digital nomad", "register my address", "personal code", "id code",
               "work permit", "study permit", "immigration", "settle"],
    "digital": ["digital id", "e-id", "eid", "id card", "smart-id", "smart id",
                "mobiil-id", "mobile-id", "digital signature", "sign a document",
                "x-road", "x-tee", "e-service", "log in", "authenticat", "once-only"],
    "services": ["health", "insurance", "tervisekassa", "doctor", "school", "education",
                 "university", "benefit", "pension", "family", "parental", "child",
                 "voting", "i-voting", "vote", "passport", "renew", "marriage", "birth"],
    "explore": ["why estonia", "e-estonia", "digital society", "culture", "history",
                "tourism", "visit", "tallinn", "travel", "about estonia", "story",
                "invest", "innovation", "startup nation"],
}


def _prefix_match(message: str) -> str | None:
    m = re.match(r"^(\w+):\s", message.strip())
    if not m:
        return None
    prefix = m.group(1).lower()
    return _PREFIX_MAP.get(prefix)


def _keyword_scores(message: str) -> dict[str, int]:
    lower = message.lower()
    scores: dict[str, int] = {}
    for slug, keywords in _SLUG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[slug] = score
    return scores


def _llm_classify(message: str) -> str:
    try:
        from utils.llm import build_llm
        slugs = ", ".join(AGENTS_BY_SLUG.keys())
        prompt = (
            f"Classify this user message into exactly one of these agent slugs: {slugs}\n"
            f"Message: {message}\n"
            f"Reply with ONLY the slug, nothing else."
        )
        llm = build_llm(temperature=0)
        resp = llm.invoke(prompt).content.strip().lower()
        if resp in AGENTS_BY_SLUG:
            return resp
    except Exception as e:
        log.warning("LLM classify failed: %s", e)
    return "explore"


def route(message: str) -> str:
    slug = _prefix_match(message)
    if slug:
        return slug

    scores = _keyword_scores(message)
    if scores:
        return max(scores, key=scores.get)

    return _llm_classify(message)


def strip_prefix(message: str) -> str:
    return re.sub(r"^\w+:\s*", "", message.strip())
