# 006 — RFC 7807 Problem Details for HTTP error responses

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

APIs need a consistent format for error responses. FastAPI's default is a single `{"detail": "..."}` shape, which is fine but limited:

- Callers can't easily distinguish error types programmatically without parsing the `detail` string.
- No standard field for an error URI, application-specific code, or which resource caused the error.
- Each endpoint tends to drift — some return `{"error": ...}`, some return `{"detail": ...}`, validation errors return a nested array, custom exceptions return something else.

[RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) defines a standard machine-readable error format (`application/problem+json`) with fields `type`, `title`, `status`, `detail`, `instance`. It's adopted by major APIs (Stripe-adjacent, GitHub's newer endpoints, most enterprise APIs).

## Decision

Every error response in this API returns **RFC 7807 Problem Details** with `Content-Type: application/problem+json`, including validation errors (422) and our application-level exceptions (`BookNotFoundError`, `LLMUnavailableError`).

One extension: we add a non-standard `code` field carrying a machine-readable application code (`BOOK_NOT_FOUND`, `VALIDATION_ERROR`, `LLM_UNAVAILABLE`). This complements the spec's `type` URI — `type` is for human-readable docs, `code` is for programmatic branching in clients.

Implementation:
- `app/schemas/problem.py` — the Pydantic `ProblemDetails` model
- `app/core/exceptions.py` — `AppError` base class with `app_error_handler` and `validation_exception_handler`
- `app/main.py` — handlers registered on the FastAPI app

## Consequences

**Positive:**
- Clients can reliably dispatch on `code` or `status` without string-matching English error messages.
- Every error has the same shape — easier for client SDKs, easier for Schemathesis/contract testing.
- `type` URIs (`https://app/errors/book-not-found`) give a place to publish human-facing error docs in the future.
- `instance` echoes the request path, useful when logs are aggregated without the request line.

**Negative:**
- More verbose than a bare `{"detail": "..."}`. Responses are ~200 bytes instead of ~50.
- Custom `code` field is a non-standard extension. Documented in the OpenAPI schema, but still an idiosyncrasy.

**Trade-offs accepted:**
- Accepting the verbosity as the price of interoperability. The spec is small, well-known, and lets the API feel grown-up with little effort.

## Alternatives considered

- **Bare FastAPI default** — Easiest, zero setup. Rejected: inconsistent across endpoint types.
- **JSON:API error objects** — Larger, more opinionated spec. Overkill for a resource-light API.
- **Custom flat format** — Bespoke, no standard to point to. Rejected: violates "pick boring standards where possible."

## References

- [RFC 7807 — Problem Details for HTTP APIs](https://datatracker.ietf.org/doc/html/rfc7807)
- [RFC 9457 — Extends RFC 7807 (newer successor, largely compatible)](https://datatracker.ietf.org/doc/html/rfc9457)
