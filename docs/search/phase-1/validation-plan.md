# Phase-1 validation plan

As of 26 October 2026

Website baseline: `3fd28a91f7bae2355492b24979ec9688f593c216`

Archive baseline: `7d353a4ce8043e284619fe409bfe87238dae2257`

Status: test plan; the search and failure tests described here have not yet been executed.

## Purpose and scope

This plan prepares independent acceptance of the first data/search pilot. It separates four questions: Is import reproducible from pinned inputs? Are domain distinctions such as announcement, occurrence and uncertainty preserved? Do search service and website honour the version contract? Do ordinary pages and the form remain usable during search outages and load?

The small case set in `validation-cases.json` is a source-based starting set, not a complete gold standard. It can support the initial technical implementation and domain-level debugging. Claims about general search quality, nDCG, recall or superiority of BM25/vector/hybrid configurations require the later assessed development and test sets.

The plan changes neither the public archive nor production services. All import-test mutations occur in copies or dedicated fixtures. Paid external providers stay disabled; a counting substitute deterministically simulates embedding success, delays and failures.

## Pinned test foundation

The following sources were actually read at the stated revisions when selecting cases:

- Architecture and development plan: `.dev/suche-architektur.html` at website commit `3fd28a9`.
- Published editorial source views: `data/quellen.json`, particularly records `1971-11-06-sounds-take-off-your-head-and-listen`, `1972-10-28-nme-john-st-field-folkclubs`, `1976-01-28-ya-folk-rock-escoces-john-st-field-la-boite`, `1997-04-15-nordlands-framtid-en-poetisk-grisegutt`, `1998-10-23-lofotposten-en-perfekt-kveld`, `2000-03-04-nordlys-grisete-sentimental`, `2007-04-05-musicomh-jackie-leven-troubadour-london` and `2007-09-17-puls-jackie-leven-pa-omfattende-norgesturne`, at website commit `3fd28a9`.
- Current detail presentation: `templates/quelle.gohtml`, routing in `internal/site/content.go` and `internal/site/server.go`, at website commit `3fd28a9`.
- Structured archive data: files listed in `validation-cases.json` under `data/document`, `data/event`, `data/person` and `data/persona`, at archive commit `7d353a4`.

Website records contain editorial German/English summaries and sometimes selected quotations in the source language. They are not complete original articles. `source_voice` therefore identifies the historical document's voice, while `text_voice`, `text_kind` and `language` describe the actual passage returned. Selected press documents are `third_party`; a German/English summary is `editorial` and `summary`, while a direct source-language quotation is `third_party` and `original`. With this starting corpus, a German query targeting a Norwegian document primarily checks correct document, language, text-kind and voice mapping. It does not by itself prove purely semantic cross-language performance if a German summary was indexed.

## Passage identities still missing

At the reviewed state, no `passages/manifest.txt` exists and source detail pages have no stable paragraph anchors. Existing section anchors `#beleg` and `#quelle` identify whole presentation sections, not expected citable passages. Cases therefore use real document IDs but explicitly set `passage_id` to `null` with status `not_assigned`.

Before an end-to-end evidence-link test, the data contract must provide a stable passage ID, document ID, source type, language, voice, target URL and an existing HTML anchor for every pilot evidence item. Only then can open fields be populated in a separate traceable step. Guessing an ID from document identity and paragraph number is not an acceptable substitute.

## Test environments and observability

Data testing needs only a pinned export, import command, empty isolated database schema and read-only access to the import registry and search schema. The data agent should provide normalised exports, input manifest, hash rules and passage manifest. The database/search-service agent should supply startup command, schema version, readiness endpoint, API contract and a way to query the active build ID. Missing observability blocks the relevant test; it must not silently pass.

The embedding substitute must count calls by profile ID and full-input-text hash. It stores no real query text outside the test run. Resumption tests must be able to stop import deliberately after a specified number of completed items, inspect registry state and restart the same run.

Every run records at least source revisions, input-manifest hash, pipeline/profile version, run/build IDs, start/end times, state counters, substitute-provider calls, normalised export hash, active schema and each acceptance result. Test logs must contain neither secrets nor visitor search text.

## Execution schedule

Phase 1 supplies the checked test foundation through this document and case set. Because import, API and website integration are not yet implemented, it does not execute the acceptance tests below. Phase 2 checks import, resumption, changes, deletion, HTTP contracts and separate-process outages. Phase 3 uses domain search cases for actual ranking/configuration assessment; only then are relevance metrics collected. Host-load, operational and rollback tests belong to phase-4 operational acceptance. Criteria are defined now so data and search-service implementations can develop independently against shared expectations.

## Import acceptance

### Reproducibility and idempotency

1. Import the same pinned snapshot twice, each time into an empty schema. Both runs must produce the same normalised export hash, membership list and semantically identical table contents. Exclude run IDs, timestamps and technical ordering as non-domain fields before comparison.
2. Process the same snapshot again against the already complete persistent indexing state. The run must neither change domain rows nor create duplicates, and must not call the embedding substitute for already validated profile/input-hash combinations.
3. Vary input-file order in a fixture. Normalised export, membership and result tie-breaks remain identical. The pipeline must not rely on filesystem order or file modification times.

Acceptance: all three comparisons agree; the repeat run reports zero unnecessary substitute-provider calls; unique keys and references remain valid.

### Additions, changes and removal

Create these variants only in a pilot-data copy:

- **Addition:** add an approved document with a genuine new fixture ID to the input manifest. Only its dependent segments and missing artifacts are added; the previous approved build stays active until acceptance.
- **Text correction:** correct an existing fixture passage. Document and passage IDs remain stable, input hash changes, and only dependent segments generate new embedding artifacts.
- **Metadata change:** change a non-embedded field such as evidence locator or target URL. Reading model and link change; identical embedding input/profile produces zero new embedding calls. If the contract places that field in the context header, explicitly treat it as a text change instead.
- **Dependent change:** alter a fixture person's label used in derived `names` or context headers. Import must recompute all dependent segments even if their document file is unchanged.
- **Removal:** an approved item is absent from the complete new manifest or explicitly no longer approved. It is absent from the new build; identity references and targets are checked; the old build stays unchanged until approval. Read errors, incomplete inventories and failed imports must not count as removal. The fixture also distinguishes ordinary snapshot changes from mandatory content withdrawal.

Acceptance: the new build diff contains only expected domain changes. Removed content appears nowhere in its search, resolution or cache. For ordinary snapshot changes, an explicitly approved rollback may restore the older snapshot's membership. Mandatory withdrawal instead prevents publication through old search snapshots, stored texts, vectors and caches as well; rollback must never republish withdrawn content. A failed variant leaves the previous build active unless that build is blocked by such a withdrawal.

### Interruption and resumption

Stop a run after at least one artifact is durable and at least one item remains reserved. After expiry or controlled release of the reservation, resume the same run ID.

Acceptance:

- Work confirmed as `done` is not repeated.
- An expired `running` reservation becomes available; its old worker cannot then complete it inconsistently.
- A validated embedding is durable before `done`, with dimensions, finite numbers and checksum checked.
- Retries are bounded; permanent errors end visibly in `failed`, not an infinite loop.
- Resumed export and build match the uninterrupted reference run.
- An older run finishing later cannot supersede a newer approved build.

A network interruption after potentially successful provider processing is documented separately as a limit: without confirmed provider idempotency, exactly-once paid invocation is not claimed.

## Domain validation of the reading model

Before ranking assessment, check cases directly against export/database. Every expected document/entity ID must resolve; referenced evidence must belong to the pinned document. `announced`, `took_place`, `probable` and `uncertain` remain distinguishable. Neither `took_place_at` nor ranked textual similarity may turn an announcement into proof of occurrence.

For Bodø in April 1997, retain the uncertain early date set `[1997-04-05,1997-04-06,1997-04-13]` with its preview source; later reviews establish 13 April and occurrence. For Bodø in September 2007, retain `Public` and `Sinus` as two announced, unresolved records. Neither merging nor choosing a venue is permitted without additional evidence.

Names are also checked against sources. `Sir Vincent Lone` is a persona linked to `person/jackie-leven` through the documented `performs_as` assertion. `Kevin O’Foster` is the source spelling; the archive records `Kevin O. Foster` as a variant of `person/kevin-foster`. Search may resolve variants but must preserve source spelling in quotations. For every returned text, additionally check the voice contract referenced in the JSON case: document voice, passage voice, text kind and language must be jointly valid. Editorial paraphrase must not appear as the critic's or Jackie Leven's original voice.

## Search cases and evaluation

`validation-cases.json` is valid JSON and records query type, domain intent, actually checked sources, positive/excluded expectations and unresolved passage state per case. For this pilot, `must_return` means at least one named document appears within the specified rank limit, provided the text named in the case is actually in the pilot index. It does not mean all other results are irrelevant. `must_not_assert` governs domain presentation regardless of rank.

Run cases first against BM25 and deterministic name/structure retrieval. Semantic variants follow only when a local substitute-vector path or explicitly approved provider test is available. Store results with configuration, content version and search release. Missing pilot documents are corpus findings, not proof that the search technology returns no matches.

The narrow negative case asserts only that the pinned sources do not establish an Oslo concert on 27 September 2007. The system should return an empty structured result or an answer labelled weak/unsupported. An arbitrary semantic neighbour must not be presented as fact.

## HTTP and version contract

Contract tests start search service and website as separate processes. A stub may replace either partner but must use real HTTP boundaries, deadlines and JSON decoding.

| Case | Acceptance |
| --- | --- |
| Valid `/v1/search` request | 200; response includes `api_version`, `data_version`, `content_version`, `search_release`, `mode`, `degraded`, `hits`; IDs match the bound readiness snapshot. |
| Genuine empty result set | 200 and `hits: []`, not 404 or 503. |
| Expected content version differs | 409 and stable code `content_version_mismatch`; no results from the other snapshot. |
| Foreign content version in a stub's 200 response | Website client rejects the response and shows no results. |
| Unsupported API version or incompatible contract | Controlled 4xx or failed readiness; never silently interpret as v1. Exact error format is fixed in OpenAPI. |
| Embedding or reranking fails | 200 with local results, reduced `mode`, `degraded: true` and stable reason. |
| Invalid request | 400 with stable error code; no SQL, filesystem or provider internals. |
| Capacity limit | 429, with `Retry-After` where meaningful; bounded queue. |
| PostgreSQL or search service unavailable | Search returns 503; website does not present an empty result set. |
| Oversized, late or invalid service response | Website client aborts within budget, bounds bytes read and displays a comprehensible search error. |

Every successful result is additionally checked against document ID, voice, source language, text kind, target URL and passage ID once available. HTML and JSON must share domain search semantics; different interface budgets are explicit configuration.

## Outage and load tests

Before load testing, measure baseline values for an ordinary content page and a local form submission with a test mail transport while search is idle. The load generator uses marked synthetic queries, bounded concurrency levels and no external providers. Increase load to the configured search limit; one additional level verifies controlled 429/503 responses instead of unbounded waiting.

Repeatedly check in parallel:

- An ordinary file-backed content page returns the expected 200 and unchanged core content.
- The form remains available, CSRF/validation errors work, and a valid local test submission reaches the stub mail transport exactly once.
- Website process and form have no search-service database/provider credentials.
- There are no website panics, restarts or exhausted website connection pools.
- Queries respect overall deadlines or are rejected predictably; after load ends, search recovers without manual registry intervention.

Acceptance: ordinary page and form achieve 100% success at every level. Report their p95 alongside the unloaded baseline. Fix the approval threshold as a concrete host budget before running and do not move it after seeing results. Without an agreed prior host budget, only availability—not performance—can be accepted. Search failures must terminate neither website nor form. Repeat with search stopped, refused connections, PostgreSQL down, slow responses, invalid JSON and substitute-provider failure.

## Privacy and negative tests

Send a unique marked query through both HTML and JSON search. Then search the agreed Go, proxy, database and trace logs. The query must be absent; aggregate counters must not contain it as a label or attribute. Responses use `Cache-Control: no-store`; HTML results additionally use `noindex`; search routes use `Referrer-Policy: no-referrer`. This check covers only named local logs. Claims about Cloudflare or production require separate tests there.

Also test invalid filters, unknown IDs, SQL-like strings, very long queries and cancelled clients. `fetch` accepts only known archive IDs. Request values cannot choose schema or database role. Error messages disclose no secrets, local paths or raw queries.

## Report and decision

For every test, the acceptance report records `passed`, `failed`, `blocked` or `not_run`, exact build/content versions, command executed and concise evidence. `blocked` is required when the contract, passage manifest, isolated cluster or observability is missing; it is not qualified success.

The phase-1 validation contribution is acceptable when:

1. Every website/archive ID named in the cases has been checked at the pinned source state.
2. Cases and plan represent text availability, voice, source language, announcement, occurrence, date conflicts, names and negative cases without invented expectations.
3. Future criteria for reproducibility, idempotency, resumption, changes, removal, API/content versions and operational isolation are observable enough to assess data and search-service implementations separately.
4. The machine-readable file is syntactically valid and explicitly marks unresolved passage IDs.
5. Unexecuted tests and remaining blockers are not presented as passed checks.

Later fulfilment of this plan's integration criteria can be established only after execution in phases 2–4. Phase 1 establishes neither an already-working end-to-end implementation nor complete archive coverage, general search quality or production readiness.
