/* Voice mode — mic ↔ xAI speech-to-speech over /ws/voice (PCM16 mono @ 24kHz). */
(() => {
    const RATE = 24000;
    const $ = (s) => document.querySelector(s);

    let ws = null, active = false;
    let micCtx = null, playCtx = null, stream = null, node = null, srcNode = null, zeroGain = null;
    let nextTime = 0, playing = [];
    let asstBubble = null;
    let statusEl = null;

    function i18n(key, fallback) {
        const el = document.getElementById("i18n-data");
        if (!el || !el._voiceMap) {
            try { el && (el._voiceMap = JSON.parse(el.textContent || "{}")); }
            catch (e) { if (el) el._voiceMap = {}; }
        }
        const map = (el && el._voiceMap) || {};
        return map[key] || fallback;
    }

    function setStatus(state, label) {
        const p = $("#voice-panel");
        if (p) p.setAttribute("data-state", state);
        if (statusEl) statusEl.textContent = label;
        const btn = $("#voice-btn");
        if (btn) {
            btn.classList.toggle("active", active);
            btn.setAttribute("aria-pressed", active ? "true" : "false");
        }
    }
    function showPanel() {
        if ($("#voice-panel")) return;
        const p = document.createElement("div");
        p.id = "voice-panel";
        p.className = "voice-panel";
        p.setAttribute("data-state", "connecting");
        p.innerHTML =
            '<span class="voice-orb" aria-hidden="true"></span>' +
            '<span class="voice-status" id="voice-status"></span>' +
            '<button type="button" class="voice-stop" id="voice-stop"></button>';
        const form = $(".chat-form");
        if (form && form.parentElement) form.parentElement.insertBefore(p, form);
        statusEl = $("#voice-status");
        statusEl.textContent = i18n("voice_connecting", "Connecting…");
        const stop = $("#voice-stop");
        stop.textContent = i18n("voice_end", "End voice");
        stop.onclick = stopVoice;
    }
    function hidePanel() {
        const p = $("#voice-panel");
        if (p) p.remove();
        statusEl = null;
    }

    function addBubble(role, text) {
        const wrap = document.createElement("div");
        wrap.className = `msg msg-${role}`;
        const b = document.createElement("div");
        b.className = "msg-bubble";
        b.textContent = text || "";
        wrap.appendChild(b);
        const m = $("#messages");
        if (m) { m.appendChild(wrap); m.scrollTop = m.scrollHeight; }
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
        const bytes = new Uint8Array(int16.buffer);
        let bin = "";
        for (let i = 0; i < bytes.length; i += 0x8000)
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        return btoa(bin);
    }
    function playPCM16(b64) {
        if (!playCtx || !b64) return;
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
    }
    function stopPlayback() {
        playing.forEach((s) => { try { s.stop(); } catch (e) {} });
        playing = []; nextTime = 0;
    }

    async function startVoice() {
        if (active) return;
        dismissHint();
        const wh = $("#welcome-hero"); if (wh) wh.style.display = "none";
        showPanel();
        setStatus("connecting", i18n("voice_mic", "Requesting microphone…"));
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
            });
        } catch (e) {
            setStatus("error", i18n("voice_mic_blocked", "Microphone blocked. Allow access and tap the mic again."));
            setTimeout(hidePanel, 4000);
            return;
        }
        active = true;
        micCtx = new (window.AudioContext || window.webkitAudioContext)();
        playCtx = new (window.AudioContext || window.webkitAudioContext)();
        try { await micCtx.resume(); await playCtx.resume(); } catch (e) {}

        const proto = location.protocol === "https:" ? "wss" : "ws";
        ws = new WebSocket(`${proto}://${location.host}/ws/voice`);
        ws.onopen = () => setStatus("listening", i18n("voice_listening", "Listening…"));
        ws.onclose = () => { if (active) stopVoice(); };
        ws.onerror = () => setStatus("error", i18n("voice_error", "Voice error"));
        ws.onmessage = (ev) => {
            try { handle(JSON.parse(ev.data)); }
            catch (e) {}
        };

        srcNode = micCtx.createMediaStreamSource(stream);
        node = micCtx.createScriptProcessor(4096, 1, 1);
        zeroGain = micCtx.createGain(); zeroGain.gain.value = 0;
        srcNode.connect(node); node.connect(zeroGain); zeroGain.connect(micCtx.destination);
        node.onaudioprocess = (e) => {
            if (!ws || ws.readyState !== 1) return;
            const pcm = downsample(e.inputBuffer.getChannelData(0), micCtx.sampleRate);
            ws.send(JSON.stringify({ type: "audio", audio: b64FromInt16(pcm) }));
        };
    }

    function stopVoice() {
        active = false;
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
        const btn = $("#voice-btn");
        if (btn) {
            btn.classList.remove("active");
            btn.setAttribute("aria-pressed", "false");
        }
    }

    function handle(m) {
        switch (m.type) {
            case "ready":
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "speech_started":
                stopPlayback();
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "speech_stopped":
                setStatus("thinking", i18n("voice_thinking", "Thinking…"));
                break;
            case "user_transcript":
                if (m.text) addBubble("user", m.text);
                asstBubble = null;
                break;
            case "assistant_delta":
                if (!asstBubble) asstBubble = addBubble("assistant", "");
                asstBubble.textContent += m.text || "";
                { const mm = $("#messages"); if (mm) mm.scrollTop = mm.scrollHeight; }
                setStatus("speaking", i18n("voice_speaking", "Speaking…"));
                break;
            case "audio":
                playPCM16(m.audio);
                break;
            case "assistant_done":
                asstBubble = null;
                break;
            case "done":
                setStatus("listening", i18n("voice_listening", "Listening…"));
                break;
            case "error":
                setStatus("error", i18n("voice_error", "Voice error"));
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

    window.toggleVoice = () => { active ? stopVoice() : startVoice(); };

    if (document.readyState !== "loading") maybeShowHint();
    else document.addEventListener("DOMContentLoaded", maybeShowHint);
})();
