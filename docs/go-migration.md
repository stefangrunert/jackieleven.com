# Go-Migration: Stand und Wiederaufnahme

Stand: 26. Oktober 2026. Arbeitsverzeichnis: `/Users/stefan/www/jackieleven`, Branch `main`. Die Go-Migration ist vollständig integriert; der separate Migrationsworktree und der Branch `go-migration` wurden lokal und auf origin entfernt.

Die serverseitige Go-Umsetzung ist fertig und auf `main` veröffentlicht. Der PHP-Ausgangsstand ist Commit `869442365d26a697f4f630b03ac073d4899055d6`, im annotierten Tag `php-before-go-migration` gesichert. Der Archiv-/Ontologie-Agent arbeitet in einem anderen Repository; neue Ontologie- und Suchfunktionen sind nicht Teil dieses Laufzeitwechsels.

## Abnahme und Nachweise

| Prüfung | Ergebnis |
|---|---|
| Vollständiger HTTP-Abgleich einschließlich Sprachen, Aliasse, Filter, Fragmente, Metadaten und Fehlerfälle | 1.613 Fälle, keine ungeklärte Abweichung |
| Referenzierte CSS-/JavaScriptdateien | 9 von 11 byteidentisch; `home.css` und `zeitgraph.js` weichen ausschließlich in den separat hashdokumentierten, streng geprüften Mount-Transformationen ab |
| Separater `/jackieleven`-Mount | 1.613 von 1.613 Seitenverträgen und 11 von 11 Assets ohne ungeklärte Abweichung; 600 Canonical-Alternativen, Noindex und Kontakt-Cookiepfad geprüft |
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
| Plattformbuild | macOS/arm64 und Linux/amd64 erfolgreich gebaut; separate Linux-Testinstanz auf Hetzner in Betrieb |

Ein Kontakt-HTTP-Vergleich mit leeren Zugangsschlüsseln ergänzt die Paket- und Mocktests. Sein Ergebnis steht im zugehörigen lokalen Bericht und in `werkzeug/parity.md`. Es wurden keine echten Nachrichten versandt.

Das Ziel ist gleiche Inhalte, Darstellung und Verhalten. Die Nachweise belegen den beschriebenen Prüfumfang. Zufällige CSRF-Werte, Asset-Zeitstempel und semantisch gleichwertige Serialisierung werden ausdrücklich normalisiert. Inline-Leerzeichen und geschützte Leerzeichen bleiben erhalten. JSON-Attribute werden nur dort strukturiert verglichen, wo JavaScript sie tatsächlich als JSON konsumiert.

Der optionale Vorschau-Mount wurde zusätzlich gegen denselben unveränderten
PHP-v2-Snapshot geprüft. Sein Bericht liegt unter
`.dev/migration-state/jackie-prefix-parity-full.json`; die genaue
Normalisierungspolitik und beide Asset-Hashes stehen in `werkzeug/parity.md`.
Canonical, hreflang, Sitemap und JSON-LD bleiben Production-Werte und werden im
Prefix-Abgleich nicht umgeschrieben. Der Prüflauf sendete keine POST-Anfrage.

Ein Infrastrukturfall wird gesondert ausgewiesen: `/de%2Fueber` liefert bei Apache und Go 404 ohne Datenpreisgabe. Apache erzeugt diese Antwort vor dem PHP-Programm. Sein HTML-Fehlertext wird nicht als gleiche App-Ausgabe ausgegeben und nicht zur behaupteten Bodyparität umetikettiert.

## Start und Prüfkommandos

```sh
cd /Users/stefan/www/jackieleven
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
  --candidate http://127.0.0.1:8080 --report /tmp/jackie-go-parity.json
```

Der normale Seitenvergleich oben verwendet keine pauschale Bytegleichheit für Assets: Die zwei dokumentierten Mount-Anpassungen werden mit `werkzeug/prefix_parity.py` streng geprüft; Aufruf und Normalisierungsregeln stehen in `werkzeug/parity.md`.

Der eingefrorene Snapshot liegt zusätzlich unter `/tmp/jackie-php-baseline-v2`; maßgeblich für Wiederaufnahme ist die dauerhafte lokale Kopie `.dev/migration-state/php-baseline-v2`. v1 bleibt separat erhalten. Screenshots, Layout-/Pixelresultate, Prüfberichte und Agenten-Checkpoints liegen unter `.dev/migration-state/`. Diese lokalen Arbeitsartefakte sind bewusst nicht in Git; der Prüfer und seine Normalisierungsregressionen sind versioniert.

Der direkte Leser-Differentialtest lässt sich zusätzlich mit `JACKIE_READING_FIXTURE="$PWD/.dev/migration-state/readers-expected.json"` und `JACKIE_CONTENT_ROOT="$PWD"` vor `go test ./internal/site` ausführen.

## Pause und Fortsetzung

„Pause“ hält laufende Agentenarbeit an. Vor der Fortsetzung zuerst Gitstatus und diesen Stand lesen; nicht fremde Änderungen zurücksetzen. Die Arbeit hängt nicht vom Kontext eines bestimmten Agenten oder einem laufenden Browser ab. Nach einem Neustart können die Server mit den dokumentierten Befehlen gestartet werden. Es gibt keine automatische Fortsetzung und keinen automatischen Produktionswechsel.

Entwicklung und Review waren getrennt. Der spätere vollständige Abgleich lief ausdrücklich auf dem günstigeren Modell GPT-5.6 mit hohem Reasoning-Aufwand. Root übernahm Integration, Leseregeln, Releasepaket und Browserprüfungen.

## Produktionsstand

Seit dem 25. Oktober 2026 bedient Go die Hauptdomain `jackieleven.com`, einschließlich
Formular. Runtime-Release `ba3224f`, Installer `e1d159a`. Öffentliche Seiten-, SEO-,
Asset-, Cookie- und Originprüfungen sowie negative Turnstiletests bestanden. Eine
vom Nutzer autorisierte Nachricht wurde über das echte Browserformular von Resend
angenommen; der Nutzer hat den Eingang im Postfach am 25. Oktober 2026 bestätigt.
Der vollständige Formularweg einschließlich Zustellung ist damit abgenommen.

PHP-FPM, bisheriges Release und Sicherung bleiben als Rückfall erhalten.
Rückfallkommando und Deploymentnachweise stehen in `ops/GO-BETRIEB.md`.
Die separate Testinstanz bleibt verfügbar. Der abgenommene Entwicklungsstand ist
in `main` integriert und auf origin veröffentlicht.

## Bereinigung des Migrationsbranches

Nach Einrichtung der Testinstanz wurden auf Wunsch des Nutzers die alte Anwendung
(`app/`, `index.php`, `.htaccess`), die doppelten JSON-Kataloge und die zugehörigen
Release-/FastCGI-/Installationswerkzeuge entfernt. Der Betriebsweg dieses Branches
ist ausschließlich Go; Inhaltspflege erfolgt über die Werkzeuge in `werkzeug/`.
Die alten Quellen bleiben über den Sicherungstag wiederherstellbar. Das PHP-Release
auf dem Server bleibt als Rückfall erhalten. Die Git-Historie wird nicht umgeschrieben.

Historische Quellen-URLs mit `.php`, Herkunftsangaben der Vergleichsfixtures,
Migrationsberichte und absichtliche Sperrtests gegen alte private Pfade sind
weiterhin Belege, keine ausführbare Abhängigkeit. Die Go-Leseregel für historische
Monats-URLs bleibt erforderlich, damit die Datierung der veröffentlichten Texte stimmt.

Die Bereinigung wurde zusätzlich geprüft: Alle 238 Laufzeit-Inhaltsdateien bleiben
SHA-256-identisch zum live geprüften Release `d94e88c` (68 Assets, 19 JSON-Daten,
33 Templates, 45 Kapiteldateien, 73 Kolumnen). Der frische Server besteht erneut
1.613/1.613 gemountete Seitenfälle und alle elf Assetverträge, einschließlich
600 Canonical-Alternativen, Noindex und beider Kontakt-Cookiepfade.
Bericht: `.dev/migration-state/jackie-cleanup-prefix-parity.json`.
Go-Race-Suite, Leserreferenztest, `go vet`, JavaScript-Abläufe und Release-/Installertests
bestehen ohne die entfernte Anwendung.

Die bisherigen Pflegefunktionen liegen jetzt in `werkzeug/quellen.py`,
`werkzeug/livevideos.py`, `werkzeug/zitate.py` und `werkzeug/inhalte.py`.
Der Quellen-Generator reproduziert den vorhandenen Katalog exakt (741 öffentlich,
25 intern, keine veralteten Übersetzungen); die zehn Originalzitate sind unverändert.
Werkzeug- und Zustandsbereinigungsregressionen laufen ohne Netzaufrufe. Details und
Abhängigkeiten stehen in `werkzeug/README.md`.

## Abschluss am 26. Oktober 2026

Der vollständig integrierte Branch `go-migration` und sein Worktree wurden entfernt.
Alle 4.278 ignorierten Dateien des Worktrees wurden vorher in
`.dev/worktree-backups/go-migration-2026-10-26.tar.gz` gesichert und anhand von
SHA-256-Prüfsummen verifiziert. Das zugehörige Manifest liegt daneben als
`go-migration-2026-10-26.manifest.json`. Das Archiv enthält auch die bisherigen
lokalen Releasepakete und Laufzeitdaten und bleibt außerhalb von Git.

Die Prüfberichte, Screenshots und eingefrorenen PHP-Referenzdaten stehen zusätzlich
unter `.dev/migration-state/` im Hauptverzeichnis bereit. Der lokale Testserver auf
Port 8080 verwendet jetzt dieses Hauptverzeichnis; produktive Versandzugänge
sind dort nicht geladen. Produktionsinstanz, Vorschau und PHP-Rückfall wurden
bei dieser lokalen Bereinigung nicht verändert.
