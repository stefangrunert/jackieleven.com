# Indexer validation, 26 October 2026

Scope: pinned website `ea653b6`, archive `7d353a4`; importer worktree `/Users/stefan/.codex/worktrees/search-pilot-data/jackieleven`. No public archive changes or real provider calls were made by this agent. Real cost-bearing imports are separately orchestrated by the coordinator.

## Corpus and rendered-text check

The complete export contains **572 represented documents, 7,993 passages, 965 full archive graph entities and 7,730 distinct embedding inputs**. Inputs include all allowlisted columns and the publicly rendered source paragraphs/quotations; Pastiche and unrendered `weitere` detail fields are excluded. Private search identities are explicitly marked and do not alter the public graph.

A separate reference website was briefly started on `127.0.0.1:18089` from this worktree. `check_render.py` fetched **1,075 local pages** and checked all **7,993 passage texts** against their rendered readable text, normalizing only whitespace for the comparison and excluding script/style contents. Short source summaries were compared with the catalog, where they are actually rendered. The check found two multiline Markdown-emphasis mismatches in the 2021 Guardian/Rankin source; these were fixed and covered by a regression test. The repeated full check returned **zero mismatches**. The check establishes text availability, not claim truth, rights clearance, ranking quality or exact paragraph anchors.

After the fix the canonical export data version is `bfcdc47dc608a088653643f18b5f4774f5b12f857efc9bcb0095954a6fb705da` with the inspected registry. Repeating the unchanged pre-fix export had already produced the identical version; the corrected version is separately reproducible from the retained private registry. Registry history is part of durable state and must be retained when reproducing existing IDs.

Reproduce with a running local website and its exact source snapshot:

```sh
python tools/search/check_render.py --export PATH_TO_PRIVATE_EXPORT_JSON --base-url http://127.0.0.1:18089
```

## Tests

Ten original tests passed, including three tests on the dedicated real local PostgreSQL/ParadeDB cluster. Database tests used unique `test_*` build IDs, mock embedding vectors, and removed only their own rows. They verified:

- repeated import performs no further embeddings;
- editing one passage embeds only that changed input;
- deleting a passage changes new-build membership while old ready builds remain intact;
- the complete JSONB entity preserves competing date assertions;
- interruption after an embedding batch reuses persisted artifacts on resume;
- a failure inside the final transaction leaves no partial passage rows and does not replace the previous manifest;
- re-running that failed build reuses its successfully cached embeddings;
- registry moves, corrections, deletion/restoration, corrupt artifact rejection, profile separation, bounded chunks and provider response validation;
- provider retries terminate and do not expose HTTP bodies.

The subsequent bounded-worker addition adds two provider/cache tests. The current suite contains **12 tests**: **9 pass without a database**, and the **3 database cases require `SEARCH_TEST_DSN`**. The three database cases passed before the worker addition; no new database writers were started while the coordinator's real import was running. The worker tests prove a 1–4 worker bound, result delivery/persistence on the main thread, error propagation, and reuse of a successful persisted batch after a concurrent batch fails. Schema, profile, text and cache identity are unchanged by concurrency.

```sh
python -m unittest discover -s tools/search/tests -v
# Set SEARCH_TEST_DSN privately to run the three database cases as well.
```

## Worker behavior and remaining operational limits

`--workers 1..4` defaults to 1. At most that many provider futures exist at once; only network calls occur in those threads. Results are validated and written to cache/PostgreSQL by the main thread before replacement work is submitted. On failure pending futures are cancelled; already running bounded requests may finish before shutdown and their unpersisted results may require a new call on resume. This is a bounded exposure, not an exactly-once billing guarantee.

The provider model alias is not an immutable upstream revision. Retain vectors/profile metadata and change the profile if the provider changes the model behavior. The initial search uses exact stored passage text without a generated context prefix; context augmentation is a future controlled profile comparison. Precise original-page anchors are not fabricated: the service/website passage reader displays the exact stored text and its original document link.
