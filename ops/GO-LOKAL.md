# Go on this MacBook

Since 26 October 2026, `https://jackieleven.localhost/de/` points to the Go application in the main directory `/Users/stefan/www/jackieleven`.

Requests follow Browser → MAMP Apache with the existing local certificate → `127.0.0.1:8080` → Go. MAMP must run for the HTTPS address to work. The Go process is independent of a terminal and starts as a LaunchAgent when Stefan logs in. It restarts automatically after exiting. This user service is unavailable after logout, and the MacBook serves nothing while asleep.

## Everyday use

```sh
cd /Users/stefan/www/jackieleven

# Go code changed: build and restart the service
ops/go-local.sh restart

# Only templates, catalogues or columns changed: reload without building
ops/go-local.sh reload

# Diagnostics
ops/go-local.sh status
ops/go-local.sh logs
curl -I https://jackieleven.localhost/de/

# Stop for this login session, then start again
ops/go-local.sh stop
ops/go-local.sh start
```

`restart` builds a new binary first and replaces it only after a successful build. A compiler error leaves the existing service running. `build` only builds and does not change the running process. There is no automatic file watcher. An additional experimental `go run` server can use port 8081; 8080 belongs to the login service. See also `.dev/go-tutorial.html`.

`stop` unloads the service for the current login session. At the next login, macOS loads the still-installed plist again. To disable it persistently:

```sh
ops/go-local.sh stop
launchctl disable "gui/$(id -u)/com.stefan.jackieleven.go"
```

`ops/go-local.sh start` enables and loads it again.

## Setup and files

`ops/go-local.sh install` builds the program, writes the LaunchAgent plist with the actual local paths, and loads it. It is intended for macOS and requires Go and Python 3. Any unrelated process on port 8080 must first be deliberately stopped or reconfigured.

- Service: `com.stefan.jackieleven.go`
- plist: `~/Library/LaunchAgents/com.stefan.jackieleven.go.plist`
- Binary: `.dev/bin/jackieleven-local`
- Logs: `.dev/logs/go-local.err.log` and `.dev/logs/go-local.out.log`
- Form state: `.dev/runtime/local-contact`
- MAMP include: `ops/apache-go-local.conf`

The LaunchAgent configuration explicitly clears all three delivery/Turnstile provider values. The local contact page can be tested, but real email delivery is disabled. Controlled proxy headers still give HTTPS cookies the correct Secure, HttpOnly and SameSite attributes. The backend binds only to loopback; Apache additionally limits this host to local access.

In MAMP PRO, host **jackieleven**, **Apache** tab, **Additional parameters for <VirtualHost> directive** contains:

```apache
Include "/Users/stefan/www/jackieleven/ops/apache-go-local.conf"
```

This setting survives MAMP configuration generation. The generated `httpd-ssl.conf` is not maintained by hand. Include-file changes require an Apache restart (Apache sidebar → context menu → Restart server). Other hosts and their configuration remain unchanged. Normal MAMP HTTP ports were not changed; the address without an explicit port is the HTTPS address above, not a newly configured HTTP port 80.

## Verification and rollback

Checks covered DE/EN, discography, CSS, contact GET and Secure cookies, plus 404 responses for `.env`, `.dev`, old private PHP configuration and JSON data. The certificate was validated normally, without `curl -k`. Automatic restart after SIGTERM and the build/restart command were exercised. The saved MAMP setting was checked after configuration generation; a full macOS restart was unnecessary and was not performed.

Previous MAMP settings and SSL configurations are stored locally in `.dev/local-service-backup-2026-10-26/` with checksums. To undo only this setup, remove the include line above from the Jackie Leven host, save and restart Apache, then stop/disable the Go service. This restores the previous DocumentRoot mapping, but not deleted PHP source files. PHP sources remain in the Git tag `php-before-go-migration`; the production PHP fallback remains on Hetzner. This local setup changes no remote server.

Background: [Apple: LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html), [Apache: Reverse Proxy](https://httpd.apache.org/docs/2.4/mod/mod_proxy.html), [MAMP: configuration files are regenerated](https://documentation.mamp.info/en/MAMP-PRO-Mac/FAQ/General/Changes-to-the-configuration-files-are-gone-when-I-restart-the-servers/).
