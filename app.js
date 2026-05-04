(() => {
  'use strict';

  // ====== CONFIG ======
  const CFG = {
    owner: 'Jesse-vdR',
    repo: 'Jesse',
    branch: 'main',
    entriesPath: 'journal/entries.jsonl',
    audioDir: 'journal/audio',
  };
  const API = `https://api.github.com/repos/${CFG.owner}/${CFG.repo}`;

  // ====== STATE ======
  const state = {
    pat: localStorage.getItem('pat') || '',
    pending: loadPending(),     // queue of {kind, entry, audioBlob?, audioName?, audioMime?}
    recording: null,            // {recorder, chunks, mime, ext, startedAt, timerId}
  };

  // ====== STORAGE ======
  function loadPending() {
    try {
      const raw = JSON.parse(localStorage.getItem('pending') || '[]');
      // Audio blobs can't be JSON-serialized; we only persist text-only items here.
      // In-memory pending may also include audio items that haven't been persisted.
      return raw;
    } catch { return []; }
  }
  function savePending() {
    // Persist only text items; audio is lost on reload (held in memory only) — see README.
    const persistable = state.pending.filter((p) => p.kind === 'text');
    localStorage.setItem('pending', JSON.stringify(persistable));
  }
  function savePat(pat) {
    state.pat = pat;
    if (pat) localStorage.setItem('pat', pat);
    else localStorage.removeItem('pat');
  }

  // ====== DATE HELPERS ======
  function nowIso() { return new Date().toISOString(); }
  function localDate() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  function fileSafeIso() {
    return nowIso().replace(/[:.]/g, '-');
  }

  // ====== GITHUB API ======
  async function ghGet(path) {
    const r = await fetch(`${API}/contents/${path}?ref=${CFG.branch}`, {
      headers: {
        Authorization: `Bearer ${state.pat}`,
        Accept: 'application/vnd.github+json',
      },
    });
    if (r.status === 404) return null;
    if (!r.ok) {
      const body = await r.text();
      throw new Error(`GET ${path}: ${r.status} — ${body.slice(0, 200)}`);
    }
    const j = await r.json();
    const bytes = Uint8Array.from(atob(j.content.replace(/\n/g, '')), (c) => c.charCodeAt(0));
    const text = new TextDecoder('utf-8').decode(bytes);
    return { text, sha: j.sha };
  }

  async function ghPutText(path, text, sha, message) {
    const bytes = new TextEncoder().encode(text);
    let bin = '';
    for (const b of bytes) bin += String.fromCharCode(b);
    return ghPutB64(path, btoa(bin), sha, message);
  }

  async function ghPutBlob(path, blob, message) {
    const buf = await blob.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let bin = '';
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return ghPutB64(path, btoa(bin), null, message);
  }

  async function ghPutB64(path, b64, sha, message) {
    const body = { message, content: b64, branch: CFG.branch };
    if (sha) body.sha = sha;
    const r = await fetch(`${API}/contents/${path}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${state.pat}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      const e = new Error(`PUT ${path}: ${r.status} — ${err.message || 'unknown'}`);
      e.status = r.status;
      throw e;
    }
    return r.json();
  }

  // ====== ENTRY CREATION ======
  function queueText(body) {
    if (!body.trim()) return;
    const entry = { ts: nowIso(), local_date: localDate(), kind: 'text', body };
    state.pending.push({ kind: 'text', entry });
    savePending();
    renderPending();
    toast(`Saved (queued, ${state.pending.length})`, 'ok');
  }

  function queueVoice(blob, mime, ext) {
    const ts = nowIso();
    const filename = `${fileSafeIso()}.${ext}`;
    const audioPath = `${CFG.audioDir}/${filename}`;
    const entry = { ts, local_date: localDate(), kind: 'voice', audio: audioPath };
    state.pending.push({ kind: 'voice', entry, audioBlob: blob, audioName: filename, audioMime: mime });
    savePending();
    renderPending();
    toast(`Recorded ${(blob.size / 1024).toFixed(0)} KB (queued)`, 'ok');
  }

  // ====== SYNC ======
  async function sync() {
    if (!state.pat) { openSettings(); toast('Add a PAT first', 'error'); return; }
    if (state.pending.length === 0) { toast('Nothing to sync', 'ok'); return; }

    setSyncing(true);
    try {
      // 1) Upload any pending audio blobs first (independent files; no sha conflict possible).
      for (const p of state.pending) {
        if (p.kind === 'voice' && p.audioBlob) {
          await ghPutBlob(`${CFG.audioDir}/${p.audioName}`, p.audioBlob, `journal: voice ${p.audioName}`);
          delete p.audioBlob; // free memory
        }
      }

      // 2) Fetch current entries.jsonl, append, PUT back. Single file = single sha race.
      const cur = await ghGet(CFG.entriesPath);
      const existing = cur ? cur.text : '';
      const sha = cur ? cur.sha : null;
      const appended = state.pending.map((p) => JSON.stringify(p.entry)).join('\n') + '\n';
      const next = (existing && !existing.endsWith('\n') ? existing + '\n' : existing) + appended;
      const n = state.pending.length;
      await ghPutText(CFG.entriesPath, next, sha, `journal: +${n} entries`);

      state.pending = [];
      savePending();
      renderPending();
      toast(`Synced ${n}`, 'ok');
    } catch (err) {
      console.error(err);
      toast(err.message || 'Sync failed', 'error');
    } finally {
      setSyncing(false);
    }
  }

  // ====== RECORDING ======
  function pickMime() {
    const candidates = [
      ['audio/webm;codecs=opus', 'webm'],
      ['audio/webm', 'webm'],
      ['audio/mp4', 'm4a'],
      ['audio/ogg;codecs=opus', 'ogg'],
    ];
    if (typeof MediaRecorder === 'undefined') return null;
    for (const [m, ext] of candidates) {
      if (MediaRecorder.isTypeSupported(m)) return { mime: m, ext };
    }
    return { mime: '', ext: 'webm' }; // browser default
  }

  async function startRecording() {
    if (state.recording) return;
    const pick = pickMime();
    if (!pick) { toast('Audio recording not supported here', 'error'); return; }

    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      toast('Mic permission denied', 'error');
      return;
    }

    const opts = pick.mime ? { mimeType: pick.mime } : {};
    const recorder = new MediaRecorder(stream, opts);
    const chunks = [];
    recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: pick.mime || 'audio/webm' });
      stream.getTracks().forEach((t) => t.stop());
      queueVoice(blob, pick.mime || 'audio/webm', pick.ext);
      state.recording = null;
      updateRecordingUI();
    };

    state.recording = {
      recorder, chunks, mime: pick.mime, ext: pick.ext, startedAt: Date.now(), timerId: null,
    };
    state.recording.timerId = setInterval(updateRecordingUI, 250);
    recorder.start();
    updateRecordingUI();
  }

  function stopRecording() {
    if (!state.recording) return;
    clearInterval(state.recording.timerId);
    state.recording.recorder.stop();
  }

  function updateRecordingUI() {
    const status = document.getElementById('rec-status');
    const time = document.getElementById('rec-time');
    const btn = document.getElementById('rec-btn');
    if (state.recording) {
      const sec = Math.floor((Date.now() - state.recording.startedAt) / 1000);
      const m = Math.floor(sec / 60);
      const s = String(sec % 60).padStart(2, '0');
      time.textContent = `${m}:${s}`;
      status.hidden = false;
      btn.textContent = '■ Stop';
      btn.classList.add('recording');
    } else {
      status.hidden = true;
      btn.textContent = '● Record';
      btn.classList.remove('recording');
    }
  }

  // ====== UI ======
  function setSyncing(on) {
    const btn = document.getElementById('sync-btn');
    btn.disabled = on;
    btn.textContent = on ? 'Syncing…' : `Sync${state.pending.length ? ' (' + state.pending.length + ')' : ''}`;
  }

  function renderPending() {
    const btn = document.getElementById('sync-btn');
    btn.textContent = `Sync${state.pending.length ? ' (' + state.pending.length + ')' : ''}`;
    const view = document.getElementById('pending-view');
    if (view) {
      view.textContent = state.pending.length === 0
        ? '—'
        : state.pending.map((p) => JSON.stringify(p.entry)).join('\n');
    }
  }

  function toast(msg, kind) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = kind || '';
    el.hidden = false;
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { el.hidden = true; }, 2400);
  }

  function openSettings() {
    document.getElementById('pat-input').value = state.pat;
    document.getElementById('settings').hidden = false;
    renderPending();
  }

  function closeSettings() {
    document.getElementById('settings').hidden = true;
  }

  // ====== WIRING ======
  function bind() {
    document.getElementById('save-btn').addEventListener('click', () => {
      const ta = document.getElementById('entry');
      const body = ta.value;
      if (!body.trim()) return;
      queueText(body);
      ta.value = '';
    });

    document.getElementById('rec-btn').addEventListener('click', () => {
      if (state.recording) stopRecording(); else startRecording();
    });

    document.getElementById('sync-btn').addEventListener('click', () => { sync(); });
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    document.getElementById('settings-close').addEventListener('click', closeSettings);

    document.getElementById('pat-save').addEventListener('click', () => {
      const v = document.getElementById('pat-input').value.trim();
      savePat(v);
      toast(v ? 'Token saved' : 'Token cleared', 'ok');
      closeSettings();
    });

    document.getElementById('pat-clear').addEventListener('click', () => {
      savePat('');
      document.getElementById('pat-input').value = '';
      toast('Token cleared', 'ok');
    });

    document.getElementById('pending-clear').addEventListener('click', () => {
      if (!confirm(`Discard ${state.pending.length} pending entries without syncing?`)) return;
      state.pending = [];
      savePending();
      renderPending();
      toast('Pending cleared', 'ok');
    });

    // Service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js').catch(() => {});
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    bind();
    renderPending();
  });
})();
