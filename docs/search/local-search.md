# Operating and developing local archive search

As of 26 October 2026. This document describes the implemented local test version. It is not approval for public operation or evidence of completed quality or end-to-end assessment.

## Open search

The standalone test website is configured at:

- German: <http://127.0.0.1:8082/de/suche-test>
- English: <http://127.0.0.1:8082/en/search-test>

`/de/suche` and `/en/search` show the same form. Pages work without JavaScript. The search service runs separately on `127.0.0.1:8081`; PostgreSQL is reachable only through `127.0.0.1:55473`. All three belong to local development. The test website replaces neither the existing website process on port 8080 nor a published website.

Use port 8082 directly for search tests. The existing Apache/MAMP route is not intended for them: its SSL access logs in particular still need review and adjustment so query strings do not log search text.

## Search modes and filters

| Setting | Effect |
| --- | --- |
| `lexical` | BM25 word search. Useful for names, titles and recognisable wording. Without reranking, no external model call is needed. |
| `semantic` | Similarity search with Qwen embeddings. Useful for paraphrases and questions about content. If semantic search is unavailable, the service can fall back to word search. |
| `hybrid` | Combines word-search and semantic candidates through Reciprocal Rank Fusion. This is the default. |
| Reranking | An optional additional model call that reorders candidates. The “Reranking used” indicator shows whether it actually succeeded. |

Semantic and hybrid requests send search text to DeepInfra. Requested reranking also sends candidate texts. The notice before the form describes this transfer. For tests without external transfer, select `lexical` and leave reranking off. The API key stays with the search service; neither website nor browser needs it.

Text voice filters `text_voice`: `leven`, `third_party`, `editorial` or `pastiche`. Source voice, `source_voice`, is displayed separately. An editorial summary of a concert review can therefore have source voice `third_party` but text voice `editorial`. The current export excludes pastiche, so that filter cannot return results.

Year filters refer to the **document's publication year**, not the date of a concert mentioned in it. Target-page language selects German or English document links; it does not restrict the language of searched texts. Actual text language is shown on each result. A query may contain at most 1024 UTF-8 bytes. The form displays at most 20 results; that number is not a total count of all matching documents.

These examples help compare modes without presupposing particular results or complete answers. German query strings are retained so the documented experiments remain reproducible:

| Query | Experiment |
| --- | --- |
| `Doll by Doll` | Try `lexical`, then `hybrid`; compare titles and passages. |
| `Norwegen` | Compare word search with and without a text-voice filter. |
| `Welche Erinnerungen beschreibt Leven an seine Kindheit?` | Compare `semantic` and `hybrid`, then select text voice `leven`. |
| `Verlust und Trauer` | Compare thematic search with and without reranking. |
| `Fife` | Use `lexical` and narrow publication years; do not interpret the year selection as an event period. |

## Read results

The **mode used**, as shown in the results, is authoritative, not just the form selection. `degraded`, the displayed reason and `reranked` expose fallback operation and skipped reranking. Results also show search duration, service version and the content snapshot's `content_version`.

A result opens the stored passage at `/de/suche/textstelle?id=…` or `/en/search/passage?id=…`. It shows the full stored text, identifiers, voices, text kind and other available metadata. “Open original page” links separately to the document. No paragraph anchors are invented on original pages. The passage belongs to the pinned content snapshot; an original page changed since then need not remain identical.

“No passages found” is a normal result. Errors are displayed separately:

| Status | Meaning |
| --- | --- |
| 400 | Invalid query or filters. |
| 404 | The requested passage does not exist in this snapshot. |
| 409 | Website and search service use different content snapshots. |
| 429 | Bounded search capacity is exhausted. |
| 503 | Search, database or internal connection is unavailable, or the response is unusable. |

Search pages send `Cache-Control: no-store`, `noindex` and `Referrer-Policy: no-referrer`. Go components do not log search text. GET queries nevertheless remain visible in the address bar and may enter browser history. The website's other pages require no connection to the search database.

## Manage local processes

Run commands from the repository root. Prerequisites are Go, Python 3, Docker Desktop using the `desktop-linux` context, and a macOS user session for persistent operation. [ops/search/local.py](../../ops/search/local.py) manages only this local search environment. Its Compose project is `jackieleven-search-dev`, with a dedicated data volume.

For an already imported and published snapshot:

```sh
python3 ops/search/local.py db-up
python3 ops/search/local.py grant-reader
python3 ops/search/local.py install
python3 ops/search/local.py install-test
```

`grant-reader` configures the read-only database role on an existing search schema. `install` builds the search service and starts it as a user LaunchAgent. `install-test` builds and starts the separate website LaunchAgent on port 8082. `launchd` supervises both within the user session. The local launcher enables DeepInfra access for the search service; its key must already be stored securely.

Other commands:

```sh
python3 ops/search/local.py status
python3 ops/search/local.py restart
python3 ops/search/local.py stop-test
python3 ops/search/local.py stop
```

`status` shows the database and search service. `restart` rebuilds and restarts search; use `install-test` again for the test website. `stop-test` and `stop` stop the respective loaded user jobs without deleting database or import state. LaunchAgent files remain installed. Stop the database separately with `db-stop`.

Use <http://127.0.0.1:8081/healthz> and <http://127.0.0.1:8081/readyz> for checks. `healthz` confirms only that the HTTP process is running. `readyz` checks the bound corpus and database, not DeepInfra availability. Only a search request, with inspection of mode and fallback indicators, tests the intended search path.

When starting the website directly as a development process, set `JACKIE_SEARCH_URL=http://127.0.0.1:8081` and `JACKIE_SEARCH_MANIFEST` to the absolute manifest path. Equivalent website flags are `-search-url` and `-search-manifest`; `-base-path` supports a URL prefix. The website accepts only a loopback HTTP origin and follows no redirects. Its HTTP client has an eleven-second overall deadline and bounded response sizes.

## Import state and manifest switching

The initial export reads website revision `ea653b6` and archive revision `7d353a4`. This selection comprises 572 documents, 7993 passages and 965 archive entities. These counts describe that export, not a completely catalogued archive. Working-copy edits do not automatically enter the index.

[tools/search/README.md](../../tools/search/README.md) describes importing and resuming. Before the first import, create the private Python environment with pinned dependencies:

```sh
uv venv .dev/runtime/search/venv
uv pip install --python .dev/runtime/search/venv/bin/python \
  -r tools/search/requirements.txt
```

The local entry point is `index`. It loads private database configuration and passes the protected key-file path to the importer; credentials need not be copied into shell commands. By default, the archive is expected in the neighbouring directory `../jackieleven-archive`.

```sh
python3 ops/search/local.py index --plan
python3 ops/search/local.py db-up
python3 ops/search/local.py index --workers 4
```

`--plan` writes the private export and identity registry, but creates no embeddings and makes no database or provider calls. Without `--plan`, `index` generates embeddings by default, processing up to four batches concurrently. `--workers 1` reduces concurrency. For a snapshot without embeddings:

```sh
python3 ops/search/local.py index --lexical-only
```

Specify new source revisions explicitly, for example first in a planning run:

```sh
python3 ops/search/local.py index --plan \
  --website-revision ea653b6 --archive-revision 7d353a4
```

Replace both revisions with the desired existing Git revisions, then use the same arguments without `--plan` for the import. After the first import, run `grant-reader`, `install` and `install-test` as above. Do not print key files, copy password-bearing DSNs into command arguments, or commit credentials or private runtime state.

Durable private state lives under `.dev/runtime/search/`: notably `registry.sqlite3`, reusable vectors in `artifacts/`, canonical exports in `exports/`, and `manifest.json`. Database tables also retain import progress and published builds. Back up the identity registry, artifacts, retained manifests and database volume together. They are not disposable build files. An interrupted import can be repeated with the same inputs; validated artifacts are reused.

The importer replaces the manifest only after a database build is complete. Website and search service read it **only at startup**, then hold their content snapshot fixed. Restart both after every manifest switch:

```sh
python3 ops/search/local.py install
python3 ops/search/local.py install-test
```

Then check `readyz` and run a search. While only one process has loaded the new snapshot, the website may return 409. To roll back, restore a previously saved manifest as the active manifest and run the same commands. The corresponding earlier database build must still exist; an old manifest alone cannot restore deleted data.

## Limits and further validation

Search retrieves passages from the selected corpus. It does not answer completeness questions such as “all documented concerts in Norway in 2004” or generate an evidence-backed overall narrative. Archive entities remain available as structured data; this does not yet constitute a fully developed search across every assertion and relationship.

Semantic similarity does not establish factual correctness. Useful evaluation needs traceable queries, relevant passages and a separate test set. The examples above are usage examples, not completed evaluation. Latency, fallback frequency and relevance must be measured on the real corpus. Provider calls may incur charges; the local database does not guarantee model availability or latency.

The local launcher enables the read-only MCP endpoint `http://127.0.0.1:8081/mcp` with `search`, `get_passage` and `get_entity`. Snapshot, voice and external-transfer rules apply there too. This does not establish compatibility with a public OpenAI connector. External assistant connections, public reachability, proxy/access logging and public operation require separate approval and checks. `noindex` and loopback addresses do not replace that work. The binding technical interface contract is [implementation-contract.md](implementation-contract.md).

`local.py index` also preserves published manifests under `.dev/runtime/search/manifests/<content_version>.json`. For a local rollback with unchanged website content, copy the desired manifest to `manifest.json`, then run `install` and `install-test`. The old database rows must still exist. If website content changed, its matching revision must also be restored.

Functional and failure checks: `python3 ops/search/check.py` and `python3 ops/search/check-failures.py`. `check.py --external` additionally tests real provider calls. External failure can fail this deliberately strict check while the interface correctly shows fallback mode. Results and domain limits are in the [acceptance report](acceptance.md).
