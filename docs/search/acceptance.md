# Local search acceptance · 26 October 2026

Search works locally and is configured for manual inspection at <http://127.0.0.1:8082/de/suche-test>, with English at `/en/search-test`. The production website was not switched. This is technical acceptance of a first complete search implementation, not approval for public operation or proof of superior search quality.

## Actual corpus and operation

- Website snapshot `ea653b6`, archive snapshot `7d353a4`.
- 572 documents, 7,993 stored passages, 965 complete archive objects.
- 7,730 distinct texts with real DeepInfra vectors from `Qwen/Qwen3-Embedding-8B`; 4,096 source dimensions, truncated to 1,024 and L2-normalised, stored in PostgreSQL as `halfvec`.
- Content version `1b3daae24677b8f27d4428b84078b6950d0c82d9e6f22723557adfc8d8155339`; profile `qwen3-8b-1024-v1`, without generated contextual headers.
- Dedicated PostgreSQL 17.11 container on loopback 55473 with `pg_search 0.26.3` and `vector 0.8.6`; persistent volume, 1.5 GiB/1.5 CPU limit. Two user LaunchAgents supervise search on 8081 and the test website on 8082. Docker Desktop must run.
- Search uses a read-only database role. Website and browser receive no database or provider credentials.

The first real import was interrupted to incorporate two text corrections and switch to bounded parallel batches. On resumption, stored artifacts were reused. The final identical rerun reported **7,730 cache hits, zero missing vectors and zero embedding calls**; the completed build was reused. Unanswered or not-yet-persisted provider calls may recur after interruption; exactly-once billing is not claimed.

## Checks performed

| Area | Result |
| --- | --- |
| Source fidelity | All 7,993 passages checked against 1,075 rendered reference pages; no differences after fixing two multiline Markdown expressions. [Data report](../../tools/search/validation.md). |
| Python pipeline | Registry identity, correction/move/deletion, artifact integrity, bounded concurrency and resumption tested. Twelve tests in total: nine without a database, three additionally run with a real test DSN. |
| Database and permissions | BM25, exact cosine distance, text-voice filters, passage/entity retrieval, two separate builds, version mismatch, reader write prohibition and SQL cancellation checked. |
| Go | `go test ./...`, `go vet ./...` and race checks for search, API, client and website packages passed. |
| Real HTTP integration | `python3 ops/search/check.py --external`: 39 checks passed, including semantic/hybrid search and actually executed reranking. |
| Failures | `python3 ops/search/check-failures.py`: provider disabled → labelled lexical fallback; unreachable database → 503 rather than empty results; separate health/readiness; homepage and contact page remain available when search is down. No test email sent. |
| Browser | German form, semantic results, hybrid search with 20 results and confirmed reranking, and exact passage view checked. English and prefixed operation additionally checked through HTTP/contract tests and the website agent. |
| MCP | Local endpoint active; real `2025-11-25` negotiation and tool list checked. SDK tests cover read-only calls, Host/Origin boundaries and capacity. Tools: `search`, `get_passage`, `get_entity`. No public client integration claimed. |
| Logs | Marked test terms absent from inspected Go and database logs. Test website bypasses the previous MAMP SSL access log. Search pages set `no-store`, `noindex` and `no-referrer`; GET queries may remain in browser history. |

An independent agent reviewed data binding, import resumption, API, link preparation and error handling. Corrections addressed pairwise query association in the reranker, an unnecessary BM25 dependency in pure vector search, and visible provider notices in the website and MCP.

Full-corpus testing found another defect absent from the small fixture: `$7::pdb.boost(3)` fixed the search parameter type such that its text use searched an internal JSON representation. `$7::text::pdb.boost(3)` binds the actual query text first. A fixture containing matching JSON structural words and 18 alternating requests on the same database connection now tests this specifically. Unknown words produce zero lexical matches in the full corpus too.

## Initial relevance observations

[Ten predefined pilot questions](phase-1/validation-cases.json) ran in all three modes: **30 queries without fallback**. Raw observations are in [pilot-search-results.json](pilot-search-results.json); repeat with `python3 ops/search/evaluate.py --external --output docs/search/pilot-search-results.json`.

Eight cases name a specific expected document. One, the persona case, is intentionally not indexed because it has `stufe=weitere`; the result file marks it `in_corpus=false`. For the seven executable cases, the measure is whether the expected document appears among the first ten **passages**, not manually assessed answer quality:

| Mode | Expected document in top 10 | Within the stricter case requirement |
| --- | --- | --- |
| Lexical | 4 of 7 | 4 of 7 |
| Semantic | 3 of 7 | 3 of 7 |
| Hybrid | 6 of 7 | 5 of 7 |

The exact Norwegian title works well lexically and in hybrid mode; the cross-language query benefits from vectors. The expected document distinguishing an announcement from an event is absent from the top ten in every mode. The persona case is an explicit corpus gap, not a measured ranking failure. The name variant ranks ninth in hybrid mode rather than the requested fifth. These give concrete directions for ranking, grouping and later structured-assertion integration. Other results may still be relevant; this table is neither whole-corpus recall nor a complete gold standard. Translations and different paragraphs of the same document currently occupy separate result positions. Exactly identical short texts within the same document, language, voice and text kind are deduplicated before truncating results. At the SQL excerpt limit of 1,201 characters, deduplication is deliberately avoided because texts may differ beyond the limit. Cases 007 and 010 have no document-rank requirement; their domain-specific negative/labelling requirements are not automatically verified by this run.

One sequential run measured 4–20 ms for BM25 and 273–1929 ms for semantic search. Immediately following hybrid queries reused cached query vectors and took 33–38 ms. **These figures are neither a load test nor a fair speed comparison between modes.** Separately measured reranking of 20 excerpts took about 4.5 seconds once; a browser request with another query and reranking took about 1.5 seconds overall. Budgets are therefore bounded at 3 seconds for query embeddings, 6 for reranking, 10 in the search core and 11 in the website client.

During an additional external check, optional reranking fell back once with the appropriate indicator. A subsequent individual check did actually rerank (835 ms total). Local functionality therefore does not guarantee continuous external-provider availability.

Independent live QA also confirmed exact text equality between API and SSR reader and the conflict entity `event/2007-09-27-bodo-public`: both the announcement and the “occurrence not established” qualification remain intact.

## Domain and operational limits

Search retrieves stored texts and generates no answers. The year filter means publication year, not concert date. Source voice and displayed-text voice remain separate. The complete archive object is available through the entity API; a query language spanning all relationships, reliable completeness answers and automated evaluation of disputed assertions are not yet implemented.

Semantic search returns nearest neighbours and may return results even for unanswerable questions. Empty lexical results and outages are technically distinct. Pastiche is not imported. Missing paragraph anchors on original pages are handled through an exact stored-passage view with a separate original-page link.

DeepInfra exposes a mutable model alias. Durable artifacts prevent unnecessary recomputation but cannot guarantee bit-identical future provider responses. Provider/model changes require a profile change, rebuild and renewed relevance testing. Public deployment, quotas, proxy logging, production backup/restore and a sufficiently large held-out quality test set remain separate acceptance items.

Usage, start/stop, source revisions and manifest switching: [local-search.md](local-search.md). Architecture and ongoing status: [suche-architektur.html](../../.dev/suche-architektur.html).
