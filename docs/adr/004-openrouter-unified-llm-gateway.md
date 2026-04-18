# 004 — OpenRouter as unified LLM gateway

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

Two AI features need external services: LLM chat completions (automatic book summary generation) and text embeddings (semantic search). Both are also reused across sibling portfolio projects (a chatbot and a RAG search system), and each project ideally should let us swap the underlying model without a deploy — for A/B comparisons, cost optimization, or provider outages.

Using the OpenAI API directly solves one provider. Picking Anthropic directly solves another. Picking them in parallel means two API keys, two billing accounts, two SDKs in the codebase (or coercion), and two rate-limit dashboards to watch. Meanwhile the integration code (chat completion, embedding call) is trivially the same shape across providers.

## Decision

Use **OpenRouter** as the single LLM gateway. It exposes an OpenAI-compatible API at `https://openrouter.ai/api/v1`, so the official `openai` Python SDK works unchanged — just override `base_url`. Provider/model selection becomes an env var (`OPENROUTER_CHAT_MODEL`, `OPENROUTER_EMBEDDING_MODEL`).

Default models:
- Chat: `openai/gpt-4o-mini` (~$0.001 per summary)
- Embeddings: `baai/bge-m3` (see ADR-007)

## Consequences

**Positive:**
- **One API key, one account, one billing dashboard** — and one spend cap via OpenRouter's prepaid credit model (no surprise bills).
- **Swap models with an env var** — no code change to migrate from `gpt-4o-mini` to `claude-3.5-haiku` or to a local-hosted model that exposes an OpenAI-compatible endpoint.
- The same `app/ai/client.py` wrapper is reusable verbatim across the three sibling portfolio repos.
- OpenRouter supports `HTTP-Referer` and `X-Title` headers for per-app usage attribution in the dashboard — useful when more than one app consumes the same key.
- Built-in failover and routing — if a specific provider is degraded, OpenRouter can retry internally.

**Negative:**
- Added latency hop: OpenRouter is a middleman. Typically 50-200ms overhead vs direct provider call.
- Slight markup on model pricing — usually under 10% vs direct API prices.
- Dependency on a third-party aggregator that could change pricing or policies independently of the underlying provider.

**Trade-offs accepted:**
- Accepting the latency/markup cost in exchange for vendor-agnostic tooling and a portable `app/ai/` layer. For this project's scale (a few calls per book creation), both costs are negligible.

## Alternatives considered

- **OpenAI SDK directly** — Simplest, fastest, but locks to OpenAI models and makes comparing providers a code change.
- **LiteLLM as a library** — Also abstracts providers but runs in-process. More code surface; each deploy ships the provider adapters. OpenRouter does this as a service instead.
- **LangChain's multi-provider abstractions** — Heavier than needed; LangChain is in scope for the sibling chatbot project but overkill here.

## References

- [OpenRouter docs](https://openrouter.ai/docs)
- [OpenRouter quickstart with OpenAI SDK](https://openrouter.ai/docs/quickstart)
- ADR-007 (embedding model choice)
