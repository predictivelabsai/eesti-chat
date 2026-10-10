/* Voice mode — mic ↔ xAI speech-to-speech over /ws/voice (PCM16 mono @ 24kHz). */
(() => {
    const RATE = 24000;
    const SPEECH_RMS = 0.02;
    const SILENCE_MS = 800;
    const $ = (s) => document.querySelector(s);
    const $$ = (s) => Array.from(document.querySelectorAll(s));

    let ws = null, active = false, armed = false;
    let micCtx = null, playCtx = null, stream = null, node = null, srcNode = null, zeroGain = null;
    let nextTime = 0, playing = [];
    let asstBubble = null, lineEl = null;
    let statusEl = null, anchorForm = null;
    let localSpeech = false, quietMs = 0, sentCommit = false, serverVad = false;
    let audioAt = 0;

    function i18n(key, fallback) {
        const el = document.getElementById("i18n-data");
        if (!el || !el._voiceMap) {
            try { el && (el._voiceMap = JSON.parse(el.textContent || "{}")); }
            catch (e) { if (el) el._voiceMap = {}; }
        }
        const map = (el && el._voiceMap) || {};
        return map[key] || fallback;
    }

    function paintButtons() {
        $$(".voice-btn").forEach((btn) => {
            btn.classList.toggle("active", active);
            btn.setAttribute("aria-pressed", active ? "true" : "false");
        });
    }

    function setStatus(state, label) {
        const p = $("#voice-panel");
        if (p) p.setAttribute("data-state", state);
        if (statusEl) statusEl.textContent = label;
        paintButtons();
    }
    function setLine(text) {
        if (lineEl) lineEl.textContent = text || "";
    }
    function showPanel(form) {
        if ($("#voice-panel")) return;
        const p = document.createElement("div");
        p.id = "voice-panel";
        p.className = "voice-panel";
        p.setAttribute("data-state", "connecting");
        p.innerHTML =
            '<span class="voice-orb" aria-hidden="true"></span>' +
            '<span class="voice-copy">' +
            '<span class="voice-status" id="voice-status"></span>' +
            '<span class="voice-line" id="voice-line"></span>' +
            '</span>' +
            '<button type="button" class="voice-stop" id="voice-stop"></button>';
        anchorForm = form || $(".chat-form") || $(".hero-prompt-form") || $(".ask-bubble-form");
        if (anchorForm && anchorForm.parentElement) anchorForm.parentElement.insertBefore(p, anchorForm);
        else document.body.appendChild(p);
        statusEl = $("#voice-status");
        lineEl = $("#voice-line");
        statusEl.textContent = i18n("voice_connecting", "Connecting…");
        const stop = $("#voice-stop");
        stop.textContent = i18n("voice_end", "End voice");
        stop.onclick = stopVoice;
    }
    function hidePanel() {
        const p = $("#voice-panel");
        if (p) p.remove();
        statusEl = null;
        lineEl = null;
    }

    function addBubble(role, text) {
        const m = $("#messages");
        if (!m) return null;
        const wrap = document.createElement("div");
        wrap.className = `msg msg-${role}`;
        const b = document.createElement("div");
        b.className = "msg-bubble";
        b.textContent = text || "";
        wrap.appendChild(b);
        m.appendChild(wrap);
        m.scrollTop = m.scrollHeight;
        return b;
    }

    function floatToPCM16(f32) {
        const out = new Int16Array(f32.length);
        for (let i = 0; i < f32.length; i++) {
            let s = Math.max(-1, Math.min(1, f32[i]));
            out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return out;
    }
    function downsample(f32, inRate) {
        if (inRate === RATE) return floatToPCM16(f32);
        const ratio = inRate / RATE, outLen = Math.floor(f32.length / ratio);
        const out = new Int16Array(outLen);
        for (let i = 0; i < outLen; i++) {
            const start = Math.floor(i * ratio), end = Math.floor((i + 1) * ratio);
            let sum = 0, c = 0;
            for (let j = start; j < end && j < f32.length; j++) { sum += f32[j]; c++; }
            let s = c ? sum / c : (f32[start] || 0);
            s = Math.max(-1, Math.min(1, s));
            out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return out;
    }
    function b64FromInt16(int16) {
        const bytes = new Uint8Array(int16.buffer, int16.byteOffset, int16.byteLength);
        let bin = "";
        for (let i = 0; i < bytes.length; i += 0x8000)
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        return btoa(bin);
    }
    function rmsOf(f32) {
        let sum = 0;
        for (let i = 0; i < f32.length; i++) sum += f32[i] * f32[i];
        return Math.sqrt(sum / (f32.length || 1));
    }
    function playPCM16(b64) {
        if (!playCtx || !b64) return;
        if (playCtx.state === "suspended") playCtx.resume();
        const bin = atob(b64), bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const int16 = new Int16Array(bytes.buffer), f32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) f32[i] = int16[i] / 0x8000;
        const buf = playCtx.createBuffer(1, f32.length, RATE);
        buf.getChannelData(0).set(f32);
        const s = playCtx.createBufferSource();
        s.buffer = buf; s.connect(playCtx.destination);
        const now = playCtx.currentTime;
        if (nextTime < now) nextTime = now;
        s.start(nextTime); nextTime += buf.duration;
        s.onended = () => { playing = playing.filter((x) => x !== s); };
        playing.push(s);
        audioAt = performance.now();
    }
    function stopPlayback() {
        playing.forEach((s) => { try { s.stop(); } catch (e) {} });
        playing = []; nextTime = 0;
    }
    function resetTurn() {
        localSpeech = false;
        quietMs = 0;
        sentCommit = false;
        serverVad = false;
    }

    async function startVoice(ev) {
        if (active) return;
        dismissHint();
        const wh = $("#welcome-hero"); if (wh) wh.style.display = "none";
        const from = ev && ev.currentTarget && ev.currentTarget.closest
            ? ev.currentTarget.closest("form") : null;
        showPanel(from);
        setStatus("connecting", i18n("voice_mic", "Requesting microphone…"));
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
            });
        } catch (e) {
            setStatus("error", i18n("voice_mic_blocked", "Microphone blocked. Allow access and tap the mic again."));
            setTimeout(hidePanel, 4000);
            return;
        }
        active = true;
        armed = false;
        resetTurn();
        paintButtons();
        const AC = window.AudioContext || window.webkitAudioContext;
        micCtx = new AC();
        try { playCtx = new AC({ sampleRate: RATE }); }
        catch (e) { playCtx = new AC(); }
        try { await micCtx.resume(); await playCtx.resume(); } catch (e) {}

        const proto = location.protocol === "https:" ? "wss" : "ws";
        ws = new WebSocket(`${proto}://${location.host}/ws/voice`);
        ws.onopen = () => setStatus("connecting", i18n("voice_connecting", "Connecting…"));
        ws.onclose = () => { if (active) stopVoice(); };
        ws.onerror = () => setStatus("error", i18n("voice_error", "Voice error"));
        ws.onmessage = (ev) => {
            try { handle(JSON.parse(ev.data)); }
            catch (e) { setStatus("error", i18n("voice_error", "Voice error")); }
        };

        srcNode = micCtx.createMediaStreamSource(stream);
        node = micCtx.createScriptProcessor(4096, 1, 1);
        zeroGain = micCtx.createGain(); zeroGain.gain.value = 0;
        srcNode.connect(node); node.connect(zeroGain); zeroGain.connect(micCtx.destination);
        node.onaudioprocess = (e) => {
            if (!armed || !ws || ws.readyState !== 1) return;
            const f32 = e.inputBuffer.getChannelData(0);
            const rms = rmsOf(f32);
            const frameMs = (f32.length / micCtx.sampleRate) * 1000;
            if (rms >= SPEECH_RMS) {
                localSpeech = true;
                quietMs = 0;
            } else if (localSpeech) {
                quietMs += frameMs;
                // Server VAD sometimes never closes a laptop-mic turn. Commit
                // the buffer ourselves once the room goes quiet.
                if (!serverVad && !sentCommit && quietMs >= SILENCE_MS) {
                    sentCommit = true;
                    ws.send(JSON.stringify({ type: "commit" }));
                    setStatus("thinking", i18n("voice_thinking", "Thinking…"));
                }
            }
            const pcm = downsample(f32, micCtx.sampleRate);
            ws.send(JSON.stringify({ type: "audio", audio: b64FromInt16(pcm) }));
        };
    }

    function stopVoice() {
        active = false;
        armed = false;
        resetTurn();
        try { node && node.disconnect(); } catch (e) {}
        try { srcNode && srcNode.disconnect(); } catch (e) {}
        try { stream && stream.getTracks().forEach((t) => t.stop()); } catch (e) {}
        stopPlayback();
        try { micCtx && micCtx.close(); } catch (e) {}
        try { playCtx && playCtx.close(); } catch (e) {}
        try { ws && ws.close(); } catch (e) {}
        ws = micCtx = playCtx = stream = node = srcNode = null;
        asstBubble = null;
        hidePanel();
        paintButtons();
    }

    function handle(m) {
        switch (m.type) {
            case "ready":
                armed = true;
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "speech_started":
                serverVad = true;
                // Ignore the echo of our own voice for a moment, or the reply
                // is cut off the instant it starts.
                if (audioAt && performance.now() - audioAt < 800) break;
                stopPlayback();
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "speech_stopped":
                serverVad = true;
                sentCommit = true;
                setStatus("thinking", i18n("voice_thinking", "Thinking…"));
                break;
            case "user_transcript":
                if (m.text) {
                    addBubble("user", m.text);
                    setLine(m.text);
                }
                asstBubble = null;
                break;
            case "assistant_delta":
                if (!asstBubble) asstBubble = addBubble("assistant", "") || { textContent: "" };
                asstBubble.textContent += m.text || "";
                setLine(asstBubble.textContent);
                { const mm = $("#messages"); if (mm) mm.scrollTop = mm.scrollHeight; }
                setStatus("speaking", i18n("voice_speaking", "Speaking…"));
                break;
            case "audio":
                playPCM16(m.audio);
                setStatus("speaking", i18n("voice_speaking", "Speaking…"));
                break;
            case "assistant_done":
                if (m.text) setLine(m.text);
                asstBubble = null;
                break;
            case "done":
                resetTurn();
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "error":
                setStatus("error", m.message || i18n("voice_error", "Voice error"));
                setLine(m.message || "");
                addBubble("assistant", (m.message || i18n("voice_error", "Voice error")));
                break;
        }
    }

    function dismissHint() {
        const h = $("#voice-hint");
        if (h) h.remove();
        try { localStorage.setItem("eesti_voice_hint", "1"); } catch (e) {}
    }
    function maybeShowHint() {
        try { if (localStorage.getItem("eesti_voice_hint")) return; } catch (e) {}
        const form = $(".chat-form"), btn = $("#voice-btn");
        if (!form || !btn || !form.parentElement) return;
        const h = document.createElement("div");
        h.id = "voice-hint";
        h.className = "voice-hint";
        h.innerHTML =
            '<span><strong></strong> <span class="voice-hint-body"></span></span>' +
            '<button type="button" class="voice-hint-x" aria-label="Dismiss">&times;</button>';
        h.querySelector("strong").textContent = i18n("voice_hint_title", "You can talk.");
        h.querySelector(".voice-hint-body").textContent = i18n(
            "voice_hint_body",
            "Tap the microphone to ask out loud. Your browser will ask to use the microphone."
        );
        form.parentElement.insertBefore(h, form);
        h.querySelector(".voice-hint-x").onclick = dismissHint;
        setTimeout(() => { const x = $("#voice-hint"); if (x) x.remove(); }, 15000);
    }

    window.toggleVoice = (ev) => { active ? stopVoice() : startVoice(ev); };

    if (document.readyState !== "loading") maybeShowHint();
    else document.addEventListener("DOMContentLoaded", maybeShowHint);
})();
