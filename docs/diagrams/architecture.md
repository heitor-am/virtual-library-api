# Architecture

High-level view of the layers and how AI features sit alongside the primary CRUD path.

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

## Notes

- **AI is additive, not in the critical path.** If OpenRouter is unreachable, the service catches the error and the book is still persisted — just without a summary or embedding. The API contract never degrades to 5xx because of a third-party outage.
- **The repository layer is the only place that touches SQLAlchemy.** Services receive/return ORM objects but never build queries themselves.
- **Dependency injection** (`DbDep`, `BookServiceDep`) wires everything at the router level, which is what makes integration tests easy: the `client` fixture overrides `get_db` and `get_book_service` to hand in in-memory SQLite and a stubbed service.

See also: [request-flow.md](request-flow.md) for the detailed sequence of a `POST /books` call.
