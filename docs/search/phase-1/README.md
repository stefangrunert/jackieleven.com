# Phase 1: search foundations

As of 26 October 2026. Integration branch `codex/search-development`.

The [architecture, agent plan and work status](../../../.dev/suche-architektur.html) form the main continuous document. Phase 1 establishes data, technology and validation foundations. It does not yet implement a production search service or importer.

## Results

| Work package | Deliverable | Actually checked |
|---|---|---|
| Data pilot | [Report](data-pilot.md), [draft contract](data-contract.md), [manifest](pilot-manifest.json), [checker](data-check.py) | 96 file hashes, 16 document candidates, 119 text selectors, 48 evidence references to 42 assertions, 12 exact quotation candidates |
| Database pilot | [Report](database-pilot.md), [measurements](database-evidence/manifest.txt), [experiment files](../../../ops/search-pilot/) | Both candidates on PG 17.11/ARM64; 14 SQL assertions; 1,000 synthetic rows, 100 warm single-client measurements each |
| Independent validation | [Test plan](validation-plan.md), [ten cases](validation-cases.json) | Bound sources, IDs, routes and text locations; later import/search/load tests explicitly not executed |

The data pilot contains 14 existing archive documents and two columns with proposed archive identities. One metadata entry has no indexable text. The 119 passage IDs are proposals, not already published HTML anchors. Source voice and actual text voice remain separate.

Website source baseline: `3fd28a91f7bae2355492b24979ec9688f593c216`. Archive baseline: `7d353a4ce8043e284619fe409bfe87238dae2257`. No changes or publication in the archive repository, no DeepInfra calls. Existing website runtime files were unchanged in this phase.

## Integration decisions

- **ParadeDB 0.26.3 is the provisional phase-2 candidate.** Functional checks favour its more direct multi-field/phrase path. Relevance, real archive texts, production amd64 architecture and server capacity are not yet accepted. pg_textsearch 1.5.1 remains a documented alternative.
- **Text voice is a separate property.** The contract uses `source_voice` and `text_voice`; editorial summaries are not original quotations. Initial grouping uses `text_voice`.
- **Pipeline states:** `pending`, `running`, `done`, `failed`, with separate retry metadata. `done` requires a validated durable result. Naming was aligned between architecture and draft contract.
- **Publication is not deployment.** Transactional registry publication does not replace coordinated activation of two services and nginx; content-version checks remain necessary.
- **No automatic expansion of the public archive.** Phase 2 prepares traceable mappings for column identities, the passage registry and evidence bindings.

## Aligning pilot data and test cases

Data and validation agents selected independently. This deliberately does not produce an immediately executable ten-case search suite:

| Case | Document in current pilot | Still required |
|---|---|---|
| `p1-date-conflict-006` | yes, D08/D09 | complete competing assertions in the subgraph; real anchors |
| `p1-announcement-only-008` | yes, D01 | preserve announcement status; real anchors |
| `p1-cross-language-inference-009` | yes, D02 | preserve original excerpts, translations and uncertainty separately |
| `001`, `002`, `003`, `004`, `005`, `007` | expected documents outside this selection | controlled pilot-manifest expansion before execution |
| `p1-negative-010` | no expected positive hit | explicitly bound the negative space to the published corpus; add context for the place-name confusion |

Missing inputs mean `blocked` or `not_run`, not failed search or a passed test. Freeze the corpus and expected evidence together before comparing rankings. A German query retrieving a German summary does not establish purely semantic cross-language performance.

## Independent review

The validation agent additionally reviewed data commit `cfc811ecceec7709e9542991f477136c1ed44153` independently: no blockers for the phase-1 proposal. Alongside the read-only checker, all 119 draft IDs were reproduced from the bootstrap rule, and text voices/languages plus the three direct test-case overlaps were cross-checked. The coordinator reran the checker successfully in the integration repository and compared the database experiment's eleven source checksums with the integrated files.

Before phase 2, the binding validator will gain explicit rules for translation voice/version group and mapping column authors to `source_voice=leven`. The current data was checked manually for these properties; the phase-1 checker does not claim full schema coverage. Inconsistent state names and the imprecise overlap description were corrected during integration.

## Resuming work

The three task branches are `codex/search-pilot-data`, `codex/search-pilot-database` and `codex/search-pilot-validation`; managed worktrees are under `/Users/stefan/.codex/worktrees/search-pilot-*/jackieleven`. They remain available for review and later tasks. The integration branch contains their checked deliverables and documented contract corrections.

Read-only source check from the integration repository:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/stefan/www/jackieleven-archive/.venv/bin/python \
  docs/search/phase-1/data-check.py \
  --website-root /Users/stefan/www/jackieleven \
  --archive-root /Users/stefan/www/jackieleven-archive
```

Repeat the database experiment separately only if needed:

```sh
python3 ops/search-pilot/run.py
```

It creates dedicated temporary containers/volumes, uses synthetic data and cleans up afterwards. The completed experiment removed its containers, volumes and network. Docker Desktop remains running; images and package downloads stay cached locally. No running pilot database needs to be carried into phase 2.

Next development step: formalise the data contract as schema and API contract, assign registry location and identities, create a complete pilot subgraph, then implement the read-only BM25 path between the separate service and website. Detailed steps and acceptance criteria are in the main document. No test or production deployment yet.
