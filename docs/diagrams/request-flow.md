# Request flow — `POST /books` with auto-summarize + embed

Shows the end-to-end path when a client creates a book **without a `summary`**, with AI features enabled. Dashed arrows on the AI path are tolerated failures: the book is saved regardless.

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant R as /books router
    participant S as BookService
    participant Sum as generate_summary
    participant E as generate_embedding
    participant OR as OpenRouter
    participant Repo as BookRepository
    participant DB as SQLite

    C->>R: POST /books<br/>{title, author, published_date}
    R->>S: create(db, **payload.model_dump())

    Note over S: AI available?<br/>(flag on + API key)
    alt Summary missing and AI available
        S->>Sum: generate_summary(title, author)
        Sum->>OR: chat.completions.create<br/>model=OPENROUTER_CHAT_MODEL
        OR-->>Sum: "Generated summary..."
        Sum-->>S: summary
        Note over S: data.summary = generated<br/>data.summary_source = "ai"
    end

    S->>E: generate_embedding(build_book_text(title, author, summary?))
    E->>OR: embeddings.create<br/>model=OPENROUTER_EMBEDDING_MODEL
    OR-->>E: float32 vector<br/>(length model-dependent)
    E-->>S: bytes (BLOB)
    Note over S: data.embedding = blob<br/>data.embedding_model = configured model

    S->>Repo: create(**data)
    Repo->>DB: INSERT INTO books
    DB-->>Repo: Book
    Repo-->>S: Book
    S-->>R: Book
    R-->>C: 201 BookRead
```

## What happens on failure

- **OpenRouter unreachable / rate-limited** — `APIError` bubbles from the client; the service `try/except` in `_enrich_with_summary` / `_enrich_with_embedding` swallows it, leaves the fields unset, and continues to the repository.
- **Retry** — the OpenRouter client has `tenacity` applied: 3 attempts with exponential backoff (1-10s) on `APIConnectionError`, `APITimeoutError`, `RateLimitError`. Auth and bad-request errors are NOT retried.
- **AI disabled** (`AI_FEATURES_ENABLED=false` or missing key) — both `if` branches skip the AI calls entirely; `POST /books` acts like a plain CRUD write.

See also: [architecture.md](architecture.md) for the big-picture layered view.
