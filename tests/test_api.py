"""Tests for the eesti.chat API.

Run: pytest tests/test_api.py -v
Requires: server running on localhost:5010 with DB access.
"""

from __future__ import annotations

import json
import os
import time

import httpx
import pytest

BASE = os.environ.get("API_BASE", "http://localhost:5010/api/v1")
TIMEOUT = 60


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE, timeout=TIMEOUT)


@pytest.fixture(scope="module")
def test_email():
    return f"apitest+{int(time.time())}@example.com"


@pytest.fixture(scope="module")
def auth_token(client, test_email):
    resp = client.post("/auth/register", json={
        "email": test_email,
        "password": "testpass123",
        "name": "Test User",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "token" in data
    return data["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Health ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────

class TestAuth:
    def test_register(self, client):
        email = f"reg+{int(time.time())}@example.com"
        resp = client.post("/auth/register", json={
            "email": email,
            "password": "pass123456",
            "name": "Reg User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email
        assert data["name"] == "Reg User"
        assert "token" in data
        assert data["user_id"] > 0

    def test_register_duplicate(self, client, auth_token, test_email):
        resp = client.post("/auth/register", json={
            "email": test_email,
            "password": "otherpass123",
        })
        assert resp.status_code == 409

    def test_login(self, client, test_email):
        resp = client.post("/auth/login", json={
            "email": test_email,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_email
        assert "token" in data

    def test_login_wrong_password(self, client, test_email):
        resp = client.post("/auth/login", json={
            "email": test_email,
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_me(self, client, auth_token, test_email):
        resp = client.get("/auth/me", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_email
        assert data["name"] == "Test User"
        assert data["user_id"] > 0

    def test_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_bad_token(self, client):
        resp = client.get("/auth/me", headers=auth_headers("garbage.token.here"))
        assert resp.status_code == 401


# ── Agents ────────────────────────────────────────────────────────────

class TestAgents:
    def test_list_agents(self, client):
        resp = client.get("/agents")
        assert resp.status_code == 200
        agents = resp.json()
        assert len(agents) >= 5
        slugs = {a["slug"] for a in agents}
        assert {"eresidency", "moving", "tax", "services", "digital", "explore"} <= slugs

    def test_agent_fields(self, client):
        resp = client.get("/agents")
        agent = resp.json()[0]
        assert all(k in agent for k in ["slug", "name", "category", "icon", "one_liner", "prefix", "example_prompts"])
        assert len(agent["example_prompts"]) > 0


# ── Sessions ──────────────────────────────────────────────────────────

class TestSessions:
    def test_list_empty(self, client, auth_token):
        resp = client.get("/sessions", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_anonymous_is_empty(self, client):
        resp = client.get("/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent(self, client, auth_token):
        resp = client.get("/sessions/999999", headers=auth_headers(auth_token))
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client, auth_token):
        resp = client.delete("/sessions/999999", headers=auth_headers(auth_token))
        assert resp.status_code == 404


# ── Chat ──────────────────────────────────────────────────────────────

class TestChat:
    def _stream_chat(self, client, auth_token, message, session_id=None):
        body = {"message": message}
        if session_id:
            body["session_id"] = session_id

        events = []
        with client.stream("POST", "/chat", json=body,
                           headers=auth_headers(auth_token)) as resp:
            assert resp.status_code == 200
            for line in resp.iter_lines():
                if line.startswith("event: "):
                    event_name = line[7:]
                elif line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        data = line[6:]
                    events.append({"event": event_name, "data": data})
        return events

    def test_business_query(self, client, auth_token):
        events = self._stream_chat(client, auth_token, "business: how do I apply for e-Residency?")

        event_types = [e["event"] for e in events]
        assert "session" in event_types, "Should emit session event"
        assert "agent_route" in event_types, "Should emit agent_route event"
        assert "done" in event_types, "Should emit done event"

        session_event = next(e for e in events if e["event"] == "session")
        assert "sid" in session_event["data"]

        route_event = next(e for e in events if e["event"] == "agent_route")
        assert route_event["data"]["slug"] == "eresidency"

        token_events = [e for e in events if e["event"] == "token"]
        assert len(token_events) > 0, "Should stream response tokens"

    def test_services_query(self, client, auth_token):
        events = self._stream_chat(client, auth_token, "gov: how do I renew my Estonian ID card?")

        route_event = next(e for e in events if e["event"] == "agent_route")
        assert route_event["data"]["slug"] == "services"
        assert any(e["event"] == "done" for e in events)

    def test_tax_query(self, client, auth_token):
        events = self._stream_chat(client, auth_token, "tax: how does VAT registration work?")

        route_event = next(e for e in events if e["event"] == "agent_route")
        assert route_event["data"]["slug"] == "tax"
        assert any(e["event"] == "done" for e in events)

    def test_digital_query(self, client, auth_token):
        events = self._stream_chat(client, auth_token, "id: how do I set up Smart-ID?")

        route_event = next(e for e in events if e["event"] == "agent_route")
        assert route_event["data"]["slug"] == "digital"
        assert any(e["event"] == "done" for e in events)

    def test_explore_query(self, client, auth_token):
        events = self._stream_chat(client, auth_token, "estonia: what makes Estonia's digital society distinctive?")

        route_event = next(e for e in events if e["event"] == "agent_route")
        assert route_event["data"]["slug"] == "explore"
        assert any(e["event"] == "done" for e in events)

    def test_session_continuity(self, client, auth_token):
        events1 = self._stream_chat(client, auth_token, "move: how do I register my address in Tallinn?")
        sid = next(e for e in events1 if e["event"] == "session")["data"]["sid"]

        events2 = self._stream_chat(client, auth_token, "what about the diesel ones?", session_id=sid)
        sid2 = next(e for e in events2 if e["event"] == "session")["data"]["sid"]
        assert sid2 == sid, "Should reuse same session"

    def test_chat_empty_message(self, client, auth_token):
        resp = client.post("/chat", json={"message": ""},
                           headers=auth_headers(auth_token))
        assert resp.status_code == 422


# ── Session CRUD after chat ───────────────────────────────────────────

class TestSessionCRUD:
    def test_session_lifecycle(self, client, auth_token):
        # Create session via chat
        events = []
        with client.stream("POST", "/chat",
                           json={"message": "tax: when do I file an income tax return?"},
                           headers=auth_headers(auth_token)) as resp:
            for line in resp.iter_lines():
                if line.startswith("event: "):
                    event_name = line[7:]
                elif line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        data = line[6:]
                    events.append({"event": event_name, "data": data})

        sid = next(e for e in events if e["event"] == "session")["data"]["sid"]

        # List sessions — should include new one
        resp = client.get("/sessions", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        sessions = resp.json()
        sids = [s["id"] for s in sessions]
        assert sid in sids

        # Get session detail
        resp = client.get(f"/sessions/{sid}", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == sid
        assert len(detail["messages"]) >= 2

        # Share session
        resp = client.post(f"/sessions/{sid}/share", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        share = resp.json()
        assert "token" in share
        assert share["url"].startswith("/shared/")

        # Delete session
        resp = client.delete(f"/sessions/{sid}", headers=auth_headers(auth_token))
        assert resp.status_code == 200

        # Verify deleted
        resp = client.get(f"/sessions/{sid}", headers=auth_headers(auth_token))
        assert resp.status_code == 404
