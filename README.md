# Journal

Minimal mobile-first PWA for journaling — text + voice. Posts to `personal_api` (`api.jesselab.space`) and stores entries in Postgres on `jesse-prod`.

## Use

1. Sign in once at <https://jesselab.space/> (Google OAuth, allowlisted).
2. Open the journal PWA. Sign-in is shared across `*.jesselab.space` via the session cookie — no token, no settings.
3. Type or record. **Save** posts a text entry; **● Record** / **■ Stop** posts a voice entry (audio is stored, transcription comes later).
4. Anything queued while offline replays on reconnect.

## API surface

| Endpoint | Use |
|---|---|
| `GET /v1/me` | Identity check on load; redirects to apex on 401. |
| `POST /v1/journal/entries` | Multipart: `kind`, `ts`, `local_date`, `body?`, `audio?`. |
| `POST /v1/auth/logout` | Sign-out button. |

Per-date markdown view, voice transcription, and the calendar nav land in later tickets — see `Jesse-vdR/Jesse#29`.

## Local dev

```sh
# 1. Start the API (in personal_api)
docker run -d --name jesse-pg -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
make dev   # uvicorn :8000

# 2. Serve the PWA
python -m http.server 8001
# Open http://localhost:8001  → app.js auto-points to http://localhost:8000
```

The API base URL flips automatically based on hostname (`localhost`/`127.0.0.1` → local API, anything else → `api.jesselab.space`).

## Stack

Vanilla HTML/CSS/JS + service worker. No build step. Same shape as `Jesse-vdR/training-app`.
