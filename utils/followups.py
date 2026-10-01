"""Generate context-sensitive follow-up question suggestions after an answer.

A separate, best-effort LLM call (never blocks or breaks the answer). Mirrors the
pattern used in ai-indurent: propose a few short follow-ups grounded in the Q+A,
returned as a plain JSON array of strings, tolerant-parsed.
"""

from __future__ import annotations

import json
import logging
import re

log = logging.getLogger(__name__)

_FENCE = re.compile(r"```(?:json)?|```", re.IGNORECASE)


def _parse_labels(text: str) -> list[str]:
    """Tolerant parse: raw JSON array, or {followups|questions|suggestions|items: [...]},
    or a list of dicts with label|question|text. Falls back to the first [...] block."""
    if not text:
        return []
    cleaned = _FENCE.sub("", text).strip()
    data = None
    try:
        data = json.loads(cleaned)
    except Exception:
        m = re.search(r"\[.*\]", cleaned, re.S)
        if m:
            try:
                data = json.loads(m.group(0))
            except Exception:
                data = None
    if data is None:
        return []
    items = data
    if isinstance(data, dict):
        for k in ("followups", "follow_ups", "questions", "suggestions", "items"):
            if isinstance(data.get(k), list):
                items = data[k]
                break
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for it in items:
        if isinstance(it, str):
            s = it
        elif isinstance(it, dict):
            s = it.get("label") or it.get("question") or it.get("text") or ""
        else:
            s = ""
        s = " ".join(str(s).split()).strip().strip('"').lstrip("0123456789.) -").strip()
        if s and len(s) <= 140:
            out.append(s)
    return out


def generate_followups(question: str, answer: str, lang_name: str = "English",
                       agent_name: str = "", n: int = 3) -> list[str]:
    """Return up to `n` short follow-up questions in `lang_name`, grounded in the Q+A.
    Returns [] on any problem (caller falls back to default starters)."""
    if not answer or len(answer.strip()) < 60:
        return []
    try:
        from utils.llm import build_llm
        topic = f" ({agent_name})" if agent_name else ""
        prompt = (
            "You suggest the next questions a user is likely to ask in a chat about Estonia"
            f"{topic} — e-Residency, digital ID, taxes, moving, and public services.\n\n"
            "Read the user's question and the assistant's answer below. Propose "
            f"{n} short, natural follow-up questions that:\n"
            "- dig deeper into specifics raised in the answer (a fee, step, deadline, "
            "document, eligibility rule or option), not generic boilerplate;\n"
            "- stay on the same topic and can be answered by the assistant from official sources;\n"
            "- are phrased as something the user would type next.\n"
            f"Write EVERY suggestion in {lang_name}. Keep each under ~70 characters, no numbering.\n"
            "Return ONLY a JSON array of strings. No prose.\n\n"
            f"USER QUESTION:\n{question[:1000]}\n\n"
            f"ASSISTANT ANSWER:\n{answer[:4000]}"
        )
        llm = build_llm(temperature=0)
        resp = llm.invoke(prompt).content
        labels = _parse_labels(resp if isinstance(resp, str) else str(resp))
        # de-dupe and drop anything echoing the original question verbatim
        seen, out = set(), []
        q_norm = " ".join(question.lower().split())
        for s in labels:
            key = s.lower()
            if key in seen or key == q_norm:
                continue
            seen.add(key)
            out.append(s)
        return out[:n]
    except Exception as e:
        log.warning("followups generation failed: %s", e)
        return []
