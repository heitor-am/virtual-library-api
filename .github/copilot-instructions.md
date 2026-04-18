# Copilot Instructions — Virtual Library API

Context and conventions for automated code review. Focus feedback on what actually matters for this project.

## Stack

- **Python 3.12**, async throughout (FastAPI + SQLAlchemy 2.0 async + httpx)
- **Pydantic v2** for HTTP contracts, separate from SQLAlchemy models
- **Alembic** for migrations, autogenerate mode
- **OpenRouter** as the unified LLM gateway (via the `openai` SDK with a custom `base_url`)
- **uv** for dependency management; `ruff` for lint and format; `mypy` strict; `pytest` with coverage
- **SQLite** single-file DB with BLOB columns for embeddings

## Architecture

Layered: `app/api/routers → app/services → app/repositories → app/database`. Plus a parallel `app/ai/` module (client, summary, embeddings) and `app/core/` (logging, RFC 7807 exceptions).

- **Routes are thin.** Business logic lives in services. Route handlers should mostly parse input, call the service, and return the mapped schema.
- **Services own orchestration.** They inject callables (e.g. `summary_generator`, `embedding_generator`) so tests can swap them for mocks.
- **Repositories touch SQLAlchemy.** No Pydantic schemas, no business rules.
- **AI is additive.** `LLMUnavailableError` and `APIError` are swallowed in the service on write paths (create/update) — the primary write must never fail because of a degraded LLM.

## Conventions

- **Conventional Commits** for every commit: `feat(scope): ...`, `fix(scope): ...`, `chore:`, `docs:`, `test:`, `ci:`, `build:`, `perf:`, `refactor:`. Flag commits that don't match.
- **RFC 7807 Problem Details** for every error response — `application/problem+json` with fields `type`, `title`, `status`, `detail`, `instance`, `code`. New endpoints must surface errors this way.
- **Dependency injection via `Annotated[X, Depends(...)]`** — see `app/api/deps.py` for `DbDep` and `BookServiceDep`. New routes should follow this pattern.
- **Tests live in `tests/`**, same structure as `app/`. Every new module needs tests; every new endpoint needs integration tests via `dependency_overrides`.
- **Markdown:** use bullet lists or blank lines between consecutive `**Label:**` — CommonMark collapses single newlines and hides rendering.

## What to flag in reviews

- Routes doing business logic that belongs in the service
- Services leaking SQLAlchemy objects beyond the response layer (routes should map via `BookRead.model_validate`)
- AI errors that would block writes instead of degrading gracefully
- New endpoints without RFC 7807 error responses
- Missing tests for new code paths (especially service branches and error cases)
- Sync I/O where async is expected (blocking calls in request handlers)
- Hardcoded model names/URLs that should be env-driven (`OPENROUTER_CHAT_MODEL`, `OPENROUTER_EMBEDDING_MODEL`)
- Unsafe shell/SQL construction; secrets in code; missing input validation at boundaries
- Non-ASCII chars in curl examples without `-G --data-urlencode` (the project has bitten by this)

## What to ignore

- Don't suggest Black, Flake8, isort, or Poetry — we use Ruff and uv.
- Don't ask for docstrings on every function — the project prefers self-documenting code with types. Only call out docstrings when a public function's intent is genuinely non-obvious.
- Don't flag `# type: ignore` or `# noqa` with inline justification — they're intentional (e.g. `typing.List` workaround for the `list` method shadow in repositories/services).
- Don't suggest renaming `list` methods — established CRUD convention.
- Don't request tests for the seed script or ADRs.
- Don't complain about Portuguese content in prompts or seed data — this is a pt-BR project.

## Priorities

When multiple issues exist, prioritize (highest first):

1. **Correctness bugs** — logic errors, wrong HTTP codes, broken error handling
2. **Security** — secrets, injection, unsafe deserialization
3. **Architectural drift** — layer violations, skipping DI, missing RFC 7807
4. **Test gaps** — untested branches, especially error paths
5. **Style nits** — only if they violate the ruff config

Skip suggestions that apply generically to any codebase without connecting to this project's context.
