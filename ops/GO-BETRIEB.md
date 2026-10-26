# Go operations and version switching

The main domain has run on Go since 25 October 2026. The separate test instance remains available (see `GO-PREVIEW.md`). This guide describes operations and rollback; it performs no server changes. The existing PHP configuration and `site-current` remain available as a fallback. Before a switch, the Go migration must pass the full HTTP, browser, contact and review comparisons.

## Local operation

A persistent Go service is configured on this MacBook: `https://jackieleven.localhost` reaches the local Go process through MAMP. Startup, builds and restarts are documented in [GO-LOKAL.md](GO-LOKAL.md). Port 8080 belongs to the LaunchAgent; use 8081 for an additional manual test server.

In the main directory `/Users/stefan/www/jackieleven`, on branch `main`:

```sh
go test ./...
go test -race ./...
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8081
```

Go is available locally at `http://jackieleven.localhost:8080` or `http://127.0.0.1:8080`. Go replaced the former local PHP application; PHP remains in the `php-before-go-migration` tag and as a server fallback. Local contact checks use no production delivery credentials. The public Turnstile sitekey affects the visible form output; both comparison instances need the same public configuration.

## Release package

```sh
python3 ops/prepare-go-release.py /tmp/jackieleven-go-release
# Verify the Linux target architecture on the server before deployment:
python3 ops/prepare-go-release.py /tmp/jackieleven-go-linux --goos linux --goarch amd64
```

`ops/go-release-files.json` is the explicit file selection. Add new published content or templates there. The tool builds the binary, preserves asset timestamps and writes SHA-256 checksums plus revision/dirty status. Runtime contents comprise the binary, JSON data, Go templates, selected Markdown texts and assets. Source code, PHP, research drafts and secrets are not packaged.

Before approval, start the package itself and check it against the same PHP snapshot. Passing source-tree tests alone is insufficient.

## Initial server installation — after acceptance

Prerequisites: existing `jackieleven` user, nginx, TLS certificates and the existing site-specific Cloudflare origin, real-IP and rate-limit configuration. Check the actual Linux architecture before building. Only the Jackie Leven site is switched.

1. Transfer the release to a new immutable directory `/var/www/jackieleven/go-releases/RELEASE`; run `sha256sum --check release-manifest.sha256` there. Make directories and files readable but not writable by `jackieleven`. Put no secrets in the release.
2. Install `run-go-release.sh` as `/usr/local/libexec/jackieleven-go-start`; copy `jackieleven-go.service` to `/etc/systemd/system/`. The starter resolves `go-current` exactly once, so templates, texts and assets come from the same version.
3. Create `/etc/jackieleven/go.env` as root with mode 0600. Required values: `JACKIE_RESEND_API_KEY`, `JACKIE_TURNSTILE_SITEKEY`, `JACKIE_TURNSTILE_SECRET`. Never put values in command arguments, logs or Git. `StateDirectory=jackieleven-go` keeps contact state private and persistent across restarts. PHP session files remain separate.
4. Point `go-current` to the new release. Validate the unit with `systemd-analyze verify`, then run `systemctl daemon-reload` and `systemctl start jackieleven-go`. Initially test only through `127.0.0.1:18765`, including de/en, error pages, sitemap, assets and contact GET. Do not send test email through real credentials.
5. Back up the current nginx site configuration outside the active include directory. Install `nginx-go-proxy.conf` as `/etc/nginx/jackieleven-go-proxy.conf`. Replace the existing site configuration with `nginx-go-site.conf` only after approval. Run `nginx -t` before reloading, then perform a controlled reload and local/external HTTP checks. The origin gate, security headers and limits remain active.
6. Enable the service persistently only after successful checks. Retain PHP-FPM configuration and the PHP release during the observation period.

Forwarded client IP and HTTPS information are trusted only with `-trust-proxy` deliberately enabled and a local TCP peer. nginx overwrites these headers; the Go port must not be publicly reachable.

## Subsequent Go releases

Transfer and check a new version in a new directory first. Record the previous `go-current` target, atomically replace the link and restart Go. A restart may briefly interrupt requests; this simple operating model does not promise zero-downtime deployment. The old process uses its resolved release path until it exits. Graceful shutdown must finish active requests before process exit.

If startup or smoke tests fail, restore the previous link target and restart. Do not remove release directories still needed for rollback or running processes.

## PHP rollback

Restore the saved PHP nginx configuration, run `nginx -t` and reload nginx. The unchanged PHP application under `site-current` resumes service. Stop Go only afterwards. Every rollback test must also check HTTPS, language switching and contact GET.

## Evidence required before production approval

Validate templates on the actual Linux system with `systemd-analyze verify` and `nginx -t`. Linux startup, graceful shutdown, network/proxy trust boundaries, state permissions, restart and rollback require separate operational acceptance. Successful local macOS migration does not replace those checks.

## State cleanup

`ops/clean-state.py --state-dir /var/lib/jackieleven-go/contact` removes only 48-character hexadecimal session files under `sessions/` and 64-character hexadecimal counter files directly in the state directory, both ending in `.json`. Retention is two days, matching the Go runtime. Active locks, symlinks and unrelated filenames are preserved. Missing directories are allowed on first startup. `jackieleven-clean-state.service` and `.timer` are templates for this; they do not replace existing cleanup without separate installation. The preview has its own state under `/var/lib/jackieleven-go-preview/contact`.

## Production cutover on 25 October 2026

`https://jackieleven.com` runs on the verified runtime release `ba3224f4314b0eef687e17adf3260cf9c4e592d7`. The active `jackieleven-go.service` is enabled and binds only to `127.0.0.1:18765`. `go-current` points to `/var/www/jackieleven/go-releases/ba3224f`. The process uses the resolved release path; all 240 package files were checked before installation.

Installer: commit `e1d159a`, `ops/install-go-production.py`; twelve offline tests and independent review passed. The installer is designed for the one-time cutover and rejects existing Go production artifacts. Its four template files must reside in the same directory. Further releases use the version-switch procedure above.

The three existing provider credentials were transferred exclusively on the server from the existing pool. `/etc/jackieleven/go.env` is root-owned with mode 0600. The running Go process loaded exactly the same values; no credential values were printed or versioned.

Public acceptance passed: DE/EN, content pages, SEO, 1,370 sitemap targets, indexing restrictions for pastiche/fragments, 17 referenced assets, HTTPS/www redirects, private paths, cookie attributes and Cache-Control. Direct origin access remains blocked even with forged proxy headers. Negative Turnstile tests in both languages reject missing/invalid proofs while preserving text.

Exactly one explicitly authorised test message was sent through the regular browser form. Turnstile was accepted, Resend confirmed acceptance, and the page showed success. The user confirmed receipt on 25 October 2026. The complete form path, including delivery, is therefore accepted. Evidence image: `.dev/migration-state/production-form-success.png` (local, ignored).

### Retained fallback

PHP-FPM, socket `/run/php/jackieleven.sock`, pool configuration, security rules and the `site-current` link remained unchanged. The PHP release is still `/var/www/jackieleven/site-releases/20261024110408-7001`.

Backup: `/var/backups/jackieleven-go-production/20261025T190144-6uclpdnf`. If needed, run this command as root on Hetzner:

```sh
python3 /var/backups/jackieleven-go-production/20261025T190144-6uclpdnf/installer.py --rollback /var/backups/jackieleven-go-production/20261025T190144-6uclpdnf
```

Rollback checks that no unrelated virtual-host changes are overwritten, restores PHP configuration, and waits for old nginx workers to exit after reload before stopping Go. If reload or draining fails, Go and its startup files remain available. The now-working main domain was not actually switched back. The separate preview remained byte-identical.
