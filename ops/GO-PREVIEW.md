# Separate Go test instance on Hetzner

Target: `https://unpubli.sh/jackieleven/`. This instance replaces neither the PHP site nor the production Jackie Leven virtual host.

## Layout

- Go service: `jackieleven-go-preview.service`, dedicated system user `jackieleven-preview`.
- Backend: only `127.0.0.1:18766`; the `/jackieleven` URL mount is preserved during proxying.
- Releases: `/var/www/jackieleven-go-preview/releases/RELEASE`; the unit uses an immutable absolute release path.
- Private state: `/var/lib/jackieleven-go-preview/contact`.
- nginx: an additional include in the existing `unpublish` HTTPS virtual host, with a dedicated snippet and limit zones.
- Go responses under `/jackieleven/` use `noindex`. The nginx-only `/jackieleven` entry redirect and upstream Cloudflare block pages are exceptions. Canonical, hreflang, JSON-LD and sitemap retain the production identity at `jackieleven.com`. Visible navigation, assets and form redirects stay within the preview path.

The three contact credentials are explicitly empty in the preview unit. This permits interface testing without sending real messages. Actual Turnstile/Resend integration is a separate later step; production secrets are not automatically copied into a test instance.

## Test and install

```sh
go test -race ./...
go vet ./...
node werkzeug/browserablaeufe.cjs
python3 -B ops/test_go_preview.py
python3 ops/prepare-go-release.py NEW_RELEASE_DIRECTORY --goos linux --goarch amd64
```

Transfer `install-go-preview.py` together with `jackieleven-preview.service`, `nginx-preview-location.conf` and `nginx-preview-limits.conf` to the server. Upload the release to a new release directory first. Run the installer as root with `--release RELEASE --expected-vhost-sha SHA256`.

Before changing anything, it verifies all release checksums and the expected checksum of the existing virtual-host file, preventing overwrites of intervening edits. It backs up existing configuration to `/var/backups/jackieleven-go-preview/`, validates the new unit with `systemd-analyze verify` and nginx with `nginx -t`, starts only the preview service, then checks the backend followed by local HTTPS. Failures restore the backed-up files and previous service state. Such a failure was simulated and recovery verified before use.

After installation, check public HTTPS requests, reference homepages, server status and the unchanged PHP virtual-host checksum. The preview port must not bind to a public interface.

## Subpath parity

The frozen PHP page contract remains authoritative. The prefix checker may normalise only visible internal mount URLs; production canonical/JSON-LD URLs remain untouched. Cookie path and noindex are checked separately. Two deliberately modified assets require dedicated evidence: `home.css` uses stylesheet-relative font URLs, and `zeitgraph.js` separates visible navigation URLs from SEO URLs when mounted. These files are no longer byte-identical to the frozen PHP version. Exact differences are reported; default operation is still checked for identical behaviour.

## Removal

Before removal, compare the saved virtual-host file with the current version to preserve later changes by other applications. Remove only the `snippets/jackieleven-preview.conf` include or carefully restore its backup, run `nginx -t` and reload nginx. Then stop and disable only `jackieleven-go-preview.service`. PHP and the main site remain available. Retain release and backup directories for a later restart.

## Live acceptance, 25 October 2026

The separate instance is installed and reachable at <https://unpubli.sh/jackieleven/>.

- Runtime release: `d94e88c98a8143fbefe03d6c18049fc992c43b61`, Linux/amd64, clean build; all 240 manifest files checked on Hetzner.
- Installer: commit `36c6b09`; service active and enabled, bound only to `127.0.0.1:18766`.
- Configuration backup: `/var/backups/jackieleven-go-preview/20261025T182756.480327Z`.
- Independent local comparison: 1,613/1,613 page cases each in normal and mounted operation; nine unchanged assets and two precisely verified mount changes.
- Public HTTPS checks passed for language redirects, DE/EN, timeline, discography, CSS, fonts, JavaScript, sitemap, robots and contact GET. Contact cookies have `Secure`, `HttpOnly`, `SameSite=Lax` and `Path=/jackieleven/`. No POST was sent.
- Internal data and unknown paths return 404. `.env` and `.git/config` are blocked upstream with 403.
- Browser checks covered DE/EN switching, dynamic milestone changes, preservation of the mount, and production canonical/hreflang URLs; contact delivery was visibly disabled.
- The unpubli.sh homepage and production PHP homepage remained byte-identical to pre-installation responses. PHP virtual host unchanged: SHA-256 `f5e6560f894ae4c840e8a0af22e53f474ce2d85d9a3d6ac70bdb8ed99e6ccbdb`.
- `nginx -t` passed. Existing warnings about duplicate TLS protocol options were left unchanged.

The first installation attempt rolled back correctly: the HTTPS check immediately after `systemctl reload` hit an old nginx worker and returned 404. The installer now waits for the new configuration with bounded retries; both transition and permanent failure are tested. Backend and HTTPS checks passed on the second attempt.

Reports and the screenshot are stored locally under `.dev/migration-state/` (ignored). At this acceptance stage, the PHP app and `main` remained the production state. The preview contact form still sends no email.

## Update to the cleaned branch state

On 25 October 2026, the test instance was updated to release `ba3224f4314b0eef687e17adf3260cf9c4e592d7`. The clean Linux/amd64 package is at `/var/www/jackieleven-go-preview/releases/ba3224f`; the active systemd unit points to exactly that release. All 240 manifest files were verified on the server. The service is active and enabled, with the backend bound only to `127.0.0.1:18766`.

Pre-switch backup: `/var/backups/jackieleven-go-preview/20261025T184735.773481Z`. The previous release `d94e88c` remains available for rollback. The nginx virtual hosts for unpubli.sh and the main domain remained byte-identical during this update.

Public HTTPS checks passed: entry/language redirects, DE/EN, timeline, discography, CSS/JavaScript/fonts, sitemap, robots, contact GET and private-path restrictions. Cookie path and security flags are correct; the preview remains noindex with email delivery disabled. Both existing homepages remained byte-identical to reference responses. No message was sent. Report: `.dev/migration-state/live-ba3224f.json` (local, ignored).
