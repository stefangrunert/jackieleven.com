# Independent review of the Go migration

As of 25 October 2026. PHP reference: commit `869442365d26a697f4f630b03ac073d4899055d6`, backup tag `php-before-go-migration`. The local Go worktree was reviewed after the corrections described below. The independent reviewer implemented no runtime or operations files. Only additional regression tests and this report were added after the initial review.

## Result and scope

The independently reproduced security and correctness findings have been fixed and retested. No known P1/P2 findings remain open in the areas examined. This describes the scope of this review, not a formal proof of universal parity for every possible HTTP input.

The review covers HTTP routes and path boundaries, language-dependent rendering and escaping, the Markdown/column reader, contact forms, persistent state and concurrency, proxy trust, the SEO origin, release packaging and operations templates. The full page comparison and browser checks are separate evidence from the migration process.

## Findings and corrections

| Finding | Effect | Correction and evidence |
|---|---|---|
| P1: `main` did not wait for `Shutdown` to finish. | SIGTERM could abort active requests despite the intended grace period. | The process now waits for `shutdownDone`. Independently tested with a real local process: incomplete contact POST, SIGTERM, process remains active, remaining body sent, complete 400 response, then exit 0. |
| P2: `net/mail` did not match PHP `FILTER_VALIDATE_EMAIL`. | Some previously valid addresses were rejected and some previously invalid ones accepted. | Explicit rules for ASCII, local parts, DNS names and IP literals. An independently generated PHP corpus of 612 combinations matches completely and is retained as `internal/site/testdata/email-validation.json`. |
| P2: Non-empty honeypot arrays were discarded. | `website[]=bot` continued processing instead of returning 429 early as in PHP. | Dedicated validation preserves PHP emptiness and overwrite rules. Both the original defect and the corrected 429 response were independently reproduced. |
| Query values were initially read with `url.Values.Get`. | Duplicate parameters used the first value rather than the last; array overwrites differed. | Central scalar PHP query evaluation, with regressions for last scalar values and array overwrites. |
| Further contact differences in trimming, body limits, JSON responses and form encoding. | Inputs were handled differently, or only partially valid upstream responses were accepted. | PHP trim character set, 128 KiB limit, fully validated bounded JSON responses, media-type-dependent form parsing including multipart, and PHP-compatible handling of the name `"0"`. |

## Independent evidence

- Two concurrent contact POSTs with the same session and token trigger exactly one delivery call. A subsequent retry after uncertain delivery uses the same persistent idempotency key, even with a new contact object.
- Twenty concurrent requests to the same IP limiter allow exactly five attempts. Forwarded client IP and HTTPS information are used only with the proxy option enabled and a local TCP peer.
- Twenty-four concurrent German and English page responses remained language-isolated. The tested execution paths passed the Go race detector without findings.
- Confidential or internal paths in `.git`, `.dev`, `app`, `data`, `templates`, `research` and `autobiografie` are not served directly. Asset traversal and directory listing are blocked.
- Attack-like name and message inputs remain present on the contact error page but are escaped as text. The regression explicitly checks that the escaped values are present; simply omitting the form fields would not pass.
- Persistent contact state contains no name, email address, message, Turnstile token, plaintext client IP or credentials. State files use 0600 and session directories created by the contact module use 0700. Permissions on an operator-supplied root directory are operator configuration; the systemd template sets it to 0700.
- Direct PHP differential tests of the reading rules passed: 73 column models and their HTML, chapter sections in both languages, and 202 Markdown/inline cases. The deliberately limited reading rules were preserved.
- The release selection contains exactly the same 186 asset/Markdown files as the generated PHP reference release. Package-boundary tests for traversal, symlinks and existing target directories passed.
- Operations templates overwrite the relevant forwarding headers, bind the backend to loopback, preserve the origin gate and limits, and use the release path resolved once. Rollback to the retained PHP release is documented.

Independent scenarios not already covered elsewhere remain in `internal/site/independent_review_test.go`: additional private resources, reflected contact XSS input, and privacy/file-permission checks for persistent contact state. Existing concurrency, idempotency, proxy and language tests were not duplicated.

Reproducible standard checks:

```sh
go test -race ./...
go vet ./...
PYTHONDONTWRITEBYTECODE=1 python3 ops/test_go_release.py
```

The additional direct PHP reader comparison takes the generated fixture path through `JACKIE_READING_FIXTURE` and the content tree through `JACKIE_CONTENT_ROOT`; the email corpus above is a permanent part of the standard test suite.

## Limits before production approval

Turnstile and Resend were tested with controlled transports or injected responses. No real message was sent and no live contact submission was tested. Actual service configuration and successful delivery are therefore not established by these checks.

Local testing does not replace `nginx -t`, `systemd-analyze verify`, or a startup/rollback test on the actual Linux server. Permissions, the real proxy chain, network reachability and restart behaviour must be confirmed there before approval. Go operations are prepared, but this review performed no live deployment.

Final approval must consider the full HTTP/content comparison, browser checks and the actual built release package. This independent review makes no unchecked blanket claim of 100% parity.

## Addendum: live preview under `/jackieleven`

The optional deployment at `https://unpubli.sh/jackieleven` was independently reviewed for base-path handling and operational readiness. No new concrete defects were found in the reviewed state. The public canonical origin remains `https://jackieleven.com`; the preview receives `noindex` even if a production Host header is accidentally forwarded.

An isolated independent suite under the race detector confirmed mount boundaries, similar and duplicate prefixes, traversal protection and redirects. Navigation, form actions, fragment assets and a fully mocked successful contact redirect remain under `/jackieleven`. Canonical, hreflang, sitemap and fragment Link headers exclude the preview prefix. The session cookie has `Path=/jackieleven/`, Secure, HttpOnly and SameSite=Lax. All four font files resolve through relative CSS URLs within the mount.

The changed JavaScript function `seitenangaben()` was also executed in isolation for both standard and preview operation. Visible language links and history URLs remain in the active instance; hreflang, canonical and JSON-LD retain the public address. The template supplies separate navigation and canonical data for this purpose.

Preview operations files were inspected: dedicated user and state, port 18766 bound only to loopback, explicitly empty contact credentials, overwritten proxy headers and dedicated nginx limits. The installer bounds its change to the existing HTTPS virtual host using an expected SHA-256 value and an unambiguous insertion point; it backs up existing content and file modes first. An independent rerun of `ops/test_go_preview.py` passed: a simulated service-start failure restores the original configuration bytes and modes and removes newly created snippets. This workflow does not switch the PHP site.

Actual installation, `nginx -t`, systemd validation and live HTTP/browser checks are subsequently performed by the coordinating agent. This section certifies the preceding code and simulation tests, not completed live acceptance. The reviewer performed no deployment action.
