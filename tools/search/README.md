# Local search importer

Python 3.11+; install `requirements.txt` into a private venv. The exporter reads pinned Git snapshots, never changing archive files. Default snapshots are website `ea653b6` and archive `7d353a4`. Pastiche is excluded. Every archive entity is preserved as its complete JSON object, including conflicting statements and references.

```sh
uv venv .dev/runtime/search/venv
uv pip install --python .dev/runtime/search/venv/bin/python -r tools/search/requirements.txt
.dev/runtime/search/venv/bin/python tools/search/ingest.py \
  --website-root "$PWD" --archive-root /Users/stefan/www/jackieleven-archive \
  --state-dir .dev/runtime/search --embed --plan
```

`--plan` writes only a private deterministic export/identity registry and prints counts/cache needs. It does not connect to PostgreSQL or load a provider key. Use `--lexical-only` for an import without embeddings. `JACKIE_SEARCH_DATABASE_URL` supplies the admin DSN; `--database-url` is supported, but environment avoids a credential in process arguments. `--manifest` overrides the default `<state-dir>/manifest.json`.

Real embedding calls require `--embed`; credentials come from `JACKIE_DEEPINFRA_API_KEY`, `JACKIE_DEEPINFRA_API_KEY_FILE`, or `--key-file`. Never commit these values or the runtime directory. This code was developed using mock provider tests only; actual cost-bearing runs are orchestrated separately.

The provider uses the [official DeepInfra Qwen3-Embedding-8B endpoint](https://deepinfra.com/Qwen/Qwen3-Embedding-8B/api), checked 26 October 2026: OpenAI-compatible `/v1/openai/embeddings`, float output. Profile `qwen3-8b-1024-v1` embeds exactly the stored passage text without a generated context prefix. Native 4096-dimensional vectors are truncated to 1024 then L2-normalized, matching the service query profile. The model alias is provider-controlled; cached vectors are durable, and a provider/model change requires a new profile ID. Batches contain at most 16 texts, each at most 2400 characters; timeout 30 seconds, at most two retries after the initial attempt. Only transient statuses retry. No response body, source text, DSN or key is logged.

Private durable state consists of `registry.sqlite3`, content-addressed validated JSON vector files under `artifacts/`, canonical exports under `exports/`, and PostgreSQL `indexer_state.runs/run_items/artifacts`. Retain/back up these with manifests. A file lock and a PostgreSQL advisory lock serialize writers; process death releases both. Retry the same command after an interruption. Valid artifacts are reused regardless of build status. Removing a source creates a new complete build membership while old ready builds remain available for rollback. New snapshots require explicit revision flags; working-copy edits are never silently imported.

Published snapshots are immutable. All passage/entity rows and the ready transition commit together; the manifest is atomically replaced afterward. Failed builds never replace the previous manifest. If a process dies after database commit but before manifest replacement, the next run finds the ready build and writes the manifest without new embeddings. External requests whose responses are lost before cache persistence may be repeated; this does not claim exactly-once billing.

The adapter includes visible source catalog summaries, detail paragraphs, correction notes, deduplicated original quotations, evidence translations and quote captions; entries with `stufe=weitere` do not expose those paragraphs and are excluded. Every allowlisted column is read using the website's special heading/date rules. Column authors other than Jackie Leven are editorial voices. Unknown archive document identities are explicitly `private_search`; they do not create public archive entities. Publication-year filtering does not substitute a capture or concert date. Stored text is readable evidence, and links identify original document pages without fabricated paragraph anchors.

The initial BM25 profile uses the Unicode/default analyzer and title boost 3. Its index SQL is shared with the service; every retrieval must filter by the pinned `build_id`. No approximate vector index is required for this initial exact-search corpus.
