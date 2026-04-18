# Virtual Library API

[![CI](https://github.com/heitor-am/virtual-library-api/actions/workflows/ci.yml/badge.svg)](https://github.com/heitor-am/virtual-library-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> REST API for virtual library management with semantic search, built with FastAPI and OpenRouter.

## ✨ Features

- **Full CRUD** for books with filtering, pagination, and ordering
- **LLM-generated summary** on create (optional, via OpenRouter)
- **Semantic search** via `bge-m3` embeddings and cosine similarity
- **RFC 7807 Problem Details** for standardized error responses
- **Structured logging** with request ID propagation
- **Scalar** for beautiful interactive API docs
- **Multi-stage Dockerfile** with slim runtime image
- **Dev Container** support for zero-setup onboarding

## 🏗 Architecture

```mermaid
flowchart TB
    Client([Client / Scalar UI])

    subgraph API["API Layer — FastAPI"]
        direction LR
        RBooks["/books router"]
        RSearch["/books/search/semantic"]
        RHealth["/health"]
    end

    subgraph Service["Service Layer"]
        BookService["BookService<br/>• orchestration<br/>• BookNotFoundError → 404"]
    end

    subgraph Repo["Repository Layer"]
        BookRepository["BookRepository<br/>• SQLAlchemy 2.0 async<br/>• filters, pagination, sort"]
    end

    subgraph AI["AI Layer (optional)"]
        direction TB
        Summary["generate_summary<br/>openai/gpt-4o-mini"]
        Embed["generate_embedding<br/>baai/bge-m3"]
        ORClient["OpenRouter client<br/>openai SDK + tenacity retry"]
        Summary --> ORClient
        Embed --> ORClient
    end

    DB[("SQLite<br/>books + embedding BLOB")]
    OR[("OpenRouter<br/>unified LLM gateway")]

    Client -->|HTTPS| API
    API --> Service
    Service --> Repo
    Service -.->|auto-summarize<br/>+ embed on write| AI
    Repo --> DB
    ORClient -.->|HTTPS| OR
```

AI is strictly additive — `LLMUnavailableError` and `openai.APIError` on the OpenRouter path are caught in the service, so a downstream LLM outage lets the book persist without a summary or embedding rather than surfacing as a 5xx. See the standalone [architecture diagram](docs/diagrams/architecture.md) for notes and the [request flow](docs/diagrams/request-flow.md) for the detailed `POST /books` sequence.

## 🚀 Quick start

```bash
# With uv (recommended)
make install
cp .env.example .env
make migrate
make dev
```

Open http://localhost:8000 for the landing page or http://localhost:8000/docs for Scalar API reference.

### With Docker

```bash
cp .env.example .env
make docker-up
```

## 📡 API

| Method | Path | Description |
|---|---|---|
| `POST` | `/books` | Create a book (auto-generates summary and embedding) |
| `GET` | `/books` | List books with filters (`title`, `author`), pagination, and ordering |
| `GET` | `/books/{id}` | Get a book by ID |
| `PUT` | `/books/{id}` | Update a book |
| `DELETE` | `/books/{id}` | Delete a book |
| `GET` | `/books/search/semantic` | Semantic similarity search |
| `GET` | `/health` | Health check with DB, version, and uptime |

Full interactive reference at `/docs` (Scalar).

## 🧪 Development

```bash
make check      # lint + typecheck + test
make fmt        # auto-format
make migration m="add books table"
```

## 📖 Documentation

- [PRD](docs/PRD.md) — scope, architecture, and decisions
- [Diagrams](docs/diagrams/) — Mermaid diagrams

### Architecture Decision Records

Short, dated decisions with context, alternatives, and trade-offs.

| # | Decision |
|---|---|
| [001](docs/adr/001-fastapi-over-django.md) | FastAPI over Django/Flask |
| [002](docs/adr/002-uv-package-manager.md) | uv as package manager |
| [003](docs/adr/003-fly-io-deployment.md) | Fly.io for deployment |
| [004](docs/adr/004-openrouter-unified-llm-gateway.md) | OpenRouter as unified LLM gateway |
| [005](docs/adr/005-scalar-over-swagger.md) | Scalar over Swagger UI |
| [006](docs/adr/006-rfc-7807-errors.md) | RFC 7807 Problem Details for errors |
| [007](docs/adr/007-bge-m3-for-multilingual-embeddings.md) | `baai/bge-m3` for multilingual embeddings |

## 🛠 Stack

- **Web:** FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic · SQLite
- **AI:** OpenRouter (chat: `openai/gpt-4o-mini`, embeddings: `baai/bge-m3`)
- **Quality:** Ruff · mypy · pytest · Schemathesis · pre-commit
- **Infra:** Docker (multi-stage) · Fly.io · GitHub Actions

## 📝 License

MIT — see [LICENSE](LICENSE).
