# 001 — FastAPI over Django/Flask

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

The project needs a Python web framework for a small API surface (CRUD + a semantic search endpoint) that also needs to integrate with LLMs and embedding providers. Three options were on the table: Django + DRF, Flask + Flask-RESTful, and FastAPI.

The API is async at heart — it calls external HTTP services (OpenRouter) and awaits DB I/O. It also needs automatic OpenAPI docs as a public interface and should feel modern enough to reflect the current state of Python backends for AI workloads.

## Decision

Use **FastAPI** with the async SQLAlchemy 2.0 stack.

## Consequences

**Positive:**
- First-class `async`/`await` without extra plumbing — LLM calls and DB queries coexist cleanly on a single event loop.
- OpenAPI schema is generated from type hints and Pydantic models, always in sync with the code. No separate spec to maintain.
- Pydantic v2 is used for both HTTP contracts and settings, unifying validation throughout the codebase.
- Small footprint: 74 MB final Docker image, startup under 1s.
- Strong community alignment with AI/ML backends (LangChain, LlamaIndex, many OpenAI-adjacent projects lead with FastAPI examples).

**Negative:**
- Thinner batteries-included than Django — no built-in admin, auth system, or ORM. Had to wire SQLAlchemy, Alembic, and structlog manually.
- Smaller ecosystem for plug-in apps compared to Django.

**Trade-offs accepted:**
- Writing our own layered architecture (routes → services → repositories) instead of inheriting Django conventions. This is a feature for a showcase project (visible design), a cost for a shipping team (more boilerplate).

## Alternatives considered

- **Django + DRF** — Rejected. Too heavy for a 5-endpoint API, async support still feels bolted-on in 5.x, admin and auth would be dead weight.
- **Flask + Flask-RESTful** — Rejected. Sync-first, OpenAPI docs require extra libraries and drift easily from code, Pydantic integration is manual.

## References

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic v2 performance](https://docs.pydantic.dev/latest/blog/pydantic-v2/)
