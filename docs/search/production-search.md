# Suche auf jackieleven.com

Die Produktionswebsite und die Vorschau verwenden getrennte Suchprozesse:

- Website: `jackieleven-go.service`, `127.0.0.1:18765`.
- Produktionssuche: `jackieleven-search.service`, `127.0.0.1:18768`, Benutzer
  `jackieleven-search`.
- Vorschau: Website `18766`, Suche `18767`; unverändert weiter nutzbar.

Beide Suchprozesse lesen zunächst denselben unveränderlichen Index
`dd84acf1b05f7632f55cf61589245bd3a30eaea7d85d0f8e02c1bed82687f3be`
in `search_dd84acf1b05f7632` mit ausschließlich lesenden Datenbankrechten.
Die PostgreSQL-Instanz heißt historisch noch
`jackieleven-search-db-preview.service`, Port `55473`. Sie ist jetzt eine
**gemeinsame Produktionsabhängigkeit** und darf beim Aufräumen der Vorschau
nicht beendet oder entfernt werden. Neue Indizes erhalten neue Datenbanken;
Produktionsmanifest und Suchdienst werden bewusst gemeinsam umgestellt.
Ein Vorschau-Deployment verändert den gepinnten Produktionsindex nicht.
Ein Ausfall dieser gemeinsamen Instanz betrifft beide Suchen.

## Geschützte Konfiguration

`/etc/jackieleven-search/production.env` ist nur für root lesbar. systemd gibt
dem Suchprozess die Datenbankverbindung und den Pfad zum DeepInfra-Schlüssel.
Der Schlüssel liegt unter `/etc/jackieleven-search/deepinfra-key`, Modus 0600,
Eigentümer `jackieleven-search`. Er ist weder Teil eines Releases noch eines
Git-Commits und wird nicht an den Browser gegeben.

Die Website liest nur `/etc/jackieleven/search.env`: interne HTTP-Adresse und
Manifestpfad. Bestehende Formularzugänge unter `/etc/jackieleven/go.env` sowie
Formularzustand unter `/var/lib/jackieleven-go/contact` bleiben unangetastet.
Die PHP-Rückfallinstallation bleibt erhalten.

Die öffentliche Website spricht ausschließlich mit dem eigenen Suchdienst.
Nginx veröffentlicht weder API noch Datenbank. Für Suchanfragen gelten
12 Anfragen pro Minute/IP und 60 insgesamt, mit kurzen Bursts. Das ist ein
Lastschutz, kein tägliches Kostenbudget. Suchlogs enthalten keine Querystrings,
Referrer oder IP-Adressen; die Fehlerlogs dieser Locations sind deaktiviert.
Suchantworten sind `no-store`, `no-referrer` und `noindex`. Die übrige Website
bleibt indexierbar. Technische Testseiten liefern öffentlich 404.

## Aktualisierung

`ops/install-go-production.py` bleibt der Installer für die ursprüngliche
PHP-zu-Go-Umstellung. Für die bereits laufende Go-Website wird jetzt
`ops/update-go-production.py` verwendet:

1. Tests ausführen, Änderungen committen und pushen.
2. Sauberes Release mit `ops/prepare-go-release.py ZIEL --goos linux
   --goarch amd64 --search-manifest .dev/runtime/search/manifest.json` bauen.
3. Nach `/var/www/jackieleven/go-releases/RELEASE` übertragen. Installer,
   `install-go-production.py`, beide `nginx-search-production-*.conf` und
   `search/search-production.service` in derselben Verzeichnisstruktur auf
   dem Server bereitstellen. Beim Upload mit rsync `--no-owner --no-group`
   verwenden und ein neues, root-eigenes Zielverzeichnis wählen. Das gesamte
   Release muss root gehören; lokale macOS-Benutzer-IDs dürfen nicht übernommen
   werden. Hardlinks auf Releases mit abweichendem Eigentümer vermeiden.
4. Aktuellen Vhost-SHA256 und Ziel von `go-current` lesen. Danach als root:

   ```sh
   python3 update-go-production.py --release RELEASE \
     --expected-sha VHOST_SHA256 --expected-current BISHERIGES_RELEASE
   ```

Der Installer prüft Dateilisten, Checksummen, Plattform, sauberen Git-Stand
und beide Vorbedingungen. Er übernimmt beim ersten Start die bereits auf dem
Server freigegebenen Suchzugänge in die geschützte Produktionskonfiguration.
Es findet kein Datenbankimport statt. Eine Sperre verhindert parallele Aufrufe
dieses Installers. Administratoren müssen weitere Deployments koordinieren.

Vor dem Website-Wechsel werden Readiness, Manifestversion und eine echte
hybride Anfrage mit Reranking geprüft. Eine degradierte Antwort verhindert
die Aktivierung. Danach werden Startseite, Formularbereitschaft, DE/EN-Suche
und TLS am Origin geprüft. Der Formularcheck ist ein GET und versendet keine
E-Mail; er prüft CSRF-Token, Turnstile-Konfiguration, Submit und sichere Cookies.
Externe Erreichbarkeit und Browserdarstellung werden zusätzlich geprüft.

## Rückweg

Jede Aktualisierung speichert unter
`/var/backups/jackieleven-go-updates/ZEITSTEMPEL` die bisherigen Dateien,
Eigentümer, Rechte, Release-Verknüpfung und Dienstzustände. Fehler während der
Aktivierung stellen den vorigen Go-Stand automatisch wieder her. Der manuelle
Rückweg verwendet die zum Vorgang gespeicherte Version des Installers:

```sh
python3 /var/backups/jackieleven-go-updates/ZEITSTEMPEL/update-go-production.py \
  --rollback /var/backups/jackieleven-go-updates/ZEITSTEMPEL
```

Eine inzwischen aktivierte andere Release-Version verhindert einen veralteten
Rollback. Vorherige Go-Releases und der PHP-Rückfall werden nicht gelöscht.
Die Backups enthalten geschützte Konfiguration und gehören nicht ins Repository.


## Aktivierung und Prüfung am 26. Oktober 2026

Aktiv ist `search-production-20261026`, gebaut aus Commit `5929c12` auf
`codex/search-development`. Dieser Branch ist vollständig nach GitHub gepusht.
Die Aktualisierung des Standardbranches `main` ist ein gesonderter Schritt.
Der vorherige Stand `/var/www/jackieleven/go-releases/ba3224f` bleibt vorhanden.
Die Transaktion liegt unter
`/var/backups/jackieleven-go-updates/20261026T100802.730829Z`.

Vor der Aktivierung bestanden `go test ./...` und 21 Offline-Prüfungen der
Release- und Deployment-Werkzeuge einschließlich Rückweg und Dateirechten.
Eine erste Vorprüfung stoppte vor jeder Änderung an der laufenden Website,
weil rsync lokale Benutzer-IDs übernommen hatte. Die Eigentümer wurden nur im
neuen Release korrigiert; gemeinsame Dateiverknüpfungen zur Vorschau wurden
vorher aufgetrennt, damit deren Dateien unverändert blieben.

Die echte hybride Serveranfrage „konzerte in norwegen“ lieferte neun Treffer
mit Reranking ohne Rückfall in 1.872 ms. Dieselbe Suche funktionierte anschließend
im öffentlichen Browser und zeigte die vier passenden Bereiche. Das ist eine
Einzelmessung, keine Laufzeitzusage. Die schon geprüften Ladeanzeigen, der
Filter-Iconbutton und die Darstellung ohne dekorative Pfeile sind enthalten.

Extern bestätigt wurden Startseite und Suche auf Deutsch und Englisch,
Formularbereitschaft in beiden Sprachen sowie das Suchskript. Startseiten
bleiben indexierbar; Suchantworten liefern `no-store`, `no-referrer` und
`noindex`. Beide technischen Suchseiten, geprüfte Schlüsselpfade, `/v1/search`
und `/mcp` liefern 404. Die internen Ports 18765, 18768 und 55473 waren von außen
nicht erreichbar. Der Standard-User-Agent von Python wurde durch die vorgelagerte
Schutzschicht abgewiesen; Browser, curl und die Prüfung mit Browser-User-Agent
funktionierten ohne Änderung an diesem Schutz.

Der Schlüssel hat Modus 0600 und gehört ausschließlich dem Produktionssuchnutzer.
`www-data`, `jackieleven` und `jackieleven-preview` können ihn nicht lesen; kein
Release-Inhalt enthält den Schlüssel. Produktionswebsite und Suchdienst sind
für automatischen Start aktiviert. Alle Vorschauprozesse laufen weiter.
Der Formularcheck hat keine neue E-Mail versandt; der früher bestätigte echte
Versandtest bleibt separat vom aktuellen Bereitschaftscheck dokumentiert.
