(() => {
  'use strict';

  // ====== CONFIG ======
  const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://api.jesselab.space';
  const APEX = 'https://jesselab.space/';

  // ====== STATE ======
  const state = {
    pending: loadPending(),     // queue of {kind, entry, audioBlob?, audioName?, audioMime?}
    recording: null,            // {recorder, chunks, mime, ext, startedAt, timerId}
    me: null,                   // {user_id, email, display_name} once signed in
  };

  // ====== STORAGE ======
  function loadPending() {
    try { return JSON.parse(localStorage.getItem('pending') || '[]'); }
    catch { return []; }
  }
  function savePending() {
    // Audio blobs can't be JSON-serialized — text-only items survive a reload.
    const persistable = state.pending.filter((p) => p.kind === 'text');
    localStorage.setItem('pending', JSON.stringify(persistable));
  }

  // ====== DATE HELPERS ======
  function nowIso() { return new Date().toISOString(); }
  function localDate() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  // ====== API ======
  async function fetchMe() {
    const r = await fetch(`${API_BASE}/v1/me`, { credentials: 'include' });
    if (r.status === 401) return null;
    if (!r.ok) throw new Error(`/v1/me: ${r.status}`);
    return r.json();
  }

  async function postEntry(p) {
    const fd = new FormData();
    fd.set('kind', p.entry.kind);
    fd.set('ts', p.entry.ts);
    fd.set('local_date', p.entry.local_date);
    if (p.entry.body) fd.set('body', p.entry.body);
    if (p.audioBlob) fd.append('audio', p.audioBlob, p.audioName);
    const r = await fetch(`${API_BASE}/v1/journal/entries`, {
      method: 'POST',
      credentials: 'include',
      body: fd,
    });
    if (r.status === 401) {
      window.location.href = APEX;
      throw new Error('not signed in');
    }
    if (!r.ok) {
      const err = await r.text().catch(() => '');
      throw new Error(`POST entries: ${r.status} — ${err.slice(0, 200)}`);
    }
    return r.json();
  }

  async function logout() {
    try {
      await fetch(`${API_BASE}/v1/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch (err) { console.warn('logout failed:', err.message); }
    window.location.href = APEX;
  }

  // ====== ENTRY CREATION ======
  function queueText(body) {
    if (!body.trim()) return;
    const entry = { ts: nowIso(), local_date: localDate(), kind: 'text', body };
    state.pending.push({ kind: 'text', entry });
    savePending();
    renderPending();
    toast(`Saved (queued, ${state.pending.length})`, 'ok');
    sync();
  }

  function queueVoice(blob, mime, ext) {
    const entry = { ts: nowIso(), local_date: localDate(), kind: 'voice', body: '' };
    const audioName = `rec.${ext}`;
    state.pending.push({ kind: 'voice', entry, audioBlob: blob, audioName, audioMime: mime });
    savePending();
    renderPending();
    toast(`Recorded ${(blob.size / 1024).toFixed(0)} KB (queued)`, 'ok');
    sync();
  }

  // ====== SYNC ======
  async function sync() {
    if (state.pending.length === 0) { return; }
    setSyncing(true);
    const survivors = [];
    let n = 0;
    for (const p of state.pending) {
      try { await postEntry(p); n++; }
      catch (err) { survivors.push(p); console.error(err); }
    }
    state.pending = survivors;
    savePending();
    renderPending();
    setSyncing(false);
    if (n > 0 && survivors.length === 0) toast(`Synced ${n}`, 'ok');
    else if (n > 0) toast(`Synced ${n}, ${survivors.length} failed`, 'error');
    else if (survivors.length > 0) toast(`Sync failed (${survivors.length} pending)`, 'error');
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
    return { mime: '', ext: 'webm' };
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

  function renderMe() {
    const el = document.getElementById('me-view');
    if (!el) return;
    el.textContent = state.me
      ? `${state.me.display_name || state.me.email}`
      : 'not signed in';
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
    document.getElementById('settings').hidden = false;
    renderPending();
    renderMe();
  }
  function closeSettings() {
    document.getElementById('settings').hidden = true;
  }

  // ====== AUTH GATE ======
  async function checkAuth() {
    try {
      const me = await fetchMe();
      if (me === null) {
        window.location.href = APEX;
        return false;
      }
      state.me = me;
      renderMe();
      return true;
    } catch (err) {
      // Network error — let the user keep writing offline; sync will surface 401 later.
      console.warn('auth check failed:', err.message);
      return true;
    }
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
    document.getElementById('signout-btn').addEventListener('click', logout);

    document.getElementById('pending-clear').addEventListener('click', () => {
      if (!confirm(`Discard ${state.pending.length} pending entries without syncing?`)) return;
      state.pending = [];
      savePending();
      renderPending();
      toast('Pending cleared', 'ok');
    });

    window.addEventListener('online', () => { sync(); });

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js').catch(() => {});
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    bind();
    renderPending();
    const ok = await checkAuth();
    if (ok) sync();
  });
})();
