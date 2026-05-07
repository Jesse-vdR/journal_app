import { Shell } from "/shell/shell.js";

// ====== CONFIG ======
  const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://api.jesselab.space';
  const APEX = 'https://jesselab.space/';

  // ====== STATE ======
  const state = {
    view: 'list',                // 'list' | 'detail'
    currentDate: null,           // 'YYYY-MM-DD' when view === 'detail'
    dates: [],                   // [{date, count}, ...] desc
    entries: [],                 // entries for currentDate, asc by ts
    lastSaved: '',               // last persisted text-block for the open date — used to skip blur saves when clean
    pending: loadPending(),      // queue of {kind, entry, audioBlob?, audioName?, audioMime?}
    recording: null,
  };

  // ====== STORAGE ======
  function loadPending() {
    try { return JSON.parse(localStorage.getItem('pending') || '[]'); }
    catch { return []; }
  }
  function savePending() {
    const persistable = state.pending.filter((p) => p.kind === 'text');
    localStorage.setItem('pending', JSON.stringify(persistable));
  }

  // ====== DATE HELPERS ======
  function nowIso() { return new Date().toISOString(); }
  function localDateStr(d = new Date()) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  function humanDate(yyyymmdd) {
    const today = localDateStr();
    if (yyyymmdd === today) return `Today · ${yyyymmdd}`;
    const d = new Date(yyyymmdd + 'T00:00:00');
    const yest = new Date(); yest.setDate(yest.getDate() - 1);
    if (yyyymmdd === localDateStr(yest)) return `Yesterday · ${yyyymmdd}`;
    return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  }
  function timeOfDay(isoTs) {
    const d = new Date(isoTs);
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }

  // ====== API ======
  async function apiFetch(path, opts = {}) {
    const r = await fetch(`${API_BASE}${path}`, { credentials: 'include', ...opts });
    if (r.status === 401) {
      window.location.href = APEX;
      throw new Error('not signed in');
    }
    return r;
  }

  async function fetchDates() {
    const r = await apiFetch('/v1/journal/dates');
    if (!r.ok) throw new Error(`GET dates: ${r.status}`);
    return r.json();
  }

  async function fetchEntries(date) {
    const r = await apiFetch(`/v1/journal/entries?date=${date}`);
    if (!r.ok) throw new Error(`GET entries: ${r.status}`);
    return r.json();
  }

  async function patchEntry(id, body) {
    const r = await apiFetch(`/v1/journal/entries/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body }),
    });
    if (!r.ok) throw new Error(`PATCH entries/${id}: ${r.status}`);
    return r.json();
  }

  async function deleteEntry(id) {
    const r = await apiFetch(`/v1/journal/entries/${id}`, { method: 'DELETE' });
    if (!r.ok && r.status !== 204) throw new Error(`DELETE entries/${id}: ${r.status}`);
  }

  async function postEntry(p) {
    const fd = new FormData();
    fd.set('kind', p.entry.kind);
    fd.set('ts', p.entry.ts);
    fd.set('local_date', p.entry.local_date);
    if (p.entry.body) fd.set('body', p.entry.body);
    if (p.audioBlob) fd.append('audio', p.audioBlob, p.audioName);
    const r = await apiFetch('/v1/journal/entries', { method: 'POST', body: fd });
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

  // ====== ENTRY CREATION (offline queue) ======
  function queueText(body, dateStr) {
    if (!body.trim()) return;
    const entry = { ts: nowIso(), local_date: dateStr, kind: 'text', body };
    state.pending.push({ kind: 'text', entry });
    savePending();
    renderPending();
    sync();
  }

  function queueVoice(blob, mime, ext, dateStr) {
    const entry = { ts: nowIso(), local_date: dateStr, kind: 'voice', body: '' };
    const audioName = `rec.${ext}`;
    state.pending.push({ kind: 'voice', entry, audioBlob: blob, audioName, audioMime: mime });
    savePending();
    renderPending();
    toast(`Recorded ${(blob.size / 1024).toFixed(0)} KB (queued)`, 'ok');
    sync();
  }

  // ====== SYNC ======
  async function sync() {
    if (state.pending.length === 0) return;
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
    if (n > 0 && state.view === 'detail') await reloadDetail();
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
    } catch {
      toast('Mic permission denied', 'error');
      return;
    }

    const opts = pick.mime ? { mimeType: pick.mime } : {};
    const recorder = new MediaRecorder(stream, opts);
    const chunks = [];
    const dateForRecording = state.currentDate || localDateStr();
    recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: pick.mime || 'audio/webm' });
      stream.getTracks().forEach((t) => t.stop());
      queueVoice(blob, pick.mime || 'audio/webm', pick.ext, dateForRecording);
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
    if (!btn) return;
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

  // ====== VIEW: LIST ======
  async function populateList() {
    const ul = document.getElementById('dates-list');
    const empty = document.getElementById('dates-empty');
    ul.innerHTML = '';
    try {
      state.dates = await fetchDates();
    } catch (err) {
      toast(`Could not load dates: ${err.message}`, 'error');
      return;
    }
    if (state.dates.length === 0) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    for (const d of state.dates) {
      const li = document.createElement('li');
      li.className = 'date-item';
      li.tabIndex = 0;
      li.dataset.date = d.date;
      li.innerHTML = `<span class="date-label">${humanDate(d.date)}</span><span class="date-count">${d.count}</span>`;
      li.addEventListener('click', () => showDetail(d.date));
      li.addEventListener('keydown', (e) => { if (e.key === 'Enter') showDetail(d.date); });
      ul.appendChild(li);
    }
    markActiveDate();
  }

  function markActiveDate() {
    const ul = document.getElementById('dates-list');
    if (!ul) return;
    for (const el of ul.querySelectorAll('.date-item')) {
      el.classList.toggle('is-active', el.dataset.date === state.currentDate);
    }
  }

  async function showList() {
    state.view = 'list';
    state.currentDate = null;
    document.getElementById('view-list').hidden = false;
    document.getElementById('view-detail').hidden = true;
    await populateList();
  }

  // ====== VIEW: DETAIL ======
  async function showDetail(dateStr) {
    state.view = 'detail';
    state.currentDate = dateStr;
    document.getElementById('view-list').hidden = true;
    document.getElementById('view-detail').hidden = false;
    document.getElementById('detail-title').textContent = humanDate(dateStr);
    markActiveDate();
    await reloadDetail();
  }

  async function reloadDetail() {
    if (state.view !== 'detail' || !state.currentDate) return;
    try {
      state.entries = await fetchEntries(state.currentDate);
    } catch (err) {
      toast(`Could not load entries: ${err.message}`, 'error');
      state.entries = [];
    }
    renderDetailVoice();
    const text = textBlock(state.entries);
    state.lastSaved = text;
    const ta = document.getElementById('detail-text');
    ta.value = text;
  }

  function textBlock(entries) {
    return entries
      .filter((e) => e.kind === 'text' && e.body)
      .map((e) => e.body)
      .join('\n\n');
  }

  function renderDetailVoice() {
    const host = document.getElementById('detail-voice');
    host.innerHTML = '';
    const voice = state.entries.filter((e) => e.kind === 'voice');
    if (voice.length === 0) return;
    for (const e of voice) {
      const card = document.createElement('div');
      card.className = 'voice-chip';
      const head = `<div class="voice-head"><span class="voice-time">${timeOfDay(e.ts)}</span><span class="voice-icon">🎤</span></div>`;
      const audio = e.audio_url
        ? `<audio controls preload="none" crossorigin="use-credentials" src="${API_BASE}${e.audio_url}"></audio>`
        : '';
      const body = e.body ? `<div class="voice-body">${escapeHtml(e.body)}</div>` : '';
      card.innerHTML = head + audio + body;
      host.appendChild(card);
    }
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
    );
  }

  // Save the textarea's content as the day's text block.
  // 0 text entries on date → POST one; 1 → PATCH it; N>1 → PATCH most-recent + DELETE older.
  // The merge-on-save is what keeps "one document per day" honest against an N-row schema.
  let inFlightSave = null;
  async function saveDetail() {
    if (inFlightSave) return inFlightSave;
    if (state.view !== 'detail' || !state.currentDate) return;
    const ta = document.getElementById('detail-text');
    const text = ta.value;
    if (text === state.lastSaved) return;
    setSaving(true);
    inFlightSave = (async () => {
      try {
        const textEntries = state.entries.filter((e) => e.kind === 'text');
        if (textEntries.length === 0) {
          if (text.trim() === '') return;
          await postEntry({ entry: { ts: nowIso(), local_date: state.currentDate, kind: 'text', body: text } });
        } else if (textEntries.length === 1) {
          await patchEntry(textEntries[0].id, text);
        } else {
          const latest = textEntries[textEntries.length - 1];
          await patchEntry(latest.id, text);
          for (const e of textEntries.slice(0, -1)) await deleteEntry(e.id);
        }
        state.lastSaved = text;
        toast('Saved', 'ok');
        await reloadDetail();
        await populateList();
      } catch (err) {
        toast(`Save failed: ${err.message}`, 'error');
      } finally {
        setSaving(false);
      }
    })();
    try { return await inFlightSave; } finally { inFlightSave = null; }
  }

  // ====== UI ======
  function setSyncing(on) {
    const btn = document.getElementById('sync-btn');
    btn.disabled = on;
    btn.textContent = on ? 'Syncing…' : `Sync${state.pending.length ? ' (' + state.pending.length + ')' : ''}`;
  }

  function setSaving(on) {
    const btn = document.getElementById('detail-save');
    if (!btn) return;
    btn.disabled = on;
    btn.textContent = on ? 'Saving…' : 'Save';
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

  async function openSettings() {
    const settings = document.getElementById('settings');
    settings.hidden = false;
    // Populate "signed in as" lazily — shell topbar handles the main display.
    try {
      const r = await fetch(`${API_BASE}/v1/me`, { credentials: 'include' });
      if (r.ok) {
        const me = await r.json();
        const display = me.display_name || me.email;
        document.getElementById('me-view').textContent = `${display} (${me.email})`;
      }
    } catch { /* offline — leave em-dash */ }
    renderPending();
  }
  function closeSettings() {
    document.getElementById('settings').hidden = true;
  }

  // ====== WIRING ======
  function bind() {
    document.getElementById('detail-back').addEventListener('click', async () => {
      await saveDetail();
      await showList();
    });
    document.getElementById('detail-save').addEventListener('click', saveDetail);
    document.getElementById('detail-text').addEventListener('blur', saveDetail);
    document.getElementById('open-today').addEventListener('click', () => showDetail(localDateStr()));

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
    Shell.mount({
      mode: "subapp",
      apiBase: API_BASE,
      homeUrl: "https://jesselab.space/",
    });
    bind();
    renderPending();
    await sync();
    await showDetail(localDateStr());
    await populateList();
  });

