# PRD — Virtual Library API

- **Project:** Virtual Library API
- **Status:** Released (`v1.0.0`)
- **Live:** https://virtual-library-api.fly.dev

## 1. Context

A REST API for a virtual library with AI-assisted features. Books can be created with just title, author, and date — the service auto-generates a summary via LLM and stores a semantic embedding so the same dataset is searchable both by text filters and by semantic similarity.

The project is part of a three-repo portfolio that shares tooling and conventions; see §13 for the sibling repos.

## 2. Scope

### 2.1 Core requirements

- Full CRUD on books (`title`, `author`, `published_date`, `summary`)
- Text search by title and/or author (case-insensitive, partial match)
- SQLite persistence
- Unit and integration tests
- Documented endpoints

### 2.2 Additional requirements (delivered)

- Pagination and ordering on list
- Versioned migrations (Alembic)
- Test coverage ≥ 80% enforced, actual ~97%
- 5-job CI (lint, typecheck, tests, contract tests via Schemathesis, security scans via pip-audit + bandit)
- Public deploy with an accessible URL
- README with badges, setup, examples

### 2.3 Differentiating features

**Documentation & DX:**
- [Scalar](https://github.com/scalar/scalar) as the interactive docs UI (`/docs`) — replaces the default Swagger
- Landing page at `/` with pitch and links
- Mermaid diagrams (architecture + request flow) rendered inline in the README
- Architecture Decision Records in [`docs/adr/`](adr/)
- Dev Container for zero-setup onboarding
- Structured logging with `request_id` propagation (`structlog`)

**AI layer:**
- **OpenRouter** as unified LLM gateway — both chat and embeddings behind one provider, model selectable via env vars
- **Auto-summary** on create when the client omits `summary` — `openai/gpt-4o-mini`, `summary_source="ai"` tracked
- **Semantic search** at `/books/search/semantic` using multilingual `baai/bge-m3` embeddings (1024 dims, 8192-token context) persisted as SQLite BLOBs
- AI is strictly additive: `LLMUnavailableError` / `openai.APIError` caught in the service, so LLM outages never block CRUD writes

**Quality:**
- Pre-commit hooks (ruff, mypy, pytest)
- Conventional Commits
- Schemathesis contract tests in CI against the running API
- **RFC 7807 Problem Details** for every error response (`application/problem+json`)

**DevOps:**
- Multi-stage Dockerfile — ~74 MB runtime image
- Makefile with canonical commands (`make check`, `make dev`, `make deploy`)
- Dependabot for automated dependency bumps
- Rich `/health` endpoint (`version`, `commit` SHA, `uptime_seconds`, DB status)
- Deployed on Fly.io with auto-deploy on push to `main`

### 2.4 Out of scope

- Authentication / authorization
- File uploads
- Relations to other entities
- Rate limiting (relies on OpenRouter's prepaid spend cap)
- Advanced observability (metrics, tracing)

## 3. Stack

| Layer | Choice | Rationale (see ADRs) |
|---|---|---|
| Web framework | FastAPI | [ADR-001](adr/001-fastapi-over-django.md) |
| Package manager | uv | [ADR-002](adr/002-uv-package-manager.md) |
| Deployment | Fly.io | [ADR-003](adr/003-fly-io-deployment.md) |
| LLM gateway | OpenRouter (`openai` SDK + custom `base_url`) | [ADR-004](adr/004-openrouter-unified-llm-gateway.md) |
| Docs UI | Scalar | [ADR-005](adr/005-scalar-over-swagger.md) |
| Error format | RFC 7807 Problem Details | [ADR-006](adr/006-rfc-7807-errors.md) |
| Embedding model | `baai/bge-m3` | [ADR-007](adr/007-bge-m3-for-multilingual-embeddings.md) |
| ORM | SQLAlchemy 2.0 (async) | Modern typed API; async fits FastAPI |
| Validation | Pydantic v2 | Integrated with FastAPI; `pydantic-settings` for env vars |
| Migrations | Alembic (autogenerate) | Industry standard for SQLAlchemy |
| Testing | pytest + httpx AsyncClient + Schemathesis | Fixtures, async-native, contract testing |
| Lint / format | Ruff | Replaces Black + Flake8 + isort in one tool |
| Type check | mypy (strict) | Mature, wide ecosystem support |

## 4. Architecture

Layered: `routers → services → repositories → database`, with a parallel `app/ai/` module for LLM/embedding integration.

```
┌─────────────────────────────────────┐
│  API Layer (FastAPI routers)        │  HTTP, validation, docs
├─────────────────────────────────────┤
│  Service Layer                      │  business logic, RFC 7807 exceptions
├─────────────────────────────────────┤
│  Repository Layer                   │  SQLAlchemy CRUD, filters
├─────────────────────────────────────┤
│  AI Layer (OpenRouter)              │  summary + embeddings, retry + graceful fail
├─────────────────────────────────────┤
│  Database (SQLite)                  │
└─────────────────────────────────────┘
```

**Principles:**

- Routes don't touch SQLAlchemy — they pass through the service
- Services inject dependencies (repo, AI generators) so tests can mock freely
- Repositories are the only place SQLAlchemy lives
- AI failures are swallowed on write paths, surfaced as `503 application/problem+json` on search paths

See the Mermaid rendering in the [README](../README.md) and the detailed [request flow diagram](diagrams/request-flow.md).

## 5. Data model

Single entity: `Book`

| Field | Type | Notes |
|---|---|---|
| `id` | int, PK | autoincrement |
| `title` | str | NOT NULL, indexed |
| `author` | str | NOT NULL, indexed |
| `published_date` | date | NOT NULL |
| `summary` | str \| null | nullable — the only field that can be cleared on PUT |
| `summary_source` | enum (`user` \| `ai`) | provenance of the summary |
| `embedding` | BLOB \| null | `bge-m3` float32 vector (4096 bytes) |
| `embedding_model` | str \| null | model identifier, used to invalidate if model changes |
| `created_at` | datetime | `CURRENT_TIMESTAMP` default |
| `updated_at` | datetime | auto-updated on modify |

Indexes on `title` and `author` power the text filters. Embeddings are recomputed on any update that touches `title`, `author`, or `summary`.

## 6. API

| Method | Path | Status codes |
|---|---|---|
| `POST` | `/books` | 201 / 422 |
| `GET` | `/books` | 200 (with `?title`, `?author`, `?skip`, `?limit`, `?sort_by`, `?order`) |
| `GET` | `/books/{id}` | 200 / 404 / 422 |
| `PUT` | `/books/{id}` | 200 / 404 / 422 |
| `DELETE` | `/books/{id}` | 204 / 404 / 422 |
| `GET` | `/books/search/semantic` | 200 / 422 / 503 (`?q`, `?top_k`, `?min_score`) |
| `GET` | `/health` | 200 / 503 |

All errors follow RFC 7807:

```json
{
  "type": "https://virtual-library-api.fly.dev/errors/book-not-found",
  "title": "Book Not Found",
  "status": 404,
  "detail": "Book with id 42 not found",
  "instance": "/books/42",
  "code": "BOOK_NOT_FOUND"
}
```

Full interactive reference at [`/docs`](https://virtual-library-api.fly.dev/docs).

## 7. Testing strategy

- **Unit** — repository and service tested in isolation (in-memory SQLite for repo, mocked repo + AI generators for service)
- **Integration** — endpoints tested via `httpx.AsyncClient` with `dependency_overrides` injecting the test DB and stubbed service
- **Contract** — Schemathesis fuzzes the live API from the OpenAPI spec in CI (`--checks not_a_server_error`). Caught three production bugs during development: `PUT /books/{id}` with `{"title": null}` returning 500 on a NOT NULL constraint; `GET /books?skip=<huge>` overflowing SQLite INTEGER; same overflow on path params `GET /books/{huge_id}`. All fixed.
- **Security** — `pip-audit` for CVEs in installed packages, `bandit -r app/` for code-level scans. Both zero-findings.

Coverage gate: `--cov-fail-under=80`. Current actual ~97%.

## 8. CI/CD

Five GitHub Actions jobs on every push and PR:

| Job | Tool |
|---|---|
| `lint` | `ruff check` + `ruff format --check` |
| `typecheck` | `mypy app` (strict) |
| `test` | `pytest` with coverage |
| `contract` | Boots the API with `AI_FEATURES_ENABLED=false`, runs Schemathesis |
| `security` | `pip-audit` + `bandit` |

Auto-deploy on push to `main` via `superfly/flyctl-actions` with the commit SHA injected as a build arg (so `/health` reports the exact version running).

GitHub Copilot code review is enabled on the default branch; reviews against custom instructions in [`.github/copilot-instructions.md`](../.github/copilot-instructions.md).

## 9. Deployment

- **Fly.io**, region `gru` (São Paulo)
- 512 MB shared-cpu-1x machine, auto-stop on idle
- 1 GB persistent volume at `/data` — the SQLite file lives there
- Healthcheck polls `/health` every 30s
- Secrets: `OPENROUTER_API_KEY`; GitHub: `FLY_API_TOKEN` (deploy-scoped, 1-year expiry)

Migrations run on container startup (`alembic upgrade head && exec uvicorn ...`) — release commands on Fly run on a machine without the volume mount, so the approach of in-container migrations avoids a known pitfall.

## 10. Folder structure

```
virtual-library-api/
├── app/
│   ├── main.py, config.py, database.py
│   ├── api/deps.py + api/routers/{books,search,health}.py
│   ├── models/book.py                  # SQLAlchemy
│   ├── schemas/{book,problem}.py       # Pydantic (HTTP contracts)
│   ├── repositories/book.py            # SQLAlchemy queries
│   ├── services/book.py                # orchestration + injected AI generators
│   ├── ai/{client,summary,embeddings,prompts}.py
│   ├── core/{exceptions,logging}.py    # RFC 7807 + structlog
│   └── static/index.html               # landing page
├── alembic/                            # migrations
├── tests/                              # parallels app/
├── docs/
│   ├── PRD.md                          # this document
│   ├── adr/                            # 7 ADRs
│   └── diagrams/                       # Mermaid architecture + request flow
├── .github/                            # CI + CD + dependabot + copilot-instructions
├── .devcontainer/                      # zero-setup VS Code
├── Dockerfile, docker-compose.yml, fly.toml
├── pyproject.toml, uv.lock, Makefile
└── README.md, LICENSE
```

## 11. Release history

- **v0.1.0** — MVP: CRUD + filters + tests + migrations
- **v0.2.0** — AI features: auto-summary + embeddings + semantic search
- **v1.0.0** — Production: deploy, CI/CD, ADRs, Mermaid diagrams, polished README

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| OpenRouter outage | `tenacity` retry (3 attempts, exponential backoff) + graceful degradation (write paths succeed without AI) |
| Runaway OpenRouter cost | Prepaid credit model — you can only spend what you funded |
| SQLite single-file lock under write pressure | Acceptable at this scale; volume provides durability |
| Deploy-time migration failures | Migrations run in-container with the volume mounted, so errors surface in logs and the old machine stays live until the new one is healthy |
| Schemathesis flaky in CI | Pinned `--hypothesis-max-examples=10` keeps the state space bounded |

## 13. Portfolio companions

This repo is one of three sibling projects sharing the same tooling and `app/ai/` pattern:

- **Virtual Library API** (this repo) — FastAPI + SQLite + OpenRouter
- **Python Tutor Chatbot** — Chainlit + LangChain + OpenRouter
- **Semantic Document Search** — FastAPI + Qdrant + OpenRouter (package-by-feature, FSM-driven ingestion, functional retrieval pipeline)
