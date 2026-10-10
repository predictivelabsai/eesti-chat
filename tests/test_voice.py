"""Voice proxy: session shape, free-question gate, and the composer control."""

from fasthtml.common import to_xml
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.testclient import TestClient

from chat.components import center_pane
from voice import (
    build_session_update,
    realtime_url,
    register_voice_routes,
    voice_block_reason,
    _client_event,
)


def test_session_uses_builtin_voice_and_project_key_shape(monkeypatch):
    monkeypatch.delenv("XAI_VOICE", raising=False)
    monkeypatch.delenv("XAI_VOICE_MODEL", raising=False)
    session = build_session_update()["session"]
    assert session["voice"] == "eve"
    assert session["audio"]["output"]["voice"] == "eve"
    assert "eesti.chat" in session["instructions"]
    assert session["tools"] == [{"type": "web_search"}]
    assert session["reasoning"] == {"effort": "none"}
    assert session["audio"]["input"]["format"]["rate"] == 24000
    assert "e-Residency" in session["audio"]["input"]["transcription"]["keyterms"]
    assert "model=grok-voice-latest" in realtime_url()


def test_voice_event_aliases():
    assert _client_event({"type": "response.audio.delta", "delta": "abc"}) == {
        "type": "audio", "audio": "abc",
    }
    assert _client_event({"type": "response.done"}) == {"type": "done"}
    assert _client_event({"type": "session.updated"}) is None


def test_anonymous_free_limit_blocks_voice():
    assert voice_block_reason({"free_q": 5})
    assert voice_block_reason({"free_q": 5, "chat_email": "a@b.c"}) is None
    assert voice_block_reason({}) is None


def test_missing_key_closes_socket(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "")
    app = Starlette()
    register_voice_routes(app)
    assert isinstance(app.router.routes[0], WebSocketRoute)
    assert app.router.routes[0].path == "/ws/voice"
    with TestClient(app) as client:
        with client.websocket_connect("/ws/voice") as ws:
            msg = ws.receive_json()
    assert msg["type"] == "error"
    assert "XAI_API_KEY" in msg["message"]


def test_composer_has_voice_button():
    html = to_xml(center_pane(messages=None, current_agent_slug=None, lang="en"))
    assert 'id="voice-btn"' in html
    assert "toggleVoice(event)" in html
    assert 'aria-label="Talk"' in html
