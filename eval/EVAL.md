# Evaluation Report — PostgreSQL RAG

**Date:** 2026-11-14  
**Model:** gemini-3.8-flash  
**Embedding:** gemini-embedding-001  
**Corpus:** 12 pages, 374 chunks (PostgreSQL 16 runtime config)  
**Retrieval:** Dense-only (Chroma, top-k=5)  

---

## Test Set Design

40 questions total, 4 categories:

| Category | n | Purpose |
|---|---|---|
| normal | 10 | Semantic queries with explicit answer |
| exact_token | 10 | Parameter-name queries (e.g., `max_connections`) |
| unanswerable | 10 | Questions whose answers are NOT in corpus |
| hard_multi_hop | 10 | Multi-hop reasoning / parameter interactions |

---

## Baseline Results

| Category | Metric | Result |
|---|---|---|
| normal | Recall@5 | **1.00** (10/10) |
| normal | Grounding rate | 0.90 (9/10) |
| exact_token | Recall@5 | **1.00** (10/10) |
| exact_token | Grounding rate | 1.00 (10/10) |
| unanswerable | Correct refusal rate | **1.00** (10/10) |
| hard_multi_hop | Pass rate | 0.80 (8/10) |
| Overall | p95 latency | ~6.0 s |
| Overall | Mean latency | ~4.8 s |

---

## Failure Analysis

### Failure 1: `max_wal_senders` not retrieved

**Query:** "What is the default for max_wal_senders and how does it differ from max_replication_slots?"

**Observed:** Top-5 chunks did not contain `max_wal_senders` or `max_replication_slots`.

**Root cause:** These parameters live in `runtime-config-replication.html`, which is **not in the 12-page corpus**. The corpus only covers connection / resource / WAL / query / client / error / logging / preset / custom / compatible / locks / statistics — replication is missing.

**Fix (Phase 8):** Add `runtime-config-replication.html` to `PAGES` and re-ingest.

---

### Failure 2: Multi-hop tuning question

**Query:** "If I set max_connections to 500, what other parameters should I adjust?"

**Observed:** Top-5 chunks contained `max_connections` but not `superuser_reserved_connections` or `shared_buffers`, which the answer requires.

**Root cause:** The answer spans **multiple chunks** across different sections. Dense retrieval with top-5 returns chunks that are individually similar to the query, but not the combination needed for multi-hop reasoning.

**Fix (Phase 8):** Hybrid search (BM25 + dense) + increase top-k to 10, or add a reranker.

---

## Limitations

1. **Small corpus** (374 chunks): Recall@5 is likely inflated compared to a 2,000+ chunk corpus.
2. **Test set authored by one person**: possible selection bias.
3. **Single model**: no comparison against a stronger baseline (e.g., gemini-3.8-pro).
4. **Dense-only retrieval**: no BM25, no reranker, no query expansion.
5. **Latency**: p95 ~6s, dominated by LLM generation, not retrieval.

---

## Next Steps

- Phase 6–7: Dockerize and deploy to Hugging Face Spaces
- Phase 8: Add `runtime-config-replication.html`, re-evaluate; try hybrid search
- Phase 9: Update README with before/after numbers