# Go-Betrieb und Versionswechsel

Die Hauptdomain läuft seit dem 25. Oktober 2026 auf Go. Die separate Testinstanz bleibt verfügbar (siehe `GO-PREVIEW.md`). Diese Anleitung beschreibt Betrieb und Rückfall; sie führt selbst keine Serveränderung aus. Die bestehende PHP-Konfiguration und `site-current` bleiben als Rückfall verfügbar. Die Go-Migration muss vor einem Wechsel den vollständigen HTTP-, Browser-, Kontakt- und Review-Abgleich bestehen.

## Lokal

Im Hauptverzeichnis `/Users/stefan/www/jackieleven` auf Branch `main`:

```sh
go test ./...
go test -race ./...
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8080
```

Go ist lokal unter `http://jackieleven.localhost:8080` beziehungsweise `http://127.0.0.1:8080` erreichbar. Die frühere lokale PHP-Anwendung wurde durch den Go-Stand ersetzt; PHP bleibt über den Tag `php-before-go-migration` und als Rückfall auf dem Server erhalten. Lokale Kontaktprüfungen verwenden keine produktiven Versandzugänge. Der öffentliche Turnstile-Sitekey beeinflusst die sichtbare Formularausgabe; beide Vergleichsinstanzen benötigen dafür dieselbe öffentliche Konfiguration.

## Release-Paket

```sh
python3 ops/prepare-go-release.py /tmp/jackieleven-go-release
# Linux-Zielarchitektur vor Auslieferung auf dem Server prüfen:
python3 ops/prepare-go-release.py /tmp/jackieleven-go-linux --goos linux --goarch amd64
```

`ops/go-release-files.json` ist die ausdrückliche Dateiauswahl. Neue veröffentlichte Inhalte oder Templates müssen dort ergänzt werden. Das Werkzeug baut die Binärdatei, bewahrt die Asset-Zeitstempel und schreibt SHA-256-Prüfsummen sowie Revision/Dirty-Status. Runtime: Binärdatei, JSON-Daten, Go-Templates, ausgewählte Markdowntexte und Assets. Weder Quellcode noch PHP, Forschungsentwürfe oder Geheimnisse werden paketiert.

Den Paketinhalt vor der Freigabe selbst starten und gegen denselben PHP-Snapshot prüfen. Ein erfolgreicher Quellbaumtest allein genügt nicht.

## Erstinstallation auf dem Server – erst nach Abnahme

Voraussetzung: bestehender Benutzer `jackieleven`, nginx, TLS-Zertifikate sowie die vorhandenen site-spezifischen Cloudflare-Origin-, Real-IP- und Rate-Limit-Konfigurationen. Die tatsächliche Linux-Architektur ist vor dem Build zu prüfen. Es wird ausschließlich die Jackie-Leven-Site umgestellt.

1. Release in ein neues unveränderliches Verzeichnis `/var/www/jackieleven/go-releases/RELEASE` übertragen; `sha256sum --check release-manifest.sha256` dort prüfen. Verzeichnisse und Dateien für Benutzer `jackieleven` lesbar machen, aber nicht schreibbar. Keine Geheimnisse in das Release schreiben.
2. `run-go-release.sh` als `/usr/local/libexec/jackieleven-go-start` installieren; `jackieleven-go.service` nach `/etc/systemd/system/` kopieren. Der Starter löst `go-current` genau einmal auf. Der Prozess bedient dadurch Templates, Texte und Assets derselben Version.
3. `/etc/jackieleven/go.env` durch root mit Modus 0600 anlegen. Benötigt werden `JACKIE_RESEND_API_KEY`, `JACKIE_TURNSTILE_SITEKEY`, `JACKIE_TURNSTILE_SECRET`. Keine Werte in Befehlsargumenten, Protokollen oder Git ablegen. `StateDirectory=jackieleven-go` hält Kontaktzustand privat und über Neustarts hinweg. Die PHP-Sitzungsdateien bleiben separat.
4. `go-current` auf das neue Release verlinken. Mit `systemd-analyze verify` die Unit prüfen, dann `systemctl daemon-reload` und `systemctl start jackieleven-go`. Zunächst nur auf `127.0.0.1:18765` prüfen, einschließlich de/en, Fehlerseite, Sitemap, Assets und Kontakt-GET. Keine Testmail über echte Zugänge senden.
5. Aktuelle nginx-Sitekonfiguration außerhalb des aktiven Include-Verzeichnisses sichern. `nginx-go-proxy.conf` als `/etc/nginx/jackieleven-go-proxy.conf` installieren. `nginx-go-site.conf` ersetzt erst bei Freigabe die bisherige Sitekonfiguration. Vor Reload `nginx -t`, dann kontrollierter Reload und lokale sowie externe HTTP-Prüfungen. Origin-Gate, Sicherheitsheader und Limits bleiben aktiv.
6. Erst nach erfolgreichen Prüfungen den Dienst dauerhaft aktivieren. Die PHP-FPM-Konfiguration und das PHP-Release während der Beobachtungsphase behalten.

Weitergeleitete Client-IP und HTTPS-Information werden nur bei bewusst aktiviertem `-trust-proxy` und lokalem TCP-Peer vertraut. nginx überschreibt diese Header; der Go-Port darf nicht öffentlich erreichbar sein.

## Weitere Go-Releases

Neue Version zunächst in ein neues Verzeichnis übertragen und prüfen. Vorheriges Ziel von `go-current` festhalten; Link atomar ersetzen und den Go-Dienst neu starten. Ein Neustart kann kurzzeitig Anfragen unterbrechen; dieses einfache Betriebsmodell verspricht kein Zero-Downtime-Deployment. Der alte Prozess verwendet bis zum Ende seinen aufgelösten Releasepfad. Graceful Shutdown muss laufende Anfragen vor Prozessende abarbeiten.

Bei fehlgeschlagenem Start oder Smoke-Test den Link auf die vorherige Version zurücksetzen und erneut starten. Kein Releaseverzeichnis entfernen, solange es für Rückfall oder laufende Prozesse benötigt wird.

## Rückfall auf PHP

Die gesicherte PHP-nginx-Konfiguration wiederherstellen, `nginx -t` ausführen und nginx neu laden. Die unveränderte PHP-Anwendung unter `site-current` übernimmt wieder. Go erst danach stoppen. Bei jeder Rückfallprobe auch HTTPS, Sprachumschaltung und Kontakt-GET prüfen.

## Noch vor Produktionsfreigabe nachzuweisen

Die Vorlagen müssen auf dem tatsächlichen Linux-System mit `systemd-analyze verify` und `nginx -t` geprüft werden. Linux-Start, graceful Shutdown, Netzwerk-/Proxy-Vertrauensgrenze, Zustandsrechte, Wiederanlauf und Rückfall sind eine eigene Betriebsabnahme. Eine erfolgreiche lokale macOS-Migration ersetzt diese Nachweise nicht.

## Zustandsbereinigung

`ops/clean-state.py --state-dir /var/lib/jackieleven-go/contact` entfernt ausschließlich
48-stellige hexadezimale Sitzungsdateien unter `sessions/` und 64-stellige
hexadezimale Zählerdateien direkt im Zustandsverzeichnis, jeweils mit `.json`.
Die Aufbewahrung beträgt wie in der Go-Laufzeit zwei Tage. Aktive Sperren, Symlinks
und fremde Dateinamen bleiben erhalten. Fehlende Verzeichnisse sind beim ersten
Start erlaubt. `jackieleven-clean-state.service` und `.timer` sind dafür die
Vorlagen; sie ersetzen keine laufende Bestandsbereinigung ohne gesonderte Installation.
Die Vorschau verwendet ihren eigenen Zustand unter `/var/lib/jackieleven-go-preview/contact`.

## Produktionswechsel am 25. Oktober 2026

`https://jackieleven.com` läuft auf dem geprüften Runtime-Release
`ba3224f4314b0eef687e17adf3260cf9c4e592d7`. Der aktive Dienst `jackieleven-go.service`
ist aktiviert und bindet ausschließlich `127.0.0.1:18765`. `go-current` zeigt auf
`/var/www/jackieleven/go-releases/ba3224f`. Der Prozess verwendet den aufgelösten
Releasepfad; alle 240 Paketdateien wurden vor der Installation geprüft.

Installer: Commit `e1d159a`, `ops/install-go-production.py`; zwölf Offline-Tests
und unabhängiger Review bestanden. Der Installer ist für die einmalige Umstellung
ausgelegt und lehnt bereits vorhandene Go-Produktionsartefakte ab. Seine vier
Vorlagendateien müssen im selben Verzeichnis liegen. Weitere Releases folgen dem
oben beschriebenen Versionswechsel.

Die drei vorhandenen Anbieterzugänge wurden ausschließlich serverseitig aus dem
bestehenden Pool übernommen. `/etc/jackieleven/go.env` gehört root und hat Modus
0600. Der laufende Go-Prozess hat exakt dieselben Werte geladen; es wurden keine
Schlüsselwerte ausgegeben oder versioniert.

Öffentliche Abnahme bestanden: DE/EN, Inhaltsseiten, SEO, 1.370 Sitemapziele,
Indexierungssperren für Pastiche/Fragmente, 17 referenzierte Assets, HTTPS-/www-
Weiterleitungen, private Pfade, Cookieattribute und Cache-Control. Direkter Origin-
Zugriff bleibt auch mit gefälschten Proxyheadern gesperrt. Negative Turnstiletests
in beiden Sprachen weisen fehlende/ungültige Nachweise ab und erhalten den Text.

Genau eine ausdrücklich autorisierte Testnachricht wurde im Browser durch das
reguläre Formular gesendet. Turnstile wurde akzeptiert, Resend bestätigte die
Annahme und die Seite zeigte die Erfolgsnachricht. Der Nutzer hat den Eingang im Postfach am 25. Oktober 2026 bestätigt.
Damit ist der vollständige Formularweg einschließlich Zustellung abgenommen. Nachweisbild:
`.dev/migration-state/production-form-success.png` (lokal, ignoriert).

### Erhaltener Rückfall

PHP-FPM, Socket `/run/php/jackieleven.sock`, Poolkonfiguration, Sicherheitsregeln
und der Link `site-current` blieben unverändert. Das PHP-Release ist weiterhin
`/var/www/jackieleven/site-releases/20261024110408-7001`.

Sicherung: `/var/backups/jackieleven-go-production/20261025T190144-6uclpdnf`.
Der folgende Befehl wird bei Bedarf als root auf Hetzner ausgeführt:

```sh
python3 /var/backups/jackieleven-go-production/20261025T190144-6uclpdnf/installer.py --rollback /var/backups/jackieleven-go-production/20261025T190144-6uclpdnf
```

Die Rücknahme prüft, dass keine fremde Vhoständerung überschrieben wird, stellt die
PHP-Konfiguration wieder her und wartet nach nginx-Reload auf das Ende der alten
Worker, bevor Go gestoppt wird. Wenn Reload oder Drain scheitert, bleibt Go samt
Startdateien verfügbar. Ein tatsächlicher Rückwechsel der jetzt funktionierenden
Hauptdomain wurde nicht durchgeführt. Die separate Vorschau blieb bytegleich.
