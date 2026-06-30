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

## Getting started

You'll need [Docker](https://docs.docker.com/get-docker/) installed. That's the only dependency.

**1. Clone the repo**
```bash
git clone https://github.com/setugk/journery.git
cd journery
```

**2. Start it**
```bash
docker compose up -d
```

**3. Open it**

Go to `http://localhost:5050` in your browser.

---

**Want to access it from anywhere — not just your home network?**

Put it behind a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/). It's free, takes about 10 minutes to set up, and gives you a public URL like `journery.yourdomain.com` that works from any device, anywhere. Add a Cloudflare Access policy (email OTP) for auth — no app-level login needed.

## Stack

Flask + SQLite backend, vanilla JS SPA frontend — no build step, no bundler, no CDN dependencies.

## License

MIT
