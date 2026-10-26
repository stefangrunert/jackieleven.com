# PostgreSQL/BM25 pilot, phase 1

As of 26 October 2026. Baseline: website `3fd28a9`; task branch `codex/search-pilot-database`. No archive data or production services were used. The ten test texts are invented and support no historical conclusions.

## Result and recommendation

**Both candidates were actually installed and queried:** ParadeDB `pg_search 0.26.3` and `pg_textsearch 1.5.1`, each with PostgreSQL `17.11` on Linux ARM64. All 14 SQL assertions for language forms, exact names, phrases with counterexamples, metadata filters, empty results and weighting pass. The complete run, including a small resource experiment, can be repeated using `ops/search-pilot/`.

For the next end-to-end implementation, **ParadeDB is provisionally recommended**, because dedicated analysis fields, phrases and title boosting work directly in one index. This recommendation rests on functionality and integration effort, not confirmed relevance or production suitability. `pg_textsearch` remains a serious alternative: much smaller index files in this small experiment, existing PostgreSQL language analysis and a permissive PostgreSQL licence. Its match conditions and multi-field combination require particularly careful definition. The [project description](https://github.com/timescale/pg_textsearch) states its licence; ParadeDB uses [AGPL-3.0](https://github.com/paradedb/paradedb/blob/v0.26.3/LICENSE).

A dedicated cluster is the safe starting point for the next stage. Both extensions are preloaded in this pilot; an additional database in an existing cluster would not isolate startup configuration or resource budgets. Production was neither inspected nor modified.

## Local prerequisites and pinned versions

Docker CLI `29.2.0`, Compose `v5.0.2` and Docker Desktop `4.60.1 (218372)` are available; the host is `darwin/arm64`, the engine `linux/arm64`. The engine was initially stopped. The first sandboxed call reported missing socket access; the approved retry reported an unreachable daemon. After the authorised `open -a Docker`, the engine became available. `psql` was absent from the host PATH; all database tools ran inside containers.

| Component | Pinned version |
|---|---|
| ParadeDB image | `paradedb/paradedb:0.26.3-pg17@sha256:950f68abebc78e28fd2ecfc8ed915aa29d07b5dd8cba25b2f513ca4e211dda70` |
| PostgreSQL base for pg_textsearch | `postgres:17.11-bookworm@sha256:858bb5e98eed02eb8cafbcdc007f9a65d1b613972028944a8ec2133ccaf80d27` |
| pg_textsearch package | `pg-textsearch-v1.5.1-pg17-arm64.zip`, SHA256 `e65f953e99f47c05dde88a031884cf36ea269bcb62377f554b76ddb4d13fdc3e` |
| Package contents | `pg-textsearch-postgresql-17_1.5.1-1_arm64.deb` |
| Measured ParadeDB database | PostgreSQL `17.11`, Debian Trixie; `pg_search 0.26.3`, `vector 0.8.6` |
| Measured pg_textsearch database | PostgreSQL `17.11`, Debian Bookworm; `pg_textsearch 1.5.1` |

Image digests came from actual pull/inspect results; the package checksum was verified against [release metadata](https://github.com/timescale/pg_textsearch/releases/tag/v1.5.1). `run.py` verifies it before extraction on every run. The pgvector version is pinned by the ParadeDB image. This is an ARM64 pilot; amd64 and the production server OS remain untested. Debian bases differ, so the resource comparison is not strictly controlled.

Installation experience: the full ParadeDB image additionally initialises `pg_cron` by default. With only `shared_preload_libraries=pg_search`, that bootstrap failed. The pilot therefore masks `/docker-entrypoint-initdb.d` with an empty tmpfs, then loads only `pg_search CASCADE`. This also installs `vector`, as described in the [installation guide from version 0.25.0](https://www.paradedb.com/docs/operate/deploy/self-hosted/extension). The PostgreSQL base container built with the verified pg_textsearch DEB without extra packages.

## Isolation and repetition

Prerequisites: running local Docker engine, Python 3, internet access for two images and the approximately 1 MB extension package. Neither host database passwords nor archive files are read. The visible password `synthetic-pilot-only` applies exclusively to disposable pilot databases.

From the repository root:

```sh
python3 ops/search-pilot/run.py
```

The script contains the full commands; principal steps are:

```sh
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml config --quiet
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml build textsearch
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml up -d
# run.py copies only SQL files into /pilot.
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml exec -T parade psql -X -v ON_ERROR_STOP=1 -U pilot -d pilot -f /pilot/parade.sql
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml exec -T textsearch psql -X -v ON_ERROR_STOP=1 -U pilot -d pilot -f /pilot/textsearch.sql
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml down --volumes --timeout 10
```

Project: `jackieleven-search-pilot`. Ports: `127.0.0.1:55471` and `127.0.0.1:55472`; availability is checked before startup and again by Docker. Dedicated internal Docker network without outbound traffic; dedicated volumes `jackieleven-search-pilot_parade-data` and `jackieleven-search-pilot_textsearch-data`. Each container has 1 CPU, 1 GiB memory limit, 256 MiB `/dev/shm`, 10 connections, 128 MiB `shared_buffers`, 4 MiB `work_mem` and 64 MiB maintenance memory. pg_textsearch additionally receives 64 MiB for its memtable cache; that is not a hard whole-process limit.

The script rejects remote Docker endpoints and pre-existing resources using its project name. It changes no unrelated containers. SQL errors abort; assertions use IDs rather than unstable score equality. SQL processing and benchmark queries have ten-second deadlines. A `finally` block removes owned containers, volumes and network after errors or SIGTERM/KeyboardInterrupt. After a hard process/host failure, inspect project state first, then use the targeted `down` command above.

Local results are ignored under `ops/search-pilot/results/`. The checked run is versioned as an immutable text record under [database-evidence](database-evidence/). Downloads remain ignored in `ops/search-pilot/downloads/`; images remain in Docker's cache. No running database is needed to resume work.

## Measured functionality

| Check | Expected / measured | Interpretation |
|---|---|---|
| German: Sänger/Lied/Stadt | IDs 3, 4 in both | ParadeDB language field with German stemmer; pg_textsearch partial index with `german` and explicit FTS predicate |
| English: sing/song | ID 1 in both | English stemming; token/lexeme output included |
| Exact name `Jackie Leven` | IDs 1, 3, 4, 5 | ParadeDB literal field; pg_textsearch candidate uses ordinary SQL equality and a separate B-tree, not BM25 name matching |
| Title phrase `The Deep Pool` | IDs 1, 5 | ID 2 has `The Deep Blue Pool` in the same field, ID 8 `Pool Deep The`: both excluded |
| Phrase + voice + year | ID 1 | Pastiche and later year excluded |
| Unknown word | no results with explicit match predicate | Score sorting alone is unreliable with pg_textsearch |
| Title weight 4 | ID 6 moves ahead of ID 7 | ParadeDB native query boost; pg_textsearch experimental weighted sum of two index scores |

Both German analyses produce `sang`, `spielt`, `lied`, `stadt`; English produces `sing`, `song`, `river`. This confirms only these examples. ParadeDB's `pdb.literal` preserves the whole name including case; PostgreSQL `simple` splits it into lowercase words. Exact name equality therefore deliberately remains a separate path. Diacritic variants, alias resolution and typo tolerance are not yet passed search cases.

Language checks are functional probes, not an identically configured relevance comparison: ParadeDB uses match-any here; PostgreSQL's FTS predicate uses match-all. ParadeDB performs the phrase as an index query. pg_textsearch uses PostgreSQL FTS with `phraseto_tsquery`; the extension supports such predicates but may recheck positions. A successful phrase therefore does not establish an exclusively native BM25 phrase path. The [versioned guide](https://github.com/timescale/pg_textsearch/blob/v1.5.1/README.md) describes language configuration, partial indexes and rechecks. Adding field scores is explicitly neither BM25F nor a recommended later hybrid-fusion strategy.

A relevant correctness finding: pg_textsearch's natural plan for the small filtered ranking query was a sequential scan plus sort and returned five rows although only one matched lexically. A forced BM25 index plan returned one. Forced sequential scoring also returns rows with zero scores for unknown words. Search must therefore use an explicit match predicate; empty-result semantics must not depend on the planner. The ParadeDB plan probe showed a `Custom Scan`, with `voice <> 'pastiche'` as a heap filter. SQL filters alone therefore do not prove complete index pushdown.

## Resource measurements and limits

The ten functional records were supplemented with 99 copies each, producing 1,000 synthetic rows. Indexes were rebuilt and analysed. Both candidates ran the same title phrase and voice/year filter with `LIMIT 5`: ten warm-up transactions followed by 100 transactions using one local socket client. Individual `pgbench` latencies and analysis are in the evidence directory. Figures exclude HTTP, TCP, embedding and reranking time.

| Measurement, final run | ParadeDB | pg_textsearch |
|---|---:|---:|
| Table bytes, 1,000 rows | 180,224 | 180,224 |
| Search index bytes | 3,129,344 (one index) | 131,072 (four BM25 indexes combined) |
| Database bytes | 12,203,699 | 8,148,659 |
| p50 latency | 0.2960 ms | 0.4175 ms |
| p95 latency | 0.416 ms | 0.492 ms |
| Highest observed individual latency | 2.578 ms | 1.537 ms |

Docker stats after the run:

```text
jackieleven-search-pilot-parade-1 CPU=0.06% Memory=33.09MiB / 1GiB PIDs=6
jackieleven-search-pilot-textsearch-1 CPU=0.05% Memory=26.55MiB / 1GiB PIDs=6
```

Memory use is one post-load Docker-stats reading, not a peak or a promise about RAM under concurrency. Database sizes include base catalogues and different extensions. Index coverage and analysis configuration differ. The 1,000 short duplicates simulate neither long columns nor realistic vocabulary. These values establish neither capacity for the shared 4 GB server nor a reliable speed winner. CPU under load, cold caches, concurrent p95, multiple releases and index-build peaks remain unmeasured.

## Researched only or still open

- Official documentation describes [German/English Snowball stemming](https://www.paradedb.com/docs/reference/token-filters/stemming), [literal fields](https://www.paradedb.com/docs/reference/tokenizers/available-tokenizers/literal) and [boosting](https://www.paradedb.com/docs/reference/full-text/relevance-tuning); the named cases above were also executed. Other tokeniser combinations were not evaluated.
- pg_textsearch uses negative scores (lower is better); ParadeDB uses positive scores (higher is better). Scores are not added across candidates. The real test set must separately evaluate language selection, titles, evidence, stopwords, short queries, catalogue numbers, missing results and pastiche.
- No version upgrade was performed. The [pg_textsearch upgrade guide on main](https://github.com/timescale/pg_textsearch/blob/main/UPGRADING.md), accessed 26 October 2026, requires restarting with the new library and running an SQL update, plus reindexing where version-dependent. It was unavailable under release tag v1.5.1 and is explicitly supplementary, mutable documentation. Reverting the binary does not undo index-format changes. Before production, both candidates need actual tests of rebuilding a fresh release index from pinned data, switching versions, interruption, rollback and reconstruction.
- Production OS, architecture, package installation, available RAM, pgvector compatibility and permissions were not checked. Do not transfer the pilot into the existing production cluster without separate acceptance.

## Handover state

The final script run cleanly removed both containers, both data volumes and its network. Docker Desktop remains open; downloaded images and the verified package remain cached. Unrelated services were neither stopped nor changed. Next: load real phase-1 pilot data and independent expectations into the same isolated setup, align analysis/match semantics, then confirm the BM25 candidate.
