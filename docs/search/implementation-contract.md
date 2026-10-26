# Search implementation contract v1

This contract fixes the first working local implementation on `codex/search-development`.
Source website revision: ea653b6 (content adapters read a pinned Git revision); archive revision: 7d353a4.
Private website sidecars may assign document identities for columns without mutating the public archive.

## Ownership

- Pipeline agent: `tools/search/`, SQL schema, dependency file, importer/exporter/state tests.
- Service agent: `cmd/jackieleven-search/`, `internal/search/`, `internal/searchapi/`, Go dependencies, service tests.
- Website agent: `internal/searchclient/`, `internal/site/search*`, website CLI/config/routes, templates/search*, assets/js/search*, website tests.
- Coordinator: `ops/search/`, local runtime configuration, integration/evaluation, review, final documentation.

## Database contract

Postgres 17 + pg_search 0.26.3 + vector 0.8.6 in its own local container (loopback 55473).
Persisted state in schema `indexer_state`; immutable per-build corpus membership in shared tables in schema `search` with a mandatory `build_id` filter. This implements immutable published snapshots without DDL per build in this first implementation; state/build binding must be checked on every retrieval path.

`search.builds`: build_id TEXT PRIMARY KEY, content_version TEXT NOT NULL UNIQUE, data_version TEXT NOT NULL, embedding_profile TEXT NOT NULL, status TEXT NOT NULL (building/ready/failed), created_at TIMESTAMPTZ. A profile may be `none` for lexical-only build. content_version is hash of canonical export AND retrieval/embedding profile, so different profiles receive distinct snapshots.
`search.passages`: row_id BIGSERIAL PRIMARY KEY (BM25 key), build_id TEXT NOT NULL REFERENCES builds, id TEXT NOT NULL, document_id TEXT NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL, language TEXT NOT NULL, source_voice TEXT NOT NULL, text_voice TEXT NOT NULL, text_kind TEXT NOT NULL, year INTEGER NULL (publication year only), url_de TEXT NOT NULL, url_en TEXT NOT NULL, content_hash TEXT NOT NULL, embedding halfvec(1024) NULL, metadata JSONB NOT NULL DEFAULT '{}', UNIQUE(build_id,id).
`search.entities`: build_id TEXT NOT NULL, id TEXT NOT NULL, data JSONB NOT NULL, PRIMARY KEY(build_id,id).
State tables may add implementation-specific fields. Schema creation is owned by pipeline; send any required index SQL to pipeline agent rather than editing its files.

`text` is actual readable source text, never generated context disguised as evidence. The full original graph is retained in entities with provenance, no arbitrary canonical date selection. Year filter means publication year, not concert date. A passage may be a short paragraph or a bounded contiguous chunk of a long paragraph; IDs live in a persistent private registry. Existing anchors are not fabricated: until source page anchors are wired, hits link to a search passage reader that displays exact text plus the original document link.

## Local snapshot manifest

Importer writes an atomic local JSON manifest only after a ready build:
`{"api_version":"v1","build_id":"...","content_version":"...","data_version":"...","embedding_profile":"...","passage_count":123,"document_count":45}`.
Separate website and service load this file at startup, pinning their build/version. No request may select arbitrary schemas/builds. For new datasets restart both with the new manifest; previous manifests support rollback. Normal pages do not depend on DB availability.

## HTTP

Service flags: `-listen 127.0.0.1:8081 -manifest PATH`; DSN env `JACKIE_SEARCH_DATABASE_URL`. DeepInfra key read from `JACKIE_DEEPINFRA_API_KEY` or `JACKIE_DEEPINFRA_API_KEY_FILE`, never logged. Provider access explicit `JACKIE_SEARCH_EXTERNAL=1`, otherwise lexical mode. Default embedding model `Qwen/Qwen3-Embedding-8B`, 1024 dimensions, truncate+normalize identically at build and query. Check official provider API before implementation.

GET `/healthz`: liveness. GET `/readyz`: check manifest/build/schema compatibility, DB availability, not provider availability.
GET `/v1/search?q=...&lang=de&limit=20&mode=lexical|semantic|hybrid&voice=...&from=1990&to=2000&rerank=0|1`.
GET `/v1/passages?id=DOCUMENT%23PASSAGE&lang=de`.
GET `/v1/entities?id=...`.
Require `X-Archive-Content-Version` on internal search/fetch/entity requests; mismatch/missing -> 409 stable JSON code. Public adapters supply the pinned version. mode default hybrid, limit max 50, bounded q and response sizes. Semantic/hybrid degrade to lexical on provider failure; mode/reason/degraded truthful. Embedding-off builds lexical only. Exact miss -> empty hits, DB/network error -> 503, invalid query ->400, capacity ->429, unknown id->404. Do not silently claim requested semantic mode was used if unavailable.

Response search: `api_version`, `content_version`, `data_version`, `search_release`, `mode`, `degraded`, `reason` (optional), `duration_ms`, `hits` array. Each hit: `id` (passage id), `document_id`, `title`, `text` (bounded excerpt), `language`, `source_voice`, `text_voice`, `text_kind`, `url` (production-relative ORIGINAL document link; not claimed exact anchor), `score`, `metadata` optional. Passage response has same version fields plus `passage` with full stored text, same fields, and original document URL. Website links hits through its passage reader, with original document link visible there. Mark excerpts and summaries by text_kind, preserve voices. API describes constraints via checked-in OpenAPI and no raw SQL/provider error bodies.

Website: env `JACKIE_SEARCH_URL` (loopback HTTP), `JACKIE_SEARCH_MANIFEST` path; cmd config flags/env into site.Config. Routes `/de/suche-test`, `/en/search-test` simple SSR test UI; `/de/suche`, `/en/search` may share UI; `/de/suche/textstelle?id=...`, `/en/search/passage?id=...` reader. Include q, language, mode, voice, year filters, optional rerank; show mode/degradation, count, duration, version, error vs empty. All prefixed deployments supported. No provider key in browser. no-store/noindex/no-referrer on search pages. HTML works without JS. Endpoint strings/JSON types documented here are stable; proposals for changes go to coordinator.

## Acceptance

End-to-end local page, genuine BM25 and Qwen embeddings, hybrid RRF, exact readable passage links, correct voices, resumable changed-only importer, new/deleted data handling, service failure and provider fallback, restart/rollback manifests, SQL resource limits, no query/secret logging. Reranker and MCP are adapters after core works; clearly document any remaining scope rather than claiming them implemented.

## Measured local request budgets

The first real corpus showed reranking 20 excerpts needs about 4.5 seconds at the provider. Bounds are therefore 3 seconds for query embeddings, 6 seconds for optional reranking, 10 seconds for the full service request and 11 seconds for the website client. These are ceilings, not latency guarantees or benchmark percentiles. Provider failure still degrades explicitly.
