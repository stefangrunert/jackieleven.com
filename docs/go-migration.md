# Go-Migration: Stand und Wiederaufnahme

Stand: 25. Oktober 2026. Arbeitsverzeichnis: `/Users/stefan/www/jackieleven-go-migration`, Branch `go-migration`. PHP-Referenz: `/Users/stefan/www/jackieleven`, erreichbar unter `https://jackieleven.localhost`.

Die serverseitige Go-Umsetzung ist fertig. PHP/main wurden dabei nicht geändert. Der PHP-Ausgangsstand ist Commit `869442365d26a697f4f630b03ac073d4899055d6`, auf origin/main und im annotierten Tag `php-before-go-migration` gesichert. Der Archiv-/Ontologie-Agent arbeitet in einem anderen Repository; neue Ontologie- und Suchfunktionen sind nicht Teil dieses Laufzeitwechsels.

## Abnahme und Nachweise

| Prüfung | Ergebnis |
|---|---|
| Vollständiger HTTP-Abgleich einschließlich Sprachen, Aliasse, Filter, Fragmente, Metadaten und Fehlerfälle | 1.613 Fälle, keine ungeklärte Abweichung |
| Referenzierte CSS-/JavaScriptdateien | 11 von 11 mit identischem Inhalt und passendem HTTP-Vertrag |
| Derselbe Vollabgleich gegen das isolierte Releasepaket | 1.613 Fälle und 11 Assets bestanden |
| Desktop 1440×1000 und Mobil 390×844 | Neun Seitentypen je Größe: DOM-Geometrie identisch, alle 18 Screenshots pixelgleich |
| Dynamische Zeitreise | Stationswechsel, Titel/Canonical, Sprachlink und Browser-Zurück geprüft |
| Diskografieinteraktion | Kombinierte Filter, fünf Doll-by-Doll-Alben, Detailnavigation und erhaltener Filterkontext bei Zurück geprüft |
| Markdown-/Lesefassungen | 73 Kolumnenmodelle/HTML, beide Kapitelsprachen und 202 Markdownfälle exakt wie PHP |
| Go-Tests und statische Analyse | `go test -race ./...` und `go vet ./...` bestanden |
| Isolierter Kontakt-HTTP-Abgleich | 15 von 15 Fällen identisch: DE/EN, Cookieflags, CSRF, Honeypot/Arrays, Ablauf, Fehlertext, Escaping, Header und Tokenretention |
| E-Mailvalidierung | 612 aus PHP abgeleitete Fälle Bestandteil der normalen Testsuite |
| Unabhängiger Review | Alle reproduzierten Befunde behoben; keine bekannten offenen P1/P2-Befunde im geprüften Umfang |
| Releasegrenzen | Explizite Allowlist, Traversal-/Symlink-/Überschreibschutz getestet; SHA-256-Manifeste gültig, kein PHP und keine lokalen Zugangskonfigurationen im Paket |
| Plattformbuild | macOS/arm64 und Linux/amd64 erfolgreich gebaut; Linuxbetrieb noch nicht ausgeführt |

Ein Kontakt-HTTP-Vergleich mit leeren Zugangsschlüsseln ergänzt die Paket- und Mocktests. Sein Ergebnis steht im zugehörigen lokalen Bericht und in `werkzeug/parity.md`. Es wurden keine echten Nachrichten versandt.

Das Ziel ist gleiche Inhalte, Darstellung und Verhalten. Die Nachweise belegen den beschriebenen Prüfumfang. Zufällige CSRF-Werte, Asset-Zeitstempel und semantisch gleichwertige Serialisierung werden ausdrücklich normalisiert. Inline-Leerzeichen und geschützte Leerzeichen bleiben erhalten. JSON-Attribute werden nur dort strukturiert verglichen, wo JavaScript sie tatsächlich als JSON konsumiert.

Ein Infrastrukturfall wird gesondert ausgewiesen: `/de%2Fueber` liefert bei Apache und Go 404 ohne Datenpreisgabe. Apache erzeugt diese Antwort vor dem PHP-Programm. Sein HTML-Fehlertext wird nicht als gleiche App-Ausgabe ausgegeben und nicht zur behaupteten Bodyparität umetikettiert.

## Start und Prüfkommandos

```sh
cd /Users/stefan/www/jackieleven-go-migration
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8080
```

Danach ist Go unter `http://127.0.0.1:8080/de/` erreichbar. Keine produktiven Schlüssel zum Vergleichen laden.

```sh
go test -race ./...
go vet ./...
python3 -B werkzeug/test_parity.py
python3 -B ops/test_go_release.py
node werkzeug/browserablaeufe.cjs
python3 werkzeug/parity.py --baseline .dev/migration-state/php-baseline-v2 \
  --candidate http://127.0.0.1:8080 --assets --report /tmp/jackie-go-parity.json
```

Der eingefrorene Snapshot liegt zusätzlich unter `/tmp/jackie-php-baseline-v2`; maßgeblich für Wiederaufnahme ist die dauerhafte lokale Kopie `.dev/migration-state/php-baseline-v2`. v1 bleibt separat erhalten. Screenshots, Layout-/Pixelresultate, Prüfberichte und Agenten-Checkpoints liegen unter `.dev/migration-state/`. Diese lokalen Arbeitsartefakte sind bewusst nicht in Git; der Prüfer und seine Normalisierungsregressionen sind versioniert.

Der direkte Leser-Differentialtest lässt sich zusätzlich mit `JACKIE_PHP_READERS_FIXTURE="$PWD/.dev/migration-state/readers-expected.json"` und `JACKIE_CONTENT_ROOT="$PWD"` vor `go test ./internal/site` ausführen.

## Pause und Fortsetzung

„Pause“ hält laufende Agentenarbeit an. Vor der Fortsetzung zuerst Gitstatus und diesen Stand lesen; nicht fremde Änderungen zurücksetzen. Die Arbeit hängt nicht vom Kontext eines bestimmten Agenten oder einem laufenden Browser ab. Nach einem Neustart können die Server mit den dokumentierten Befehlen gestartet werden. Es gibt keine automatische Fortsetzung und keinen automatischen Produktionswechsel.

Entwicklung und Review waren getrennt. Der spätere vollständige Abgleich lief ausdrücklich auf dem günstigeren Modell GPT-5.6 mit hohem Reasoning-Aufwand. Root übernahm Integration, Leseregeln, Releasepaket und Browserprüfungen.

## Vor dem Produktionswechsel

Die lokale Migration ist von der Betriebsfreigabe getrennt. Der nächste Schritt ist die Prüfung der Linuxvorlagen am tatsächlichen Zielsystem: `nginx -t`, `systemd-analyze verify`, realer Start, Proxy-/Dateirechteprüfung und kontrollierter Rückfall. Echte Turnstile-/Resend-Konfiguration und Zustellung wurden nicht getestet. Kein Produktionsdienst, kein Webserver-VHost und kein Hauptbranch wurden umgestellt.

Nach Abnahme kann `main` auf den geprüften Migrationsstand vorgezogen werden. Der Sicherungstag und PHP-Worktree bleiben als Rückfall erhalten. Details stehen in `ops/GO-BETRIEB.md`, die Architektur in `docs/go-architecture.md` und der unabhängige Review in `docs/go-review.md`.
