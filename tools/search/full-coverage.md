# Public corpus coverage — 26 October 2026

This report describes the bounded public corpus, not the historical completeness of the archive or a scholarly critical edition. Website inputs are pinned to `11947ff9ed768bdd525defbc1807d6ebb1f88266`; the archive remains pinned to `7d353a4ce8043e284619fe409bfe87238dae2257`. Before selecting that archive revision, HEAD and status were inspected: there were 965 committed data files and only unrelated untracked IDE files. Those files were not read into the corpus or changed.

## Inventory

The export contains **16,217 passages**, **1,752 document identities**, **965 unchanged original graph entities**, and **13,779 distinct text inputs for embeddings**. All **7,730 previous embedding text inputs remain byte-identical members** of the new input set. The embedding profile and provider input construction are unchanged, so their valid artifacts can be reused. New metadata and passages create a new immutable build; they do not overwrite the currently published build.

| Section | Documents | Passages | Actual covered material |
|---|---:|---:|---|
| `music` | 100 | 2,666 | 88 releases, all 881 detailed track rows, displayed format/label/catalog fields, facts, credits, release source labels, catalog notes, listening notes, 5 listening groups with 10 songs, public introduction text |
| `live` | 221 | 1,319 | 220 archive Event records and their statements; one default-visible official concert video with 13 song rows |
| `timeline` | 14 | 122 | All 14 stations, DE/EN title/label/body/image caption fields and original English quotations |
| `writing` | 74 | 1,362 | All 73 allowlisted columns, according to the website reading rules, and its public introduction |
| `press` | 929 | 9,525 | All 741 catalog sources; 500 detail-page candidates and 241 catalog-only entries; public captions/page labels; archive Document/Publication records and statements |
| `biography` | 16 | 588 | 15 published pastiche chapters with language fallbacks and apparatus, plus the explanatory public introduction |
| `site` | 398 | 635 | Public About/Imprint/contact invitation/home text; remaining archive entity types and statements |

The 584 chapter/note/apparatus passages from the pastiche have `metadata.fiction=true`, `source_voice=pastiche` and `text_voice=pastiche`. The four explanatory introduction passages about what a pastiche is are editorial nonfiction. The service must exclude fiction by default and require a deliberate opt-in. Merely importing fiction does not authorize its use as historical evidence.

All 965 original archive objects remain complete JSONB objects. They comprise 250 Documents, 220 Events, 146 Persons, 216 Places, 101 Publications, 20 Groups, 10 Organizations and 2 Personas. All 1,853 statement IDs have readable search representations, including their rank, uncertainty, source references and evidence types. No competing assertion is replaced by a selected canonical date. These representations are labelled archive records, not newly discovered original prose or independent verification of the claims. They are rendered in German with original names, values and quotations retained; this is not a claim that all source material has been translated.

## Public-data boundaries

Adapters use explicit public allowlists and fields:

- Detail-page source paragraphs, original quotations, evidence translations and captions follow their actual website rendering. Duplicate quotations already suppressed by the renderer are not reintroduced.
- `stufe=weitere` sources contribute publicly displayed catalog titles, publication names and page labels. Their stored but unrendered `kurz`, `inhalt`, `beleg` and `zitate` fields are not indexed. Existing catalog anchors are real; no detail page or paragraph anchor is invented.
- Release notes and extra catalog track mentions point to their real catalog entry because they are not rendered on the release detail page. Detailed tracklists, credits and facts point to the release page.
- The pastiche is loaded only for the 15 entries in `data/pastiche.json`. Private chapter plans, editorial frontmatter and the `00-*` working documents are excluded. The published language fallback and apparatus boundaries follow the website adapter.
- The default website excludes fan videos unless `JACKIE_FAN_VIDEOS=1`. The coordinator confirmed that preview keeps this default. Five such groups are excluded; checked, embeddable official material is included. This does not index remote video/audio contents.
- Only allowlisted `research/columns/` files are read from the research tree. No private research notes, credentials, uncommitted files or arbitrary template variables are ingested. Localized static pages fail closed if a new unsupported dynamic template construct appears.
- Existing image/caption data is used; images and facsimiles are not OCRed. Raw YouTube/provider URLs and UI error/configuration strings are not treated as article text.

The explicit file/hash input manifest is part of every private export. It records all actual content and rendering dependencies. `coverage` in the export and CLI plan repeats the machine-readable counts.

## Metadata and links

Every passage has `metadata.section` from `music/live/timeline/writing/press/biography/site` and a Boolean `fiction`. Optional metadata fields are:

| Field | Shape and meaning |
|---|---|
| `image` | Existing `/assets/...` or HTTPS image URL, or null. No generated/downloaded image. The UI validates usable hosts. |
| `display_date` | Display string, preserving uncertain values and alternatives separated by ` | `. A capture date is labelled in column metadata, not converted to a publication date. |
| `place` | Existing archive place labels, multiple alternatives separated by ` | `. |
| `event_status` | `announced`, `took_place`, `cancelled`, `unknown`, or `mixed`; `event_status_values` retains all original status values. |
| `entity_id` | Existing archive ID for archive representations. |
| `record_kind` | `source`, `catalog_source`, `column`, `release`, `track`, `timeline`, `pastiche`, `site`, `listening_selection`, `live_media`, `archive_entity`, or `archive_statement`. |
| `representation` | `displayed_record` for assembled visible public fields, `archive_record` for labelled archive representations. Plain text passages have no extra representation tag. |
| `version_group` | Groups related language versions without claiming sentence-aligned translation. All language variants share the original document identity. |

The top-level `year` remains a publication-year filter. Event dates are not silently placed in it. All Event records preserve their original date alternatives and provenance in the graph and the display metadata.

Original document links remain production-relative. Entities without a published website page use `/de/suche/objekt?id=ENCODED_ID` or `/en/search/entity?id=ENCODED_ID`; the coordinating website implementation supplies the readable entity view. Original graph data returned by the entity API is unchanged. The passage reader supplies the full stored text of each clearly labelled record/chunk and its source link.

## Verification

`check_render.py` compared **13,398 website passages on 1,949 local pages**, with **zero mismatches**. For assembled record rows, it checks each declared public display fragment rather than pretending the assembled record is an original contiguous quotation. The remaining **2,819 archive-record passages** (some long records need a bounded chunk) are separately checked against the complete pinned graph and the 1,853 original statement IDs; they do not claim to be existing website prose.

The full suite ran 19 tests: **16 passed**, while the three PostgreSQL write tests were deliberately skipped during the coordinator's real import. Those existing transactional/recovery cases had passed previously; this update changes adapters, metadata and coverage only, not the database schema or publishing transaction. The new checks cover:

- all published source/catalog members and all seven sections;
- no hidden catalog summaries or private research inputs;
- all pastiche parts explicitly marked as fiction;
- exact graph preservation and complete statement-ID coverage;
- competing Bodø date claims and null event publication years;
- byte-identical repeated export from the same persistent registry;
- retention of every one of the previous 7,730 embedding inputs.

```sh
SEARCH_BASELINE_EXPORT=PATH_TO_PREVIOUS_PRIVATE_EXPORT.json \
  python -m unittest discover -s tools/search/tests -v
python tools/search/check_render.py \
  --export PATH_TO_CURRENT_PRIVATE_EXPORT.json \
  --base-url http://127.0.0.1:18089
```

The temporary reference server was stopped after verification. This work did not make provider calls, write to the archive, or deploy remotely. Real new embeddings, the service's default fiction filter, grouped-result behavior and the remote deployment are integration responsibilities and require their own end-to-end checks.
