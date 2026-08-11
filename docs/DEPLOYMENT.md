# Deploying QSFIN

The app is a single FastAPI service (`webapp/backend/main.py`) that serves both the API and the
static frontend — one process, one deployment, no separate frontend host needed. Three ready-made
paths, pick whichever platform you already have or want an account on:

## Option A — Render.com (recommended: real free tier, GitHub-connected auto-deploy)

1. Push this repo to GitHub (see below).
2. On [render.com](https://render.com), **New → Blueprint**, point it at your GitHub repo. It
   reads `render.yaml` at the repo root automatically and configures everything.
3. Deploy. Render gives you a public `https://qsfin-xxxx.onrender.com` URL.
4. Every push to `main` auto-redeploys.

Note: Render's free tier spins the service down after ~15 minutes of inactivity and takes
10–30 seconds to wake back up on the next request — fine for a portfolio/demo project, not for
something that needs to always be instantly warm.

## Option B — Railway.app

1. Push this repo to GitHub.
2. On [railway.app](https://railway.app), **New Project → Deploy from GitHub repo**.
3. Railway auto-detects the `Procfile` and Python project; no extra config needed.
4. It assigns a public domain automatically (or generate one under Settings → Networking).

## Option C — Any Docker host (Fly.io, Cloud Run, Azure Container Apps, a VPS)

The `Dockerfile` at the repo root is a complete, portable build:

```bash
docker build -t qsfin .
docker run -p 8420:8420 qsfin
```

For Fly.io specifically: `fly launch` (it detects the Dockerfile), then `fly deploy`.

## Before deploying anywhere public

- Fill in the three placeholder link fields in `webapp/frontend/index.html`'s About section
  (GitHub, LinkedIn, Portfolio — search for `data-placeholder`).
- Everything runs on synthetic, fictional case data — nothing here should be presented as
  analysis of a real case, and the site already says so in the hero and footer; don't remove that.
- There's no authentication or rate limiting on the API endpoints. Fine for a demo; if this ever
  needs to be more than that, put a rate limiter in front of the `/api/*/rerun` endpoints since
  they do real (if cheap) computation on every call.
