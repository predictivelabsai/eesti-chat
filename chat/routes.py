"""Chat routes -- 3-pane UI + SSE streaming."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse

from chat.layout import chat_page
from chat import sse
from db import DB_ENABLED, SCHEMA
from utils.session import (get_user_email, set_user_email, clear_user,
                           get_user_id, set_user_id)

log = logging.getLogger(__name__)

# Number of free questions an anonymous visitor may ask before sign-in is required.
FREE_QUERIES = int(os.getenv("FREE_QUERIES", "5"))

# Light in-memory request throttling. The window is intentionally shared by
# anonymous and authenticated visitors; only the request budget differs.
RATE_LIMIT_ANON = int(os.getenv("RATE_LIMIT_ANON", "20"))
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "60"))
RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_REQUESTS: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else ""


def _prune_rate_limit_cache(cutoff: float) -> None:
    if len(_RATE_LIMIT_REQUESTS) <= 10_000:
        return
    for key, stamps in list(_RATE_LIMIT_REQUESTS.items()):
        if not stamps or stamps[-1] <= cutoff:
            _RATE_LIMIT_REQUESTS.pop(key, None)
    if len(_RATE_LIMIT_REQUESTS) > 10_000:
        oldest = sorted(_RATE_LIMIT_REQUESTS, key=lambda key: _RATE_LIMIT_REQUESTS[key][-1])
        for key in oldest[:len(_RATE_LIMIT_REQUESTS) - 10_000]:
            _RATE_LIMIT_REQUESTS.pop(key, None)


def _rate_limited(request: Request, authenticated: bool) -> bool:
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW
    ip = _client_ip(request)
    recent = [stamp for stamp in _RATE_LIMIT_REQUESTS.get(ip, []) if stamp > cutoff]
    if recent:
        _RATE_LIMIT_REQUESTS[ip] = recent
    else:
        _RATE_LIMIT_REQUESTS.pop(ip, None)

    _prune_rate_limit_cache(cutoff)

    limit = RATE_LIMIT_AUTH if authenticated else RATE_LIMIT_ANON
    if len(recent) >= limit:
        return True
    _RATE_LIMIT_REQUESTS.setdefault(ip, []).append(now)
    _prune_rate_limit_cache(cutoff)
    return False


def _get_db():
    from db import SessionLocal
    return SessionLocal()


def _user_exists(uid) -> bool:
    """Guard against a session cookie that references a deleted/stale user id
    (e.g. after a DB reset) — otherwise inserts hit the FK and 500."""
    if not uid or not DB_ENABLED:
        return False
    from sqlalchemy import text
    db = _get_db()
    try:
        return db.execute(
            text(f"SELECT 1 FROM {SCHEMA}.chat_users WHERE id = :id"), {"id": uid}
        ).fetchone() is not None
    except Exception:
        return False
    finally:
        db.close()


def _ensure_user(sess) -> tuple[int | None, str | None]:
    if not DB_ENABLED:
        return None, None
    email = get_user_email(sess)
    if not email:
        return None, None
    uid = get_user_id(sess)
    if uid and _user_exists(uid):
        return uid, email
    from sqlalchemy import text
    db = _get_db()
    try:
        row = db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_users (email) VALUES (:email) "
                 "ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email "
                 "RETURNING id"),
            {"email": email},
        ).fetchone()
        db.commit()
        uid = row[0]
    finally:
        db.close()
    set_user_id(sess, uid)
    return uid, email


def _ensure_session(user_id, sid, first_message=None):
    from sqlalchemy import text
    db = _get_db()
    try:
        if sid:
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                sid_int = 0
            if sid_int:
                row = db.execute(
                    text(f"SELECT id FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
                    {"sid": sid_int, "uid": user_id},
                ).fetchone()
                if row:
                    return sid_int

        title = (first_message or "New chat")[:80]
        row = db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_sessions (user_id, title) VALUES (:uid, :title) RETURNING id"),
            {"uid": user_id, "title": title},
        ).fetchone()
        db.commit()
        return row[0]
    finally:
        db.close()


def _list_sessions(user_id, limit=30):
    from sqlalchemy import text
    db = _get_db()
    try:
        rows = db.execute(
            text(f"SELECT id, title, agent_slug, updated_at FROM {SCHEMA}.chat_sessions "
                 "WHERE user_id = :uid ORDER BY updated_at DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


def _session_messages(session_id):
    from sqlalchemy import text
    db = _get_db()
    try:
        rows = db.execute(
            text(f"SELECT role, content, agent_slug FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


def _persist_message(session_id, role, content, agent_slug=None, tool_calls=None):
    from sqlalchemy import text
    db = _get_db()
    try:
        db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_messages (session_id, role, content, agent_slug, tool_calls) "
                 "VALUES (:sid, :role, :content, :agent, :tools)"),
            {"sid": session_id, "role": role, "content": content,
             "agent": agent_slug,
             "tools": json.dumps(tool_calls) if tool_calls else None},
        )
        db.execute(
            text(f"UPDATE {SCHEMA}.chat_sessions SET updated_at = now() WHERE id = :sid"),
            {"sid": session_id},
        )
        db.commit()
    finally:
        db.close()


def _ensure_guest(sess) -> int | None:
    """Create/reuse a guest user row for an anonymous visitor so chat history
    persists across their session (multi-turn + sidebar history)."""
    if not DB_ENABLED:
        return None
    uid = get_user_id(sess)
    if uid and _user_exists(uid):
        return uid
    key = sess.get("guest_key")
    if not key:
        import secrets
        key = secrets.token_hex(8)
        sess["guest_key"] = key
    from sqlalchemy import text
    db = _get_db()
    try:
        row = db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_users (email) VALUES (:e) "
                 "ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email RETURNING id"),
            {"e": f"guest+{key}@eesti.local"},
        ).fetchone()
        db.commit()
        uid = row[0]
    finally:
        db.close()
    set_user_id(sess, uid)
    return uid


def register_chat_routes(rt):
    """Register all chat routes on the given FastHTML router."""

    @rt("/app")
    def app_home(sess, sid: str = ""):
        uid, email = _ensure_user(sess)
        if not uid and DB_ENABLED:
            # Returning guest: show their history without creating a new row.
            cached = get_user_id(sess)
            uid = cached if _user_exists(cached) else None
        sessions = _list_sessions(uid) if uid else []
        messages = []
        current_agent = None
        if uid and sid:
            try:
                from sqlalchemy import text
                db = _get_db()
                try:
                    row = db.execute(
                        text(f"SELECT id, agent_slug FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
                        {"sid": int(sid), "uid": uid},
                    ).fetchone()
                    if row:
                        messages = _session_messages(int(sid))
                        current_agent = row._mapping.get("agent_slug")
                finally:
                    db.close()
            except (TypeError, ValueError):
                pass

        from utils.i18n import get_lang
        lang = get_lang(sess)
        return chat_page(
            user_email=email,
            sessions=sessions,
            current_sid=str(sid) if sid else "",
            messages=messages,
            current_agent_slug=current_agent,
            lang=lang,
        )

    @rt("/app/chat", methods=["POST"])
    async def chat_stream(request: Request):
        sess = request.session
        form = await request.form()
        user_msg = (form.get("msg") or "").strip()
        sid_str = form.get("sid") or ""

        if not user_msg:
            return JSONResponse({"error": "empty message"}, status_code=400)

        if _rate_limited(request, bool(get_user_email(sess))):
            return JSONResponse({
                "error": "rate_limited",
                "message": "Too many questions too quickly. Please wait a moment and try again.",
            }, status_code=429)

        uid, email = _ensure_user(sess)

        # --- Free-query gate: N free questions, then require sign-in ---
        # Session changes must happen here (before the streaming response begins),
        # otherwise the updated cookie is never persisted.
        if not email:
            used = int(sess.get("free_q", 0))
            if used >= FREE_QUERIES:
                return JSONResponse({
                    "error": "login_required",
                    "message": (f"You've used your {FREE_QUERIES} free questions. "
                                "Sign in to keep asking eesti.chat."),
                    "free_used": used,
                    "free_limit": FREE_QUERIES,
                }, status_code=402)
            sess["free_q"] = used + 1
            free_remaining = FREE_QUERIES - (used + 1)
        else:
            free_remaining = None

        from agents import router as agent_router
        from agents.registry import by_slug
        agent_slug = agent_router.route(user_msg)
        spec = by_slug(agent_slug)
        stripped_msg = agent_router.strip_prefix(user_msg)

        session_id = 0
        history = []
        if DB_ENABLED:
            # Persist history (multi-turn) for signed-in users and guests alike.
            # Never let a DB hiccup (e.g. a stale user id) 500 the chat — fall
            # back to an ephemeral, unpersisted turn instead.
            try:
                if not uid:
                    uid = _ensure_guest(sess)
                session_id = _ensure_session(uid, sid_str, first_message=user_msg)
                _persist_message(session_id, "user", user_msg)
                history = _session_messages(session_id)[:-1]
            except Exception:
                log.exception("chat persistence failed; continuing ephemerally")
                session_id = 0
                history = []

        async def event_stream():
            yield sse.event("session", {"sid": session_id})
            yield sse.event(sse.AGENT_ROUTE, {
                "slug": agent_slug,
                "agent": spec.name if spec else agent_slug,
                "icon": spec.icon if spec else "*",
            })

            from utils.i18n import get_lang, LANGUAGES
            lang = get_lang(sess)
            lang_info = LANGUAGES.get(lang, LANGUAGES["en"])
            # Hard rule: always answer in the user's selected UI language,
            # regardless of the language of the sources found.
            lang_directive = (
                f"IMPORTANT: Write your ENTIRE response in {lang_info['name']} "
                f"(language code '{lang}'), even though the official sources may be in "
                f"another language. Keep URLs, official names, and proper nouns as-is."
            )
            lc_messages = [SystemMessage(content=lang_directive)]
            for h in history[-20:]:
                if h["role"] == "user":
                    lc_messages.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    lc_messages.append(AIMessage(content=h["content"]))
            lc_messages.append(HumanMessage(content=stripped_msg))

            accumulated = []
            tool_calls_log = []

            try:
                from agents.base import cached_agent
                graph = cached_agent(agent_slug)

                async for event in graph.astream_events({"messages": lc_messages}, version="v2"):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        chunk = event["data"].get("chunk")
                        if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                            if not getattr(chunk, "tool_call_chunks", None):
                                accumulated.append(chunk.content)
                                yield sse.event(sse.TOKEN, {"text": chunk.content})
                    elif kind == "on_tool_start":
                        name = event.get("name", "unknown")
                        args = event["data"].get("input", {})
                        tool_calls_log.append({"name": name, "args": args})
                        yield sse.event(sse.TOOL_START, {"name": name, "args": args})
                    elif kind == "on_tool_end":
                        name = event.get("name", "unknown")
                        raw = event["data"].get("output", "")
                        output = getattr(raw, "content", None) or (raw if isinstance(raw, str) else str(raw))
                        yield sse.event(sse.TOOL_END, {"name": name, "output": output[:2000]})

                        if isinstance(output, str) and "__ARTIFACT__" in output:
                            try:
                                artifact_str = output[output.index("__ARTIFACT__") + len("__ARTIFACT__"):]
                                sep = artifact_str.find("\n\n")
                                if sep != -1:
                                    artifact_str = artifact_str[:sep]
                                payload = json.loads(artifact_str)
                                yield sse.event(sse.ARTIFACT, payload)
                            except Exception:
                                pass
            except Exception as e:
                log.exception("chat stream failed")
                yield sse.event(sse.ERROR, {"message": str(e)})

            final = "".join(accumulated) or "(no response)"
            if DB_ENABLED and session_id:
                _persist_message(session_id, "assistant", final, agent_slug=agent_slug,
                                 tool_calls=tool_calls_log or None)
                from sqlalchemy import text
                db = _get_db()
                try:
                    db.execute(text(f"UPDATE {SCHEMA}.chat_sessions SET agent_slug = :slug WHERE id = :sid"),
                               {"slug": agent_slug, "sid": session_id})
                    db.commit()
                finally:
                    db.close()
            yield sse.event(sse.DONE, {"slug": agent_slug, "tools": len(tool_calls_log),
                                       "free_remaining": free_remaining})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @rt("/app/feedback", methods=["POST"])
    async def chat_feedback(request: Request):
        try:
            try:
                payload = await request.json()
            except Exception:
                payload = dict(await request.form())

            rating = str(payload.get("rating") or "").strip().lower()
            if rating not in {"up", "down"}:
                return JSONResponse({"ok": False, "error": "invalid rating"}, status_code=400)

            sid_value = payload.get("sid")
            session_id = None
            if sid_value not in (None, ""):
                try:
                    session_id = int(sid_value)
                    if session_id < 0:
                        session_id = None
                except (TypeError, ValueError):
                    session_id = None
            content = str(payload.get("content") or "")[:200]
            agent_slug = str(payload.get("agent_slug") or "").strip()[:100] or None

            if DB_ENABLED:
                from sqlalchemy import text
                db = _get_db()
                try:
                    db.execute(
                        text(f"INSERT INTO {SCHEMA}.chat_feedback "
                             "(session_id, msg_content_text, rating, agent_slug) "
                             "VALUES (:sid, :content, :rating, :agent)"),
                        {"sid": session_id, "content": content,
                         "rating": rating, "agent": agent_slug},
                    )
                    db.commit()
                finally:
                    db.close()
            else:
                data_dir = Path("data")
                data_dir.mkdir(parents=True, exist_ok=True)
                record = {
                    "session_id": session_id,
                    "msg_content_text": content,
                    "rating": rating,
                    "agent_slug": agent_slug,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                with (data_dir / "feedback.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            return JSONResponse({"ok": True})
        except Exception:
            log.exception("chat feedback failed; continuing without feedback")
            return JSONResponse({"ok": False, "error": "feedback unavailable"})

    @rt("/app/config", methods=["POST"])
    async def app_config(request: Request):
        from utils.i18n import set_lang, get_lang
        form = await request.form()
        lang_code = (form.get("lang") or "").strip()
        if lang_code:
            set_lang(request.session, lang_code)
        return JSONResponse({"ok": True, "lang": get_lang(request.session)})

    @rt("/app/auth/signin", methods=["POST"])
    async def signin(request: Request):
        form = await request.form()
        email = (form.get("email") or "").strip().lower()
        if "@" not in email:
            return JSONResponse({"ok": False, "error": "invalid email"}, status_code=400)
        set_user_email(request.session, email)
        _ensure_user(request.session)
        return JSONResponse({"ok": True, "email": email})

    @rt("/app/auth/signout", methods=["POST"])
    async def signout(request: Request):
        clear_user(request.session)
        return JSONResponse({"ok": True})

    @rt("/api/share/{sid}", methods=["POST"])
    async def share_session(request: Request, sid: str):
        sess = request.session
        uid, _ = _ensure_user(sess)
        if not uid:
            return JSONResponse({"error": "not signed in"}, status_code=401)
        try:
            sid_int = int(sid)
        except (TypeError, ValueError):
            return JSONResponse({"error": "invalid session"}, status_code=400)
        from sqlalchemy import text
        db = _get_db()
        try:
            row = db.execute(
                text(f"SELECT share_token FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
                {"sid": sid_int, "uid": uid},
            ).fetchone()
            if not row:
                return JSONResponse({"error": "session not found"}, status_code=404)
            token = row[0]
            if not token:
                import secrets
                token = secrets.token_urlsafe(32)
                db.execute(
                    text(f"UPDATE {SCHEMA}.chat_sessions SET share_token = :token WHERE id = :sid"),
                    {"token": token, "sid": sid_int},
                )
                db.commit()
            return JSONResponse({"token": token, "url": f"/shared/{token}"})
        finally:
            db.close()

    @rt("/shared/{token}")
    def shared_chat(token: str):
        from sqlalchemy import text
        db = _get_db()
        try:
            row = db.execute(
                text(f"SELECT s.id, s.title, s.agent_slug, u.email "
                     f"FROM {SCHEMA}.chat_sessions s "
                     f"JOIN {SCHEMA}.chat_users u ON u.id = s.user_id "
                     f"WHERE s.share_token = :token"),
                {"token": token},
            ).fetchone()
            if not row:
                from starlette.responses import HTMLResponse
                return HTMLResponse("<h2>Chat not found</h2>", status_code=404)
            sid = row[0]
            messages = _session_messages(sid)
        finally:
            db.close()

        from chat.layout import shared_chat_page
        return shared_chat_page(
            title=row[1] or "Shared Chat",
            messages=messages,
            agent_slug=row[2],
        )
