# Go-Migration: Stand und Wiederaufnahme

Stand: 25. Oktober 2026. Arbeitsverzeichnis: `/Users/stefan/www/jackieleven-go-migration`, Branch `go-migration`. PHP-Referenz: `/Users/stefan/www/jackieleven`, erreichbar unter `https://jackieleven.localhost`.

Die serverseitige Go-Umsetzung ist fertig. PHP/main wurden dabei nicht geändert. Der PHP-Ausgangsstand ist Commit `869442365d26a697f4f630b03ac073d4899055d6`, auf origin/main und im annotierten Tag `php-before-go-migration` gesichert. Der Archiv-/Ontologie-Agent arbeitet in einem anderen Repository; neue Ontologie- und Suchfunktionen sind nicht Teil dieses Laufzeitwechsels.

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
  --candidate http://127.0.0.1:8080 --report /tmp/jackie-go-parity.json
```

Der normale Seitenvergleich oben verwendet keine pauschale Bytegleichheit für Assets: Die zwei dokumentierten Mount-Anpassungen werden mit `werkzeug/prefix_parity.py` streng geprüft; Aufruf und Normalisierungsregeln stehen in `werkzeug/parity.md`.

Der eingefrorene Snapshot liegt zusätzlich unter `/tmp/jackie-php-baseline-v2`; maßgeblich für Wiederaufnahme ist die dauerhafte lokale Kopie `.dev/migration-state/php-baseline-v2`. v1 bleibt separat erhalten. Screenshots, Layout-/Pixelresultate, Prüfberichte und Agenten-Checkpoints liegen unter `.dev/migration-state/`. Diese lokalen Arbeitsartefakte sind bewusst nicht in Git; der Prüfer und seine Normalisierungsregressionen sind versioniert.

Der direkte Leser-Differentialtest lässt sich zusätzlich mit `JACKIE_READING_FIXTURE="$PWD/.dev/migration-state/readers-expected.json"` und `JACKIE_CONTENT_ROOT="$PWD"` vor `go test ./internal/site` ausführen.

## Pause und Fortsetzung

„Pause“ hält laufende Agentenarbeit an. Vor der Fortsetzung zuerst Gitstatus und diesen Stand lesen; nicht fremde Änderungen zurücksetzen. Die Arbeit hängt nicht vom Kontext eines bestimmten Agenten oder einem laufenden Browser ab. Nach einem Neustart können die Server mit den dokumentierten Befehlen gestartet werden. Es gibt keine automatische Fortsetzung und keinen automatischen Produktionswechsel.

Entwicklung und Review waren getrennt. Der spätere vollständige Abgleich lief ausdrücklich auf dem günstigeren Modell GPT-5.6 mit hohem Reasoning-Aufwand. Root übernahm Integration, Leseregeln, Releasepaket und Browserprüfungen.

## Vor dem Produktionswechsel

Die separate Vorschau auf Hetzner ist mit `nginx -t`, `systemd-analyze verify`, realem Linux-Start, Proxy-/Dateirechteprüfung und öffentlichen HTTPS-/Browserprüfungen abgenommen; der Installer hat bei einem vorübergehenden Startcheckfehler seine automatische Rücknahme nachgewiesen. Details stehen in `ops/GO-PREVIEW.md`. Echte Turnstile-/Resend-Konfiguration und Zustellung sowie die spätere Umstellung der Hauptdomain sind noch nicht abgenommen. Der produktive VHost und `main` bleiben unverändert.

Nach Abnahme kann `main` auf den geprüften Migrationsstand vorgezogen werden. Der Sicherungstag und PHP-Worktree bleiben als Rückfall erhalten. Details stehen in `ops/GO-BETRIEB.md`, die Architektur in `docs/go-architecture.md` und der unabhängige Review in `docs/go-review.md`.

## Bereinigung des Migrationsbranches

Nach Einrichtung der Testinstanz wurden auf Wunsch des Nutzers die alte Anwendung
(`app/`, `index.php`, `.htaccess`), die doppelten JSON-Kataloge und die zugehörigen
Release-/FastCGI-/Installationswerkzeuge entfernt. Der Betriebsweg dieses Branches
ist ausschließlich Go; Inhaltspflege erfolgt über die Werkzeuge in `werkzeug/`.
Die alten Quellen bleiben über den Sicherungstag und den separaten Referenz-Worktree
wiederherstellbar. Die Git-Historie wird nicht umgeschrieben.

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
