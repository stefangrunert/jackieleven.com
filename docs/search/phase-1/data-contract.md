# Draft document, passage and import contract

As of 26 October 2026. **Proposal for joint agreement before phase 2**, not an already implemented export format. It is based on the two Git revisions fixed in the [pilot manifest](pilot-manifest.json) and the architecture in `.dev/suche-architektur.html`. The pilot can be checked against this draft; it is not itself a complete import release.

## Identity and voice

An archive document is the bibliographic original, such as a Guardian review. Its German summary is editorial website text. Neither a German nor an English summary may inherit the original language or voice of its source document.

| Object | Required fields in the proposed export | Meaning |
|---|---|---|
| `document` | `id`, `source_voice`, `document_type`, `title`, `original_language`, `source_inputs`, `source_access`, `rights`, `date_assertions` | `id` matches an existing archive identity; website columns must first be explicitly mapped or registered. Access and rights remain separate. |
| `text_version` | `id`, `document`, `language`, `text_kind`, `text_voice`, `version_group`, `source_input`, `source_selector`, `raw_text_sha256` | A specific version: original, translation or summary. `text_voice`: `leven`, `third_party`, `editorial`, `pastiche`. In the phase-1 manifest this is recorded for each unit as `text_units.text_voice`. |
| `passage` | `id`, `document`, `text_version`, `text`, `source_selector`, `raw_text_sha256`, `display_text_sha256`, `target`, `status` | A citable, independently identified passage; text and target must agree in the published snapshot. |
| `evidence` | `subject`, `statement_id`, `predicate`, `reference_index`, `document`, `evidence_type`, `locator`, `quote`, `passage`, `binding_status` | Assertion and source remain traceable without alteration. `passage=null` is allowed but means the evidence cannot be resolved precisely. |
| `segment` | `id`, `document`, `text_version`, `passages`, `text`, `language`, `text_kind`, `text_voice`, `retrieval_profile` | Derived indexing unit. Must not cross document, voice, language or version boundaries. |

`source_voice` describes the original document; `text_voice` describes the text actually searched. Result grouping follows `text_voice`. Provenance also names the original and its voice. DE/EN summaries share a `version_group`, which does not imply sentence-by-sentence translation. An original quotation and its explicitly available translations share a different group. Original quotations displayed identically on DE and EN pages are one text version with two targets, not two index copies.

A Leven statement reported by a journalist initially retains `third_party` as the transmitting text voice. `asserted_by`/speaker, mediation and archive evidence type are preserved separately; not every quotation in a concert review becomes a directly available self-statement. Pastiche never serves as evidence for a historical assertion. Its possible later inclusion in search remains open; it is absent from this pilot.

Date is not a single ISO field inferred from a filename: publication, archival capture and event time are separate assertions. EDTF uncertainty, alternatives, `rank`, `certainty`, notes and evidence types remain intact. Under the archive schema, missing rank means `normal`, not `preferred`; missing certainty means unknown. A record name such as `event/1981-06-08-...` does not override an actual value of `1981-06-08?`. Status `announced` does not become `took_place`.

## Stable passages, changing segments

The archive schema expects `document/<key>#<passage>`. The proposal is a permanently maintained sidecar registry with a `p-<opaque-id>` identifier for each semantically coherent passage. It is versioned alongside import data; its final maintenance location must be agreed with the archive owner before phase 2. This phase writes nothing to the archive.

The manifest's 119 `proposed_passage_ref` values are **reservable draft identifiers**, not existing archive references, HTML anchors or public `/id/` addresses. For traceable initial allocation, UUIDv5 values were derived from document identity and the then-current JSON pointer or starting line (URL namespace; first 20 hexadecimal characters after `p-`). The precise rule is in the manifest. Once accepted, these IDs are frozen in the registry. Later movement or correction must **not recalculate them from position or content**. Collisions are input errors; IDs are never reused.

Each registry entry includes current source selectors, version, full text/context hash, preceding/following context, reason for change and any predecessor/successor. A simple typo correction or move retains the ID after mapping review and increments its content revision. Substantive replacement, splitting or merging creates new IDs; old IDs remain as tombstones with precisely described successors. Ambiguous mappings pause for review. Identical text in two places does not prove passage identity. Existing evidence bindings must be reviewed after substantive text changes.

Search segments have separate recomputable IDs derived from document/version, ordered passage membership, segmentation profile and normalised segment text. Resegmentation changes segments, not passage IDs. The architecture's 150–400-token target belongs in the segmentation profile, not in a paragraph's historical identity.

## Evidence binding and target contract

The phase-1 manifest contains 48 selected evidence references to 42 distinct assertions, **not a complete graph export**. Selection is limited to event time, venue and occurrence status for the selected documents. Twelve references contain quotations found as exact substrings in available original excerpts; `candidate_passage_refs` records these candidates. This establishes textual agreement, not that the quoted sentence supports the entire assertion. All bindings remain `unbound`/`needs_semantic_review`. Without a quotation, topical similarity alone creates no binding. An editorial summary cannot replace the original location supporting an archive assertion.

The complete phase-2 export must carry every assertion, its rank, certainty and all references in the agreed subgraph. Complete entity files included in the pilot are a verification basis, not instructions to publish their entire surrounding graph unchecked. External graph dependencies are either loaded as clearly labelled metadata stubs with IDs/labels or explicitly marked outside pilot scope. Competing date assertions, such as Bodø 1997 or Marquee 1980, must not silently disappear.

`target` contains language-dependent production-relative paths without host or preview prefix, an actual HTML anchor and the bound content version. The website client adds its prefix exactly once. It selects a suitable UI language without changing the quoted passage's language. If a translation is missing, the available original may be shown with its actual language. Section anchors may be declared only as section-level precision; they are not paragraph evidence.

Existing manifest targets were checked against router, catalogue and templates. Detail pages have no paragraph anchors. Phase 2 must insert `id="p-..."` at the actual rendered location from the same sidecar and verify it through HTTP/DOM checks. This also applies to original quotations whose duplicates the current renderer suppresses. D02 therefore contains the two `beleg` originals and their translations, without also including their identical `zitate` entries.

D04 has no detail page because of `stufe=weitere`. Its catalogue target `?auswahl=0#...` identifies metadata inside an initially closed `<details>` element, not readable passage evidence. It stays outside the passage index. D15/D16 still lack confirmed archive document identities. Until assigned, a strictly archive-compatible import deliberately rejects these two candidates; phase 1 does not invent existing documents.

## Input manifest and reproducible import

A future import binds `format_version`, both full Git commits, an explicit file allowlist with byte SHA-256, the passage registry, exporter/extraction/normalisation/segmentation profiles and optional embedding profile. Local paths are measurement locations, not portable identities. The checker accepts `--website-root` and `--archive-root`; Git revision, relative path and hash are authoritative. Production imports accept only approved snapshots, never changing working files.

Source-integrity checks perform no normalisation: file SHA-256 over bytes; JSON-field hash over the exact decoded UTF-8 string; Markdown selections over inclusive lines joined with LF and no trailing LF. The manifest uses these rules. A later `display_text_sha256` comes from a precisely defined website-text adapter; Markdown markup, navigation and headings must not accidentally enter the index. The importer must obtain the same reading text as `LoadColumns`/`ColumnReadingText` and the same duplicate rules as `templates.go`. Do not declare an independent heuristic parser authoritative prematurely.

Normalised exports use UTF-8, a fixed Unicode rule, explicit nulls, sorted object keys and deterministic ID ordering for sets. Meaningful order—paragraphs, segment passages, reference positions—remains intact. Canonical serialisation and test vectors must be agreed before phase 2. Timestamps and local paths do not belong in content identity. Identical input snapshots must produce byte-identical canonical exports; external vectors are retained as artifacts, not assumed deterministically reproducible.

| Change | Derived data to invalidate | Reusable |
|---|---|---|
| Passage wording/extraction | Text revision, segmentation, lexical index, affected embeddings | Unchanged other segments |
| Author/date/source title in context header | Metadata, display, actual embedding input | Vectors only if the entire input remains identical |
| Entity label/alias/evidence/rank | Entity/evidence export, filters, display; inspect context dependencies | Text vectors with unaffected input fields |
| Website path/anchor only | Target mapping, website content manifest, link checks | Vectors and unchanged segment texts |
| Segmentation profile | Segments and affected index entries | Passage registry; identical embedding inputs |
| Model/revision/tokeniser/pooling/instruction/truncation/normalisation/provider | New embedding profile and compatible search snapshot | Source texts/evidence; old rollback artifacts |
| Removal | New build membership; tombstones/evidence review | Active old build until an approved switch |

Dependencies form a directed graph: input files → document/version/evidence/entity → passages → segments/context headers → artifacts → build. File changes trigger selection and hash comparison; they do not automatically require embeddings for every entry in the large `quellen.json`.

The durable registry follows the architecture: `runs`, `run_items`, `artifacts`, `builds`, outside immutable release schemas. Items follow `pending → running → done` or end in `failed`; failures additionally record code, retryability and, where applicable, next-attempt time. `running` requires a lease and bounded retries. `done` requires a validated, durably registered result. Artifacts are first written under temporary names, checked for dimensions/profile/checksum, then registered atomically. After a crash, an expired lease may release work; validated artifacts are reused. A paid provider call whose response is lost before durable storage can incur another charge without provider idempotency: no unsupported exactly-once promise.

A build records complete membership, content version, export hash, profiles, schema format, compatible API version and approval status. Registry publication occurs in a database transaction only after complete validation; failed builds do not affect the active build. That transaction does not atomically switch website, search service and nginx together. Activation and version checks follow the coordinated release procedure in architecture section 7. Website and search service must confirm the same approved combination of texts, passages and targets. Without that binding, readiness fails. Deletions require a complete, successfully enumerated snapshot; an unreachable source file is not a deletion instruction.

## Decisions required before phase 2

1. Registry location and formal approval of proposed passage and column identities.
2. Binding JSON schema, canonical serialisation and text adapter, including voice/language test cases.
3. Complete pilot subgraph with stubs, all competing assertions and checked evidence bindings.
4. Publication of paragraph anchors and HTTP checks covering preview prefixes, languages and D04 exclusion.
5. Resumption, addition, correction, deletion and failed-build tests without provider calls; embedding cache later, using an approved profile.
