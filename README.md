# Journal

Minimal mobile-first PWA for journaling — text + voice. Posts to `personal_api` (`api.jesselab.space`) and stores entries in Postgres on `jesse-prod`.

## Use

1. Sign in once at <https://jesselab.space/> (Google OAuth, allowlisted).
2. Open the journal PWA. Sign-in is shared across `*.jesselab.space` via the session cookie — no token, no settings.
3. Today opens by default. Edit the day's text in one textarea. Save on blur or via the **Save** button.
4. **‹ Dates** opens a list of days that have entries; tap any to edit.
5. **● Record** / **■ Stop** appends a voice entry to the open date (audio stored; transcription lands in a later ticket).
6. Anything queued while offline replays on reconnect.

## Data model

The textarea per day shows all `kind=text` entries for that date joined by `\n\n`. Voice entries surface as read-only chips above the textarea. On save:

- 0 text entries → POST a new one.
- 1 text entry → PATCH it.
- N>1 text entries → PATCH the most recent and DELETE the older ones (so re-reading doesn't duplicate the day's text).

## API surface

| Endpoint | Use |
|---|---|
| `GET /v1/me` | Identity check on load; redirects to apex on 401. |
| `GET /v1/journal/dates` | Date list with entry counts. |
| `GET /v1/journal/entries?date=YYYY-MM-DD` | Entries for a date, asc by `ts`. |
| `POST /v1/journal/entries` | Multipart: `kind`, `ts`, `local_date`, `body?`, `audio?`. |
| `PATCH /v1/journal/entries/{id}` | JSON: `{body}`. |
| `DELETE /v1/journal/entries/{id}` | Used by the merge-on-save path. |
| `POST /v1/auth/logout` | Sign-out button. |

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
