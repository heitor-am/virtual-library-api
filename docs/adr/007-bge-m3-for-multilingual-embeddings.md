# 007 — `baai/bge-m3` as the default embedding model

- **Status:** accepted
- **Date:** 2026-04-18
- **Deciders:** @heitor-am

## Context

Semantic search embeds each book's `title + author + summary` and compares query vectors via cosine similarity. The corpus is in **Brazilian Portuguese** (classic literature, AI-generated summaries in pt-BR). Model choice directly affects retrieval quality.

Constraints:
- Must be accessible through OpenRouter (ADR-004) to keep the single-gateway story intact.
- Must handle Portuguese well; English-only models will trail.
- Embeddings are stored as BLOBs in SQLite, so vector size affects disk footprint and memory during `bulk_cosine`.
- Cost per 1k tokens matters because it multiplies across every insert/update.

## Decision

Default the embedding model to **`baai/bge-m3`** (BAAI's multilingual open-source embedding model), served via OpenRouter. Dimensionality: 1024. Supported input context: 8192 tokens.

The model name is environment-driven (`OPENROUTER_EMBEDDING_MODEL`) so it can be swapped at runtime; the book record stores the model used (`embedding_model` column) so legacy vectors can be detected and re-embedded after a migration.

## Consequences

**Positive:**
- **Strong multilingual retrieval quality.** `bge-m3` is one of the top open-source multilingual embedding models on MTEB benchmarks in 2024-2025, and it handles Portuguese on par with English.
- **$0.01 per 1M tokens via OpenRouter** — roughly half the cost of `text-embedding-3-small` at the time of writing. For our scale (tens of books with ~500-token concatenated text each), embedding cost is effectively zero.
- 8192-token context handles long summaries comfortably; we won't hit truncation at realistic sizes.
- 1024 dims is a middle-ground that keeps SQLite BLOB storage light (4 KB per book) while retaining enough dimensionality for good separation.
- Open-source model — no vendor lock to OpenAI-only embeddings. If we ever self-host, we can run the same model locally via `sentence-transformers` or Infinity.

**Negative:**
- Less well-known brand than OpenAI's embeddings — some reviewers will need to look it up.
- MTEB benchmarks are a proxy; in-domain retrieval quality still depends on the corpus. Not validated on a formal Portuguese literature benchmark.

**Trade-offs accepted:**
- Choosing a vendor-neutral open-source model over `openai/text-embedding-3-small`. Slight loss in brand recognition for a win on cost, portability, and multilingual quality.

## Alternatives considered

- **`openai/text-embedding-3-small`** — 1536 dims, proven, slightly better on English benchmarks. Rejected: doubles cost, English-biased, vendor-locked name even if the API is via OpenRouter.
- **`openai/text-embedding-3-large`** — Higher quality but 3x the dims (3072) and much higher cost. Overkill for our scale.
- **`sentence-transformers/all-MiniLM-L6-v2`** — Cheap, well-known, 384 dims. Rejected: English-only in practice, weaker Portuguese handling.
- **Self-hosted `bge-m3`** — Same model, ~400 MB download, adds memory to the Fly.io machine, no cost per call. Rejected for now (OpenRouter is cheap enough and keeps the VM small); could revisit if usage scales.

## References

- [BAAI/bge-m3 on Hugging Face](https://huggingface.co/BAAI/bge-m3)
- [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [OpenRouter embedding models](https://openrouter.ai/docs/embeddings)
- ADR-004 (OpenRouter as gateway)
