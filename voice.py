"""Voice mode — a WebSocket proxy between the browser and xAI speech-to-speech.

The browser cannot set an Authorization header, so /ws/voice holds XAI_API_KEY and
bridges mic audio to wss://api.x.ai/v1/realtime. Audio is PCM16 mono at 24 kHz.
Server-side VAD handles turn-taking. The spoken voice is the same built-in voice
the xAI voice API uses by default (eve); override with XAI_VOICE.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import websockets as wslib
from starlette.websockets import WebSocket, WebSocketDisconnect

log = logging.getLogger(__name__)

DEFAULT_VOICE = "eve"
DEFAULT_MODEL = "grok-voice-latest"
FREE_QUERIES = int(os.environ.get("FREE_QUERIES", "5"))

# Short on purpose. The voice model speaks this; the typed agents keep the long prompt.
VOICE_INSTRUCTIONS = """You are the voice of eesti.chat, an independent guide to Estonian public services. You are not a government official and you do not give legal advice.

Speak in short, plain sentences. Answer in the language the person is speaking. Cover e-Residency and running an Estonian company, taxes, moving and residence, digital ID, everyday public services, and the 2027 Riigikogu election. On the election, stay neutral and do not endorse a party.

For fees, steps, eligibility, deadlines, or rates, use web search and prefer official Estonian sites such as eesti.ee, e-resident.gov.ee, emta.ee, politsei.ee, ria.ee, id.ee, rik.ee, and valimised.ee. If you cannot verify a figure, say so and name the authority to check. Never invent a fee, a deadline, or a URL.

Do not read URLs, markdown, or a sources list aloud. Name the institution in the sentence. When the topic is legal, tax, or immigration, add one short line that this is general information and they should confirm it on the official site before acting.
"""

KEYTERMS = [
    "eesti.chat", "e-Residency", "e-resident", "Smart-ID", "Mobiil-ID",
    "X-Tee", "X-Road", "Riigikogu", "e-MTA", "eesti.ee", "OÜ", "Tervisekassa",
    "valimised", "EMTA", "RIA",
]


def voice_name() -> str:
    return (os.environ.get("XAI_VOICE") or DEFAULT_VOICE).strip() or DEFAULT_VOICE


def api_key() -> str:
    return (os.environ.get("XAI_API_KEY") or "").strip()


def voice_model() -> str:
    return (os.environ.get("XAI_VOICE_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL


def realtime_url() -> str:
    return f"wss://api.x.ai/v1/realtime?model={voice_model()}"


def voice_block_reason(session: dict | None) -> str | None:
    """Refuse voice once an anonymous visitor has used the typed free-question allowance.

    The session cookie is readable on the socket. It is only rewritten on an HTTP
    response, so a voice turn does not itself increment the counter.
    """
    sess = session or {}
    if sess.get("chat_email"):
        return None
    try:
        used = int(sess.get("free_q") or 0)
    except (TypeError, ValueError):
        used = 0
    if used >= FREE_QUERIES:
        return (
            f"You've used your {FREE_QUERIES} free questions. "
            "Sign in to keep talking with eesti.chat."
        )
    return None


def build_session_update() -> dict:
    return {
        "type": "session.update",
        "session": {
            # Top-level voice is ignored by grok-voice-think-fast-2.0. The live
            # field is audio.output.voice. Both are set so either shape applies.
            "voice": voice_name(),
            "instructions": VOICE_INSTRUCTIONS,
            "turn_detection": {"type": "server_vad"},
            "tools": [{"type": "web_search"}],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "transcription": {
                        "model": "grok-transcribe",
                        "keyterms": KEYTERMS,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "voice": voice_name(),
                },
            },
            "replace": {
                "eesti.chat": "Eesti chat",
                "X-Tee": "cross tee",
            },
        },
    }


def _client_event(event: dict) -> dict | None:
    """Map an xAI server event onto the small set static/voice.js understands."""
    t = event.get("type") or ""
    if t in ("response.output_audio.delta", "response.audio.delta"):
        return {"type": "audio", "audio": event.get("delta") or event.get("audio") or ""}
    if t in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
        return {"type": "assistant_delta", "text": event.get("delta", "")}
    if t in ("response.output_audio_transcript.done", "response.audio_transcript.done"):
        return {"type": "assistant_done", "text": event.get("transcript", "")}
    if t in (
        "input_audio_buffer.input_audio_transcription.completed",
        "conversation.item.input_audio_transcription.completed",
    ):
        return {"type": "user_transcript", "text": event.get("transcript", "")}
    if t in (
        "input_audio_buffer.input_audio_transcription.updated",
        "conversation.item.input_audio_transcription.updated",
    ):
        return {"type": "user_partial", "text": event.get("transcript", "")}
    if t == "input_audio_buffer.speech_started":
        return {"type": "speech_started"}
    if t == "input_audio_buffer.speech_stopped":
        return {"type": "speech_stopped"}
    if t == "response.done":
        return {"type": "done"}
    if t == "error":
        return {"type": "error", "message": json.dumps(event.get("error", event))[:300]}
    return None


async def _voice_ws(ws: WebSocket):
    await ws.accept()
    blocked = voice_block_reason(ws.scope.get("session"))
    if blocked:
        await ws.send_json({"type": "error", "message": blocked})
        await ws.close()
        return

    key = api_key()
    if not key:
        await ws.send_json({"type": "error", "message": "voice not configured (no XAI_API_KEY)"})
        await ws.close()
        return

    headers = {"Authorization": f"Bearer {key}"}
    try:
        async with wslib.connect(realtime_url(), additional_headers=headers, max_size=None) as xai:
            await xai.send(json.dumps(build_session_update()))
            await ws.send_json({"type": "ready"})

            async def browser_to_xai():
                while True:
                    msg = json.loads(await ws.receive_text())
                    mt = msg.get("type")
                    if mt == "audio":
                        await xai.send(json.dumps(
                            {"type": "input_audio_buffer.append", "audio": msg.get("audio", "")}))
                    elif mt == "commit":
                        await xai.send(json.dumps({"type": "input_audio_buffer.commit"}))
                        await xai.send(json.dumps({"type": "response.create"}))
                    elif mt == "cancel":
                        await xai.send(json.dumps({"type": "response.cancel"}))

            async def xai_to_browser():
                async for raw in xai:
                    if isinstance(raw, bytes):
                        continue
                    event = json.loads(raw)
                    out = _client_event(event)
                    if out:
                        await ws.send_json(out)

            _, pending = await asyncio.wait(
                [asyncio.create_task(browser_to_xai()), asyncio.create_task(xai_to_browser())],
                return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
    except WebSocketDisconnect:
        pass
    except Exception as ex:  # noqa: BLE001
        log.warning("voice proxy error: %s", ex)
        try:
            await ws.send_json({"type": "error", "message": str(ex)[:200]})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


def register_voice_routes(app):
    """Attach /ws/voice at the front of the router so a catch-all cannot shadow it."""
    from starlette.routing import WebSocketRoute
    app.router.routes.insert(0, WebSocketRoute("/ws/voice", _voice_ws))
