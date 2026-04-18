# 003 — Fly.io for deployment

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

The API needs a public HTTPS endpoint for demos and portfolio showcase. Because it uses **SQLite** (per the brief), the hosting environment has an uncommon requirement: a persistent writable volume that survives redeploys and machine restarts. Without that, every deploy wipes the database.

Most modern PaaS offerings (Render, Railway, Vercel, Deno Deploy) are ephemeral-filesystem-first and steer users to managed Postgres. Fitting SQLite into those platforms means either fighting the defaults or paying for a managed DB just to avoid that fight.

Secondary requirements: generous free tier (this is a portfolio project, not a business), region close to Brazilian traffic, a CLI that fits into CI.

## Decision

Deploy to **Fly.io** in region `gru` (São Paulo) with a 1 GB volume mounted at `/data` for the SQLite file. Auto-deploy on push to `main` via `flyctl deploy` in a GitHub Action.

## Consequences

**Positive:**
- First-class volume support. One line of `fly.toml` mounts a persistent disk at any path.
- Free tier covers this workload: 3 shared-cpu-1x machines (256 MB each), 3 GB of volume storage, auto-stop on idle.
- São Paulo region brings p95 latency under 30ms for our target audience.
- `flyctl` is scriptable and pairs with a simple GitHub Action (`superfly/flyctl-actions/setup-flyctl`) for CD.
- Healthchecks, SSL, HTTP/2, graceful machine restarts — included.

**Negative:**
- Free tier requires a credit card for verification. No charges as long as usage stays within limits, but it's a signup step some users hit.
- SQLite on a single-node volume is not horizontally scalable. Fly has a story for this (LiteFS) but it's extra work and out of scope for this project.
- Cold start of auto-stopped machines adds ~2s to the first request after idle.

**Trade-offs accepted:**
- Accepting Fly's "machines" abstraction (different from typical container PaaS semantics) and its lower-level controls. More knobs to get right (like `release_command` vs inline migrations — see the fix history in PR #16), but also more transparent operationally.

## Alternatives considered

- **Render** — Free tier cold starts are aggressive (30s+), disk add-ons cost real money. Rejected for demo latency.
- **Railway** — Good DX but the forever-free tier was discontinued; ongoing small cost. Rejected for a showcase project.
- **Vercel / Deno Deploy** — No persistent filesystem, steer toward managed Postgres. Would force a stack change.
- **Heroku** — No free tier since 2022. Rejected.
- **Self-hosting (VPS + Caddy)** — Overkill for a single small app; doubles the ops surface.

## References

- [Fly.io Python quickstart](https://fly.io/docs/languages-and-frameworks/python/)
- [Fly.io volumes](https://fly.io/docs/volumes/)
- [superfly/flyctl-actions](https://github.com/superfly/flyctl-actions)
