# Journery

A self-hosted private journaling app. Nestable folders, tagged notes, markdown-syntax editor, search. Runs on a NAS or any Docker host, accessed via browser on any device.

![Journery desktop](screenshots/clippery_desktop.png)

<img src="screenshots/clippery_mobile.png" alt="Journery mobile" width="320" />

## What it does

- Nested folders with rename, move, and drag-and-drop
- Tags with autocomplete and inline autocomplete in the editor
- Markdown syntax (raw textarea) — bullets, numbered lists, indentation
- Full-text search across all notes
- Trash with 30-day retention + restore
- PWA — add to home screen on iOS/Android
- Auto-saves 2s after last keystroke
- Real-time sync polling across tabs/devices
- 3-pane layout on desktop; drill-down navigation on mobile

## Try it first

Kick the tyres at **[demo-journery.setugk.com](https://demo-journery.setugk.com)** — a full demo where everything is saved only in your browser (nothing shared, nothing stored on a server). When you're ready, host your own below.

## Getting started

You own your data — it lives in a folder you choose, on hardware you control. The only dependency is [Docker](https://docs.docker.com/get-docker/).

### Quickest — one command

```bash
docker run -d --name journery -p 5050:5000 -v ~/journery-data:/data ghcr.io/setugk/journery
```

Then open **http://localhost:5050**. No cloning, no build — your notes are stored in `~/journery-data`.

### Or with Docker Compose

```bash
curl -O https://raw.githubusercontent.com/setugk/journery/main/docker-compose.yml
docker compose up -d
```

Open **http://localhost:5050**. Data lives in `./data`.

### Where's my data?

Everything is a single SQLite file inside the volume you mounted (`~/journery-data` or `./data` above). **Point that at anywhere you like** — a folder on your NAS, an external drive, a named Docker volume:

```bash
-v /mnt/nas/journery:/data      # store it on your NAS
-v journery-data:/data          # a managed Docker volume
```

Back it up by copying that folder. Nothing ever leaves your machine.

### Add a password (optional)

By default Journery runs with no login (handy on a private network). To require one, set two env vars:

```bash
docker run -d -p 5050:5000 -v ~/journery-data:/data \
  -e JOURNERY_USER=me -e JOURNERY_PASS=change-this \
  ghcr.io/setugk/journery
```

### Access it from anywhere

Put it behind a free [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (~10 min) for a public URL like `journery.yourdomain.com` that works from any device. Add a Cloudflare Access policy (email OTP) for auth — no app-level login needed.

## Stack

Flask + SQLite backend, vanilla JS SPA frontend — no build step, no bundler, no CDN dependencies.

## License

MIT
