# Search data pilot, phase 1

As of 26 October 2026. The pilot contains **16 document candidates: 14 existing archive documents and two explicitly proposed column identities**. Fifteen candidates provide 119 existing passages; the remaining paywall entry is a negative metadata control. This is not a search release and contains neither a pipeline nor new HTML anchors.

Machine-readable inventory: [pilot-manifest.json](pilot-manifest.json). Shared contract proposal: [data-contract.md](data-contract.md). Reproducible local check: [data-check.py](data-check.py).

## Pinned source baseline

- Website baseline: `3fd28a9` (full commit in the manifest); measurement location/worktree `/Users/stefan/.codex/worktrees/search-pilot-data/jackieleven`, task branch `codex/search-pilot-data`.
- Archive: `7d353a4ce8043e284619fe409bfe87238dae2257`, read-only at `/Users/stefan/www/jackieleven-archive`.
- Ninety-six input files are bound by repository, relative path, Git blob and SHA-256. These include source notes, selected archive documents/events and direct metadata dependencies, the published catalogue, three original page images, language routes, templates, schema and coverage register. `local_root` identifies the historical measurement location and can be overridden through checker arguments.
- No provider calls, external-original downloads, API-key reads/copies or archive changes. Existing `live`/`paywall` values are historical source metadata, not current reachability tests.

Local research files were read; DE/EN text layers and original quotations in the website catalogue were separated. Three local original page images were also visually checked: NME, 28 October 1972, printed pages 24/33, and Record Mirror, 20 June 1981, page 18. Both selected column transcriptions were read in full. Other press articles have no complete original transcription here: existing summaries and excerpts were not reclassified as full texts. Independently rechecking every historical cataloguing decision against originals is outside this evidence's scope.

## Selection and actual availability

DE/EN means editorial website summaries. Original language is recorded separately. IDs, paths, specific JSON pointers/line ranges, text checksums, archive evidence references and targets are in each manifest entry; third-party full texts are not duplicated in deliverables.

| Pilot | Source | Available text/original language | Purpose and limit |
|---|---|---|---|
| D01 | NME, 28 October 1972, Gig Guide | DE/EN; English original pages as images | Three folk-club announcements; `primary_document` and `inferred`. Archive ID contains `gig-guide`, website ID does not. Do not infer that events took place. |
| D02 | Ya, 28 January 1976, La Boîte Madrid | DE/EN; two Spanish original excerpts with DE/EN translations | `paywall`, BNE search excerpts only; no complete text, imprecise concert month. Duplicate quotations are not indexed twice. |
| D03 | Record Mirror, 28 October 1978, Roundhouse | DE/EN + English original quotations | Frontmatter anonymous/byline absent; body and archive name Alex Skorecki. Contradiction remains visible. |
| D04 | Sounds, 23 February 1980, Marquee | Bibliographic use only; original EN | Title “Shattered Dolls”, no accessible verdict. `stufe=weitere`: no detail page, zero passages. Uncertain merge with 5 February 1980. |
| D05 | Record Mirror, 9 August 1980, Torrington | DE/EN + English original quotations | Note about truncated OCR/byline coexists with later expanded content naming Graham Stevens. No automatic removal of uncertainty. |
| D06 | Record Business, 15 June 1981, Venue | DE/EN + English original excerpt | Date 8 June 1981? and identity with D07 inferred. |
| D07 | Record Mirror, 20 June 1981, Venue | DE/EN + English original quotations; local original scan | Scan confirms Robin Smith's Doll by Doll text; “Crystal Balls Up” belongs to the neighbouring article. Old ID retained solely for link stability. |
| D08 | Nordlands Framtid, 15 April 1997, Bodø | DE/EN + Norwegian original quotations (`no`) | Review of Den Siste Glæde. Reported stage joke remains an assertion in a third-party report. |
| D09 | Nordlandsposten, 15 April 1997, Bodø | DE/EN + Norwegian original quotations (`no`) | Second voice on the same event. Archive also retains an earlier date set, 5/6/13 April. Heading in research note uncertain. |
| D10 | Guardian, 3 February 2003, Korks Otley | DE/EN + English original quotations | Publication date is not concert date. Recollection of Leven's stage story must not become independently verified biography. |
| D11 | Gaesteliste, 23 February 2003, Gloria Cologne | DE/EN + German original quotations | German original plus English summary; misspelled names/titles do not create new entities. |
| D12 | Whisperin & Hollerin, Leeds 19th Feb | DE/EN + English original quotations | 2005 is inferred; filename date has no greater evidential weight. |
| D13 | KindaMuzik, 22 September 2010, Paradiso | DE/EN + Dutch original quotations | Report on 19 September 2010; unnamed accompanist remains unnamed. Origin claim stays attributed to the reviewer. |
| D14 | theArtsDesk, 13 August 2011, Fringe | DE/EN + English original quotations | Leven portion of a combined review only. Cabaret Voltaire/11 August 2011 comes from an unchecked calendar and is `inferred` in the archive. |
| D15 | Deep Pool, February 2003 | Complete local English original transcription; three pilot paragraphs | Leven's voice: Otley stay, planned Tromsø visit, tour. New archive document ID only proposed; a future Tromsø plan is not evidence of occurrence. |
| D16 | Blog, Bergen/Odda, December 2009 capture | Complete local English original transcription; three pilot paragraphs | Journey, fantastical glacier tunnel, Odda. Capture month is not an event date; first-person narrative is not independent evidence. Archive ID only proposed. |

The selection covers five original languages (`en`, `de`, `no`, `es`, `nl`) and three **existing** archive evidence types (`third_party`, `primary_document`, `inferred`). `self_statement` is a possible later binding for columns, not an existing archive reference in this manifest. Norwegian is not silently narrowed from `no` to `nb`. No pastiche, complete third-party texts or newly researched events were added.

Direct expected-result overlaps with the independent test plan are D01 (1972 announcement, case 008), D02 (Madrid 1976, case 009) and D08 (Bodø 1997, case 006). D09 supplements the Bodø event as a second source but is not independently required by that case. Other cases—Tromsø 2000, Public/Sinus 2007, Sir Vincent Lone, Kevin Foster/O’Foster—remain deliberately outside this small import pilot. They remain useful additional evaluation cases once sources and identity bindings are approved.

## Source → assertion/entity → website

Forty-eight selected evidence references link the 14 archive documents to event time, venue and occurrence status. Assertions supported by both D06/D07 or D08/D09 yield 42 distinct assertion IDs. This sample does not replace a complete graph export. Entire source files are hashed so later imports can retain additional evidence, notes and competing assertions.

Particularly inspectable chains:

- D01 → `event/1972-10-27-portsmouth-star-inn`, `st-886f2bd92670`, status `announced`, `primary_document` → `/de/stimmen/1972-10-28-nme-john-st-field-folkclubs`. The other two dates are separate events; weekdays sometimes lead to `inferred` dating.
- D06/D07 → `event/1981-06-08-london-the-venue`, `st-6d1e5b18eb22`, EDTF `1981-06-08?`, `inferred` → two different critic pages. Do not merge into a single voice.
- D08/D09 → `event/1997-04-13-bodo-den-siste-glaede`, `st-483d637aef04` → two source pages. The complete event file also contains `st-7a54fe0fa988` with an uncertain date set. This alternative is not separately referenced in the sample but must survive the later export.
- D14 → `st-975cb783ec84` (time) and `st-327363694cc8` (venue), both `inferred` → ArtsDesk source page. Do not attribute location/day information absent from the original review to that review.
- D04 → merged Marquee event, but website target only `/de/stimmen?auswahl=0#1980-02-23-sounds-doll-by-doll-marquee-london` in the closed metadata block. No `.../stimmen/<id>` detail target and no passage result.

Twelve quotation references match exact substrings in existing original excerpts. The manifest lists candidates but leaves domain-level binding open: textual agreement alone does not establish the whole assertion. No `passage` references are currently set in the checked archive selection.

## Targets, rights and verification limits

Paths derive from actual catalogue entries, `sourcePage`, `routePath`, language files and templates. Detail pages render DE/EN summaries and original quotations; original and UI languages may differ. Columns appear in English in both interfaces. This result is a source-code/file check, not yet HTTP/browser evidence.

Existing sections use `#quelle`, sometimes `#beleg`, and columns use `#quellenhinweis`. **None of the 119 proposed passage IDs is already an HTML anchor.** Columns also require approval of their new archive identities. These gaps prevent claiming a completed evidence-to-passage path; the draft contract describes next steps.

The archive's `LICENSE-DATA.md` specifies CC BY-NC 4.0 for original project data, excluding third-party quotations, Leven texts and third-party images. D08/D09 have `ccbyncnd` in the website catalogue, checked on 23 October 2026; this is retained as existing metadata, not interpreted as new blanket permission. Many sources have `lizenz=null`. Access (`frei`, `online`, `abo`) is not a licence. The pilot duplicates no full texts, downloads nothing and makes no new legal assessment.

## Checks and resumption

The checker is read-only, using `git show <commit>:<path>`, and can replace historical root paths:

```sh
/Users/stefan/www/jackieleven-archive/.venv/bin/python \
  docs/search/phase-1/data-check.py \
  --website-root /Users/stefan/.codex/worktrees/search-pilot-data/jackieleven \
  --archive-root /Users/stefan/www/jackieleven-archive
```

It needs Python and PyYAML (already available in the archive venv; nothing installed). It checks JSON, pinned revisions/hashes, all text selectors and individual text hashes, unique proposed passage IDs, existing archive/assertion/reference IDs, carried-over evidence types and quotation candidates, website record mappings, detail/catalogue paths, column allowlist and absent paragraph anchors. Passing does not confirm original-content rights, factual correctness or already-working HTTP evidence links.

Outstanding work: registry/identity approval, binding subgraph and evidence review, precise anchors with HTTP tests, and the resumable import itself. On resumption, inspect commit/worktree first, rerun the checker and jointly formalise the contract. No running service or experimental process belongs to this work package.
