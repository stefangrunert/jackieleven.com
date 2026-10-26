# Go migration: status and resuming work

As of 26 October 2026. Working directory: `/Users/stefan/www/jackieleven`, branch `main`. The Go migration is fully integrated; the separate migration worktree and `go-migration` branch were removed locally and on origin.

The server-side Go implementation is complete and published on `main`. The PHP starting point is commit `869442365d26a697f4f630b03ac073d4899055d6`, preserved in the annotated `php-before-go-migration` tag. The archive/ontology agent works in another repository; new ontology and search features are outside this runtime migration.

## Acceptance and evidence

| Check | Result |
|---|---|
| Full HTTP comparison including languages, aliases, filters, fragments, metadata and error cases | 1,613 cases, no unexplained differences |
| Referenced CSS/JavaScript files | 9 of 11 byte-identical; `home.css` and `zeitgraph.js` differ only in separately hash-documented, strictly verified mount transformations |
| Separate `/jackieleven` mount | 1,613 of 1,613 page contracts and 11 of 11 assets without unexplained differences; 600 canonical alternatives, noindex and contact cookie paths checked |
| Same full comparison against the isolated release package | 1,613 cases and 11 assets passed |
| Desktop 1440×1000 and mobile 390×844 | Nine page types per size: identical DOM geometry, all 18 screenshots pixel-identical |
| Dynamic timeline | Milestone changes, title/canonical, language link and browser Back tested |
| Discography interaction | Combined filters, five Doll by Doll albums, detail navigation and preserved filter context on return tested |
| Markdown/reading versions | 73 column models/HTML, both chapter languages and 202 Markdown cases exactly match PHP |
| Go tests and static analysis | `go test -race ./...` and `go vet ./...` passed |
| Isolated contact HTTP comparison | 15 of 15 cases identical: DE/EN, cookie flags, CSRF, honeypot/arrays, expiry, error text, escaping, headers and token retention |
| Email validation | 612 PHP-derived cases included in the standard test suite |
| Independent review | All reproduced findings fixed; no known open P1/P2 findings within the reviewed scope |
| Release boundaries | Explicit allowlist; traversal/symlink/overwrite protection tested; SHA-256 manifests valid; no PHP or local credential configuration in the package |
| Platform build | macOS/arm64 and Linux/amd64 builds successful; separate Linux test instance running on Hetzner |

A contact HTTP comparison with empty credentials supplements package and mock tests. Its result is recorded in the local report and `werkzeug/parity.md`. Those comparison checks sent no real messages.

The objective is equal content, presentation and behaviour. The evidence covers the stated test scope. Random CSRF values, asset timestamps and semantically equivalent serialisation are explicitly normalised. Inline and non-breaking spaces are retained. JSON attributes are compared structurally only where JavaScript actually consumes them as JSON.

The optional preview mount was also checked against the same unchanged PHP v2 snapshot. Its report is `.dev/migration-state/jackie-prefix-parity-full.json`; the exact normalisation policy and both asset hashes are in `werkzeug/parity.md`. Canonical, hreflang, sitemap and JSON-LD remain production values and are not rewritten in the prefix comparison. The run sent no POST requests.

One infrastructure case is reported separately: `/de%2Fueber` returns 404 without data disclosure in both Apache and Go. Apache generates this response before the PHP program. Its HTML error text is not presented as equal application output or relabelled as body parity.

## Startup and verification commands

```sh
cd /Users/stefan/www/jackieleven
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8080
```

Go is then available at `http://127.0.0.1:8080/de/`. Do not load production delivery credentials for comparisons.

```sh
go test -race ./...
go vet ./...
python3 -B werkzeug/test_parity.py
python3 -B ops/test_go_release.py
node werkzeug/browserablaeufe.cjs
python3 werkzeug/parity.py --baseline .dev/migration-state/php-baseline-v2 \
  --candidate http://127.0.0.1:8080 --report /tmp/jackie-go-parity.json
```

The ordinary page comparison above does not assume blanket byte equality for assets: the two documented mount adjustments are strictly checked by `werkzeug/prefix_parity.py`; invocation and normalisation rules are in `werkzeug/parity.md`.

The frozen snapshot is also at `/tmp/jackie-php-baseline-v2`; the durable local copy `.dev/migration-state/php-baseline-v2` is authoritative when resuming work. v1 remains separate. Screenshots, layout/pixel results, reports and agent checkpoints are in `.dev/migration-state/`. These local working artifacts are deliberately not in Git; the checker and its normalisation regressions are versioned.

The direct reader differential test can additionally be run by setting `JACKIE_READING_FIXTURE="$PWD/.dev/migration-state/readers-expected.json"` and `JACKIE_CONTENT_ROOT="$PWD"` before `go test ./internal/site`.

## Pausing and resuming

“Pause” stops ongoing agent work. Before resuming, first read the Git status and this document; do not reset other people's changes. The work does not depend on one agent's context or a running browser. After a restart, servers can be started with the documented commands. There is no automatic resumption or automatic production cutover.

Development and review were separate. The later full comparison explicitly ran on the cheaper GPT-5.6 model with high reasoning effort. Root handled integration, reading rules, release packaging and browser checks.

## Production state

Since 25 October 2026, Go serves the main domain `jackieleven.com`, including the form. Runtime release `ba3224f`, installer `e1d159a`. Public page, SEO, asset, cookie and origin checks and negative Turnstile tests passed. A user-authorised message submitted through the real browser form was accepted by Resend; the user confirmed receipt on 25 October 2026. The full form path, including delivery, is therefore accepted.

PHP-FPM, the previous release and backups remain available for rollback. Rollback instructions and deployment evidence are in `ops/GO-BETRIEB.md`. The separate test instance remains available. The accepted development state is integrated into `main` and published on origin.

## Migration branch cleanup

After the test instance was established, the old application (`app/`, `index.php`, `.htaccess`), duplicate JSON catalogues and associated release/FastCGI/installation tools were removed at the user's request. This branch operates exclusively through Go; content maintenance uses `werkzeug/`. Old sources remain recoverable through the backup tag. The PHP release on the server remains a fallback. Git history is not rewritten.

Historical `.php` source URLs, comparison-fixture provenance, migration reports and intentional blocking tests for old private paths remain evidence, not executable dependencies. The Go reading rule for historical monthly URLs remains necessary to date published texts correctly.

Cleanup was additionally verified: all 238 runtime content files remain SHA-256-identical to live-tested release `d94e88c` (68 assets, 19 JSON files, 33 templates, 45 chapter files, 73 columns). The fresh server again passes 1,613/1,613 mounted page cases and all eleven asset contracts, including 600 canonical alternatives, noindex and both contact cookie paths. Report: `.dev/migration-state/jackie-cleanup-prefix-parity.json`. The Go race suite, reader-reference test, `go vet`, JavaScript workflows and release/installer tests pass without the removed application.

Former maintenance functions now reside in `werkzeug/quellen.py`, `werkzeug/livevideos.py`, `werkzeug/zitate.py` and `werkzeug/inhalte.py`. The source generator reproduces the existing catalogue exactly (741 public, 25 internal, no stale translations); the ten original quotations are unchanged. Tool and state-cleanup regressions run without network access. Details and dependencies are in `werkzeug/README.md`.

## Completion on 26 October 2026

The fully integrated `go-migration` branch and its worktree were removed. Before removal, all 4,278 ignored worktree files were saved in `.dev/worktree-backups/go-migration-2026-10-26.tar.gz` and verified with SHA-256 checksums. The corresponding manifest is alongside it as `go-migration-2026-10-26.manifest.json`. The archive includes previous local release packages and runtime data and stays outside Git.

Reports, screenshots and frozen PHP reference data are also available in `.dev/migration-state/` in the main directory. The local test server on port 8080 now uses that directory, without production delivery credentials. This local cleanup changed neither the production instance, preview nor PHP fallback.
