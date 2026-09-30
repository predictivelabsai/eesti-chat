"""FastAPI application for the eesti.chat API.

Mounted at /api/v1 by main.py and also runnable standalone with
``python -m api.app``.
"""

from __future__ import annotations

import json
import logging
import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.account_deletion import delete_user_data
from api.auth import create_token
from api.deps import get_current_user, get_db, get_optional_user
from api.schemas import (
    AgentOut,
    AuthResponse,
    ChatRequest,
    ContactRequest,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    SessionDetail,
    SessionSummary,
    ShareResponse,
    SharedSessionOut,
    UpdateProfileRequest,
    UserInfo,
    UserProfileOut,
)
from auth.utils import hash_password, verify_password
from db import SCHEMA

log = logging.getLogger(__name__)


def create_app(root_path: str = "") -> FastAPI:
    """Build the API. The /api/v1 prefix is supplied by main.py's mount."""
    api = FastAPI(
        title="eesti.chat API",
        description="API for eesti.chat — AI guidance for Estonian public services",
        version="1.0.0",
        root_path=root_path,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    # ── Authentication ──────────────────────────────────────────────

    @api.post("/auth/register", response_model=AuthResponse, tags=["auth"])
    def register(body: RegisterRequest, db: Session = Depends(get_db)):
        existing = db.execute(
            text(f"SELECT id, password_hash FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()
        if existing and existing.password_hash:
            raise HTTPException(409, "An account with this email already exists")

        pw_hash = hash_password(body.password)
        if existing:
            db.execute(
                text(f"UPDATE {SCHEMA}.chat_users SET password_hash = :pw, name = :name, is_verified = TRUE WHERE email = :email"),
                {"pw": pw_hash, "name": body.name, "email": body.email},
            )
            db.commit()
            uid = existing.id
        else:
            row = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_users (email, password_hash, name, is_verified) "
                     "VALUES (:email, :pw, :name, TRUE) RETURNING id"),
                {"email": body.email, "pw": pw_hash, "name": body.name},
            ).fetchone()
            db.commit()
            uid = row[0]

        return AuthResponse(token=create_token(uid, body.email), email=body.email,
                            name=body.name, user_id=uid)

    @api.post("/auth/login", response_model=AuthResponse, tags=["auth"])
    def login(body: LoginRequest, db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, email, password_hash, name FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()
        if not row or not row.password_hash or not verify_password(body.password, row.password_hash):
            raise HTTPException(401, "Invalid email or password")
        return AuthResponse(token=create_token(row.id, row.email), email=row.email,
                            name=row.name or "", user_id=row.id)

    @api.post("/auth/google", response_model=AuthResponse, tags=["auth"])
    def google_auth(body: dict, db: Session = Depends(get_db)):
        """Validate a Google ID token and return an API token."""
        import urllib.request

        id_token = body.get("id_token")
        if not id_token:
            raise HTTPException(400, "id_token is required")
        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            with urllib.request.urlopen(url, timeout=10) as response:
                info = json.loads(response.read())
        except Exception as exc:
            raise HTTPException(401, f"Invalid Google token: {exc}") from exc

        email = info.get("email")
        if not email or info.get("email_verified") != "true":
            raise HTTPException(401, "Email not verified")
        name = info.get("name", "")

        row = db.execute(
            text(f"SELECT id, name FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": email},
        ).fetchone()
        if row:
            uid = row.id
            name = row.name or name
        else:
            row = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_users (email, name, is_verified) "
                     "VALUES (:email, :name, TRUE) RETURNING id"),
                {"email": email, "name": name},
            ).fetchone()
            db.commit()
            uid = row[0]

        return AuthResponse(token=create_token(uid, email), email=email,
                            name=name, user_id=uid)

    @api.get("/auth/me", response_model=UserInfo, tags=["auth"])
    def me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, email, name FROM {SCHEMA}.chat_users WHERE id = :id"),
            {"id": user["user_id"]},
        ).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return UserInfo(user_id=row.id, email=row.email, name=row.name or "")

    @api.delete("/auth/account", tags=["auth"])
    def delete_account(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        if not delete_user_data(db, user["user_id"]):
            raise HTTPException(404, "User not found")
        return {"ok": True}

    # ── Agents ───────────────────────────────────────────────────────

    @api.get("/agents", response_model=list[AgentOut], tags=["agents"])
    def list_agents():
        from agents.registry import AGENTS

        return [
            AgentOut(
                slug=agent.slug,
                name=agent.name,
                category=agent.category,
                icon=agent.icon,
                one_liner=agent.one_liner,
                prefix=agent.prefix,
                example_prompts=list(agent.example_prompts),
            )
            for agent in AGENTS
        ]

    # ── Sessions ─────────────────────────────────────────────────────

    def _uid(user: dict | None) -> int:
        return int((user or {}).get("sub", 0))

    @api.get("/sessions", response_model=list[SessionSummary], tags=["sessions"])
    def list_sessions(limit: int = 30, user: dict | None = Depends(get_optional_user),
                      db: Session = Depends(get_db)):
        rows = db.execute(
            text(f"SELECT id, title, agent_slug, updated_at FROM {SCHEMA}.chat_sessions "
                 "WHERE user_id = :uid ORDER BY updated_at DESC LIMIT :lim"),
            {"uid": _uid(user), "lim": min(limit, 100)},
        ).fetchall()
        return [SessionSummary(id=row.id, title=row.title, agent_slug=row.agent_slug,
                               updated_at=str(row.updated_at)) for row in rows]

    @api.get("/sessions/{session_id}", response_model=SessionDetail, tags=["sessions"])
    def get_session(session_id: int, user: dict | None = Depends(get_optional_user),
                    db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, title, agent_slug FROM {SCHEMA}.chat_sessions "
                 "WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": _uid(user)},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        messages = db.execute(
            text(f"SELECT role, content, agent_slug FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        return SessionDetail(
            id=row.id,
            title=row.title,
            agent_slug=row.agent_slug,
            messages=[MessageOut(role=msg.role, content=msg.content,
                                 agent_slug=msg.agent_slug) for msg in messages],
        )

    @api.delete("/sessions/{session_id}", tags=["sessions"])
    def delete_session(session_id: int, user: dict | None = Depends(get_optional_user),
                       db: Session = Depends(get_db)):
        uid = _uid(user)
        row = db.execute(
            text(f"SELECT id FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": uid},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        db.execute(text(f"DELETE FROM {SCHEMA}.chat_messages WHERE session_id = :sid"),
                   {"sid": session_id})
        db.execute(text(f"DELETE FROM {SCHEMA}.chat_sessions WHERE id = :sid"),
                   {"sid": session_id})
        db.commit()
        return {"ok": True}

    @api.post("/sessions/{session_id}/share", response_model=ShareResponse, tags=["sessions"])
    def share_session(session_id: int, user: dict | None = Depends(get_optional_user),
                      db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT share_token FROM {SCHEMA}.chat_sessions "
                 "WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": _uid(user)},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")
        token = row.share_token or secrets.token_urlsafe(32)
        if not row.share_token:
            db.execute(text(f"UPDATE {SCHEMA}.chat_sessions SET share_token = :token WHERE id = :sid"),
                       {"token": token, "sid": session_id})
            db.commit()
        return ShareResponse(token=token, url=f"/shared/{token}")

    @api.get("/shared/{token}", response_model=SharedSessionOut, tags=["sessions"])
    def get_shared_session(token: str, db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, title, agent_slug FROM {SCHEMA}.chat_sessions WHERE share_token = :token"),
            {"token": token},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Shared session not found")
        messages = db.execute(
            text(f"SELECT role, content, agent_slug FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": row.id},
        ).fetchall()
        return SharedSessionOut(
            title=row.title or "Shared Chat",
            agent_slug=row.agent_slug,
            messages=[MessageOut(role=msg.role, content=msg.content,
                                 agent_slug=msg.agent_slug) for msg in messages],
        )

    # ── Chat (SSE streaming) ─────────────────────────────────────────

    @api.post("/chat", tags=["chat"], responses={
        200: {"content": {"text/event-stream": {}},
              "description": "SSE stream of chat events"},
    })
    def chat(body: ChatRequest, user: dict | None = Depends(get_optional_user),
             db: Session = Depends(get_db)):
        uid = _uid(user)
        session_id = None
        if body.session_id:
            row = db.execute(
                text(f"SELECT id FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
                {"sid": body.session_id, "uid": uid},
            ).fetchone()
            session_id = row.id if row else None
        if not session_id:
            row = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_sessions (user_id, title) "
                     "VALUES (:uid, :title) RETURNING id"),
                {"uid": uid, "title": body.message[:80]},
            ).fetchone()
            db.commit()
            session_id = row[0]

        from agents import router as agent_router
        from agents.registry import by_slug

        agent_slug = agent_router.route(body.message)
        spec = by_slug(agent_slug)
        db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_messages (session_id, role, content) "
                 "VALUES (:sid, 'user', :content)"),
            {"sid": session_id, "content": body.message},
        )
        db.commit()
        history_rows = db.execute(
            text(f"SELECT role, content FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        history = [{"role": row.role, "content": row.content} for row in history_rows[:-1]]
        stripped_msg = agent_router.strip_prefix(body.message)

        async def event_stream():
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
            from utils.i18n import LANGUAGES

            yield _sse_event("session", {"sid": session_id})
            yield _sse_event("agent_route", {
                "slug": agent_slug,
                "agent": spec.name if spec else agent_slug,
                "icon": spec.icon if spec else "*",
            })

            lang_info = LANGUAGES.get(body.lang, LANGUAGES["en"])
            lang_directive = ""
            if body.lang != "en":
                lang_directive = f"\nUser language: {body.lang} ({lang_info['name']}). Respond in {lang_info['name']}."
            system = (
                "You are an eesti.chat assistant for Estonian public services. "
                "Respond helpfully and concisely."
            )
            lc_messages = [SystemMessage(content=system + lang_directive)]
            for item in history[-20:]:
                if item["role"] == "user":
                    lc_messages.append(HumanMessage(content=item["content"]))
                elif item["role"] == "assistant":
                    lc_messages.append(AIMessage(content=item["content"]))
            lc_messages.append(HumanMessage(content=stripped_msg))

            accumulated: list[str] = []
            tool_calls_log: list[dict] = []
            try:
                from agents.base import cached_agent

                graph = cached_agent(agent_slug)
                async for event in graph.astream_events({"messages": lc_messages}, version="v2"):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        chunk = event["data"].get("chunk")
                        if (chunk and hasattr(chunk, "content") and isinstance(chunk.content, str)
                                and chunk.content and not getattr(chunk, "tool_call_chunks", None)):
                            accumulated.append(chunk.content)
                            yield _sse_event("token", {"text": chunk.content})
                    elif kind == "on_tool_start":
                        name = event.get("name", "unknown")
                        args = event["data"].get("input", {})
                        tool_calls_log.append({"name": name, "args": args})
                        yield _sse_event("tool_start", {"name": name, "args": args})
                    elif kind == "on_tool_end":
                        name = event.get("name", "unknown")
                        raw = event["data"].get("output", "")
                        output = getattr(raw, "content", None) or (raw if isinstance(raw, str) else str(raw))
                        yield _sse_event("tool_end", {"name": name, "output": output[:2000]})
            except Exception as exc:
                log.exception("chat stream failed")
                yield _sse_event("error", {"message": str(exc)})

            final = "".join(accumulated) or "(no response)"
            from db import SessionLocal

            persist_db = SessionLocal()
            try:
                persist_db.execute(
                    text(f"INSERT INTO {SCHEMA}.chat_messages "
                         "(session_id, role, content, agent_slug, tool_calls) "
                         "VALUES (:sid, 'assistant', :content, :agent, :tools)"),
                    {"sid": session_id, "content": final, "agent": agent_slug,
                     "tools": json.dumps(tool_calls_log) if tool_calls_log else None},
                )
                persist_db.execute(
                    text(f"UPDATE {SCHEMA}.chat_sessions SET agent_slug = :slug, updated_at = now() "
                         "WHERE id = :sid"),
                    {"slug": agent_slug, "sid": session_id},
                )
                persist_db.commit()
            finally:
                persist_db.close()
            yield _sse_event("done", {"slug": agent_slug, "tools": len(tool_calls_log)})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ── Profile ──────────────────────────────────────────────────────

    @api.get("/user/profile", response_model=UserProfileOut, tags=["profile"])
    def get_profile(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        uid = user["user_id"]
        account = db.execute(
            text(f"SELECT name, email FROM {SCHEMA}.chat_users WHERE id = :id"),
            {"id": uid},
        ).fetchone()
        if not account:
            raise HTTPException(404, "User not found")
        row = db.execute(
            text(f"SELECT * FROM {SCHEMA}.user_profiles WHERE user_id = :uid"),
            {"uid": uid},
        ).fetchone()
        profile = dict(row._mapping) if row else {}
        return UserProfileOut(
            name=account.name or "",
            email=account.email,
            phone=profile.get("phone") or "",
            country=profile.get("country") or "",
            city=profile.get("city") or "",
            currency=profile.get("currency") or "EUR",
            language=profile.get("language") or "en",
        )

    @api.post("/user/profile", tags=["profile"])
    def update_profile(body: UpdateProfileRequest, user: dict = Depends(get_current_user),
                       db: Session = Depends(get_db)):
        uid = user["user_id"]
        if body.name is not None:
            db.execute(text(f"UPDATE {SCHEMA}.chat_users SET name = :name WHERE id = :id"),
                       {"name": body.name, "id": uid})

        fields = {}
        for field in ("phone", "country", "city", "currency", "language"):
            value = getattr(body, field)
            if value is not None:
                fields[field] = value

        existing = db.execute(
            text(f"SELECT user_id FROM {SCHEMA}.user_profiles WHERE user_id = :uid"),
            {"uid": uid},
        ).fetchone()
        if existing:
            if fields:
                set_clause = ", ".join(f"{key} = :{key}" for key in fields)
                db.execute(text(f"UPDATE {SCHEMA}.user_profiles SET {set_clause}, updated_at = NOW() "
                                "WHERE user_id = :uid"), {**fields, "uid": uid})
        else:
            fields["user_id"] = uid
            columns = ", ".join(fields)
            values = ", ".join(f":{key}" for key in fields)
            db.execute(text(f"INSERT INTO {SCHEMA}.user_profiles ({columns}) VALUES ({values})"), fields)
        db.commit()
        return {"ok": True}

    @api.post("/contact", tags=["contact"])
    def submit_contact(body: ContactRequest):
        log.info("Contact form: name=%s email=%s message=%s", body.name, body.email, body.message[:200])
        return {"ok": True, "message": "Thank you for your message. We will get back to you soon."}

    return api


def _sse_event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=str)}\n\n"


api_router = create_app()


if __name__ == "__main__":
    import uvicorn

    standalone = create_app(root_path="/api/v1")
    uvicorn.run(standalone, host="0.0.0.0", port=5012)
