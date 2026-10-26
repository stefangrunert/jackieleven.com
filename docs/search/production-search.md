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
   dem Server bereitstellen.
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
