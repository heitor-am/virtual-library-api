# 005 — Scalar as OpenAPI documentation UI

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

FastAPI ships with Swagger UI (`/docs`) and ReDoc (`/redoc`) out of the box. Both work, both are well-known, and both look dated — especially Swagger's 2010-era styling. For a portfolio project where the docs page is the first thing a reviewer clicks, the default doesn't sell the API well.

Scalar (`scalar-fastapi`) is a modern OpenAPI renderer built for the current generation of API consumers: clean typography, dark mode, a request builder that feels like a proper HTTP client, code samples per language, and good rendering of nested schemas.

## Decision

Replace Swagger UI with **Scalar** at `/docs`. ReDoc stays available at `/redoc` as a secondary view for users who prefer it. OpenAPI JSON is served at `/openapi.json` unchanged.

Integration is two lines in `app/main.py`:

```python
@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    return get_scalar_api_reference(openapi_url="/openapi.json", title=f"{app.title} — Reference")
```

And `docs_url=None` in the `FastAPI(...)` constructor to suppress the default Swagger.

## Consequences

**Positive:**
- Visually sharper docs page — matches the polish level of the rest of the project.
- Built-in request runner handles JSON bodies, auth headers, and file uploads cleanly; easier for reviewers to try endpoints without curl.
- Dark mode by default.
- Zero custom CSS or JS — one function call into `scalar_fastapi`.

**Negative:**
- External package (`scalar-fastapi`) to maintain. If it goes stale, we fall back to ReDoc or re-enable Swagger.
- Less universally recognized than Swagger — some reviewers may expect the classic UI.

**Trade-offs accepted:**
- Adopting a newer library (v1.x as of 2026) in exchange for visible quality uplift. For a public portfolio API the payoff is immediate and the downside is bounded (trivial to revert).

## Alternatives considered

- **Keep Swagger UI** — Safest default, no change. Rejected: doesn't meet the polish bar.
- **Stoplight Elements** — Another modern renderer, comparable quality. Scalar won on simpler FastAPI integration.
- **Custom ReDoc with CSS overrides** — Time sink for diminishing returns vs Scalar's defaults.

## References

- [scalar-fastapi on PyPI](https://pypi.org/project/scalar-fastapi/)
- [Scalar documentation](https://github.com/scalar/scalar)
