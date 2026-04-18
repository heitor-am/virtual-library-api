# 002 — uv as package manager and build tool

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

The project needs a deterministic way to install and manage Python dependencies across local development, Docker builds, CI, and production. Python has historically suffered from fragmented tooling: `pip` + `venv`, Poetry, Pipenv, PDM, Hatch — all overlap with subtle differences and different performance profiles.

The Dockerfile runs `uv sync` during build; CI runs `uv sync --all-extras` on every job; `make` targets wrap `uv run`. Slow dependency resolution directly hits iteration speed.

## Decision

Use **uv** (by Astral) for dependency management, lockfile generation, and as the Python project runner. `pyproject.toml` is the single source of truth, with dev/runtime dependency groups and `uv.lock` committed.

## Consequences

**Positive:**
- **Install time is a fraction of pip/poetry.** Full sync of ~130 packages completes in seconds; caching in CI is effective.
- One tool: dependency resolution, venv management, running scripts, lockfile (`uv.lock`). Replaces `pip` + `venv` + `pip-tools` + `pipenv`.
- Dependency groups (`[dependency-groups.dev]`) keep test/lint tools out of the production image, shrinking the final runtime layer.
- Rust-backed resolver is strict about conflicts and fast enough to be a non-concern in developer flow.

**Negative:**
- Young tool (2024+). Some edge cases around private indexes or complex build backends may not be as battle-tested as pip.
- Team members unfamiliar with uv need a short onboarding; not as universally known as Poetry.

**Trade-offs accepted:**
- Betting on an Astral-maintained tool (same org as Ruff) — good alignment with the rest of the stack's direction, but locks the project's tooling DX to one vendor's roadmap.

## Alternatives considered

- **Poetry** — Most mature "modern" Python tool, but slower resolver and install. No significant feature gap for this project but loses on speed.
- **pip + venv + requirements.txt** — Zero-magic, zero-features. Rejected: no lockfile semantics, no dev/runtime split, manual venv management.
- **PDM / Hatch** — Viable but smaller ecosystem momentum than uv as of 2026.

## References

- [uv docs](https://docs.astral.sh/uv/)
- [Benchmarks vs pip/Poetry](https://astral.sh/blog/uv)
