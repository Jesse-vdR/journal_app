# Journal

Minimal mobile-first PWA for journaling — text + voice. Writes append-only entries to the data hub repo (`Jesse-vdR/Jesse`) via the GitHub Contents API.

## Data layout (in `Jesse-vdR/Jesse`)

- `journal/entries.jsonl` — one entry per line
- `journal/audio/<ISO-ts>.{webm,m4a,…}` — voice recordings

Entry shape:

```json
{"ts":"2026-05-04T15:30:00.000Z","local_date":"2026-05-04","kind":"text","body":"…"}
{"ts":"2026-05-04T15:31:00.000Z","local_date":"2026-05-04","kind":"voice","audio":"journal/audio/2026-05-04T15-31-00-000Z.webm"}
```

## Use

1. Open the deployed page (see GitHub Pages setup below).
2. Tap the cog → paste a fine-grained PAT scoped to `Jesse-vdR/Jesse` with `Contents: Read and write`. The token lives only in this browser's localStorage.
3. Type or record. **Save** queues a text entry; tapping **● Record** starts mic capture, **■ Stop** queues a voice entry.
4. **Sync** uploads queued audio files, then appends all queued entries to `journal/entries.jsonl` in one commit.

Text entries persist across reloads (localStorage). **Voice blobs are held in memory only** — sync before you close the tab, or the audio is lost (the placeholder text entry would also be discarded by sync since the blob is gone).

## Stack

Vanilla HTML/CSS/JS + service worker. No build step. Same shape as `Jesse-vdR/training-app`.
