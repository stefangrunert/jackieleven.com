# Öffentliche Suchvorschau auf Hetzner

Die Vorschau unter https://unpubli.sh/jackieleven erhält eine eigene Suche. Die
Produktionswebsite jackieleven.com und ihre Konfiguration bleiben unverändert.
Die Website zeigt ein Suchfeld und gruppierte Fundstücke; Bereich, Stimme und
Jahre liegen in einem zunächst geschlossenen Filterfeld. Die öffentliche Suche
verwendet automatisch Hybrid-Suche und Reranking. Technische Suchmodi bleiben
auf der lokalen Testseite. Die literarische Biografie erscheint nur nach
bewusster Auswahl und wird als Fiktion gekennzeichnet.

## Daten und fortlaufender Import

Der Vollbestand und seine konkreten Grenzen stehen in
[full-coverage.md](../../tools/search/full-coverage.md). „Alle Daten“ bedeutet die
veröffentlichten Website-Inhalte und den versionierten Archivgraphen; private
Recherchedateien, unsichtbare Detailtexte, ausgeschaltete Fanvideos und eine
nicht durchgeführte Bild-OCR sind ausgeschlossen.

Der Import läuft weiterhin lokal mit dauerhaftem Register, Artefaktcache und
Importzustand, nicht bei jeder Serveranfrage. Neue Git-Revisionen ausdrücklich
angeben:

```sh
python3 ops/search/local.py index --plan --website-revision REV --archive-revision REV
python3 ops/search/local.py index --workers 4 --website-revision REV --archive-revision REV
```

Nur neue Textinputs erzeugen neue Embeddings. Anschließend einen vollständigen
Read-Model-Dump der Schema `search` exportieren, nicht `indexer_state` mit seinen
lokalen Pfaden. Der Server bekommt einen unveränderlichen Indexstand; frühere
Datenbanken und Releases bleiben für einen Rückweg erhalten. Neue Daten werden
also inkrementell importiert, die Veröffentlichung erfolgt als geprüfter
Snapshot. Automatische Archivüberwachung ist noch nicht eingerichtet.

## Getrennte Prozesse

- Website: `jackieleven-go-preview.service`, Loopback `127.0.0.1:18766`.
- Suchdienst: `jackieleven-search-preview.service`, Loopback `127.0.0.1:18767`.
- Eigene PostgreSQL-Instanz: `jackieleven-search-db-preview.service`, Loopback
  `127.0.0.1:55473`; Daten unter
  `/mnt/HC_Volume_107171732/jackieleven-search-preview/pgdata`.
- Die vorhandenen PostgreSQL-Cluster werden weder ersetzt noch neu gestartet.
  PostgreSQL 17.11, pg_search 0.26.3 und vector 0.8.6 entsprechen dem lokalen
  Stand. pg_search wurde aus dem offiziellen Noble/amd64-Paket mit SHA256
  `033648d32c54e9e21dd57d1c4c0dc89ca7e45504741cc6a069491377d86bfe5d`
  additiv installiert. Es wird nur in der neuen Instanz vorgeladen.

Jeder Inhaltsstand erhält eine Datenbank `search_<erste 16 Zeichen der
content_version>`. Der Reader darf nur lesen. Die lokale HBA-Regel nennt den
konkreten Datenbanknamen. Website und Suchdienst lesen dasselbe Manifest beim
Start; nach einem Wechsel müssen beide neu gestartet werden.

Der Suchdienst läuft als eigener Systembenutzer ohne Schreibrechte auf Code
oder Index. Die Datenbank hat ein Speicherlimit von 1 GiB, der Go-Suchdienst
256 MiB. Öffentliche direkte Datenbank-, Such-API- oder MCP-Zugänge gibt es
nicht. Nginx spricht ausschließlich mit der Website.

## Bereitstellung

`ops/search/bootstrap-preview.py` ist ein einmaliger, rootpflichtiger Aufbau
für die dedizierte Instanz. Bei vorhandenem Datenverzeichnis verweigert er jede
Neuinitialisierung. Ein unterbrochener Aufbau benötigt eine manuelle Prüfung und Fortsetzung
am fehlenden Schritt; der Bootstrap bietet kein automatisches Resume. das Datenverzeichnis niemals zur Reparatur löschen.

1. Go-Tests und Exportprüfungen ausführen, Import abschließen.
2. Website mit `ops/prepare-go-release.py ZIEL --goos linux --goarch amd64
   --search-manifest .dev/runtime/search/manifest.json` paketieren. Das baut
   beide Go-Binaries und nimmt das Manifest in die SHA256-Dateiliste auf.
3. Über `docker --context desktop-linux exec jackieleven-search-dev-postgres-1`
   einen `pg_dump -Fc --schema=search --no-owner --no-acl` erzeugen und den
   SHA256-Digest festhalten. Private Dumps und Manifeste liegen lokal unter
   `.dev/runtime/search/deploy`, niemals im Git-Repository.
4. Release, Dump und Installer per SSH übertragen. `install-preview.py`
   verifiziert Release/Dump, stellt eine neue Datenbank her, vergibt Leserechte,
   bindet den Suchdienst an das Manifest und prüft `/readyz`. Scheitert der
   Restore, bleibt die bisher aktive Datenbank unberührt. Die gerade neu angelegte Datenbank wird bei einem fehlgeschlagenen
   Restore entfernt; ein erneuter Versuch kann sie frisch aufbauen.
5. `ops/install-go-preview.py` installiert die Website und Nginx-Regeln. Der
   erwartete SHA256-Wert des unpubli.sh-Vhosts verhindert das Überschreiben
   gleichzeitiger Änderungen. Website-/Nginx-Rollback erfolgt bei Fehlern
   automatisch; bei einer fehlgeschlagenen koordinierten Bereitstellung auch
   den Suchdienst auf seinen vorigen Stand zurückstellen.
6. Öffentliche Suche, Leseransicht, Präfixlinks, Sprachwechsel, Assets,
   Filter, Fiktionsauswahl und eine reale Anbieteranfrage prüfen. `/readyz`
   allein beweist keine funktionierende externe semantische Suche.

Der vorhandene DeepInfra-Schlüssel wurde nach ausdrücklicher Nutzerfreigabe
nur für diesen Suchdienst unter `/etc/jackieleven-search-preview/deepinfra-key`
hinterlegt (0600, Eigentümer Suchdienst). Die Datenbankverbindung liegt in einer
rootlesbaren systemd-Environment-Datei; die Website erhält nur interne URL und
Manifestpfad. Vorschau-Formularzugänge bleiben leer.

## Protokolle und Grenzen

Für die Suchpfade verwendet Nginx ein eigenes Access-Log ohne Querystring,
Referrer oder IP-Adresse; das Fehlerlog dieser Locations ist abgeschaltet,
weil Nginx dort Anfrage-URLs protokollieren könnte. Go protokolliert weder
Suchtexte noch Schlüssel. `Referrer-Policy: no-referrer` und `Cache-Control:
no-store` verhindern die Weitergabe der Such-URL als Referrer und reguläres
Zwischenspeichern. Browserhistorie, Cloudflare und DeepInfra haben eigene
Verarbeitung; diese Einstellung verspricht keine Löschung ihrer Daten.
Suchtexte werden für Embeddings, ausgewählte Textstellen für Reranking an
DeepInfra übertragen. Die Oberfläche erklärt das in einem geschlossenen
Hinweisfeld.

Nginx begrenzt Suchanfragen pro Client auf 12 pro Minute (kurzer Burst 8),
zusätzlich insgesamt auf 60 pro Minute (Burst 12). Die technischen Testpfade
liefern dort 404. Diese Grenzen begrenzen Last, sind aber kein tägliches
Kostenbudget. Der Dienst begrenzt Parallelität und Laufzeiten; bei einem
Anbieterausfall erscheint eine verständliche Rückfallanzeige.

## Sicherung und Rückweg

Deployment-Konfigurationen werden unter
`/var/backups/jackieleven-search-preview/<Zeitstempel>` und
`/var/backups/jackieleven-go-preview/<Zeitstempel>` gesichert. Vorherige Releases,
Indexdatenbanken und übertragene Snapshot-Dumps bleiben erhalten. Bei einem
Rückweg die gesicherten beiden Such-Environment-Dateien und Such-Unit sowie die
passende Website-Unit/Nginx-Konfiguration gemeinsam wiederherstellen,
`systemctl daemon-reload` ausführen und beide Vorschauprozesse neu starten.
Danach `nginx -t`, gezieltes Reload und reale Suchprüfung durchführen.

Zusätzlich müssen lokales `registry.sqlite3`, `artifacts/`, `exports/`,
`manifests/` und das lokale PostgreSQL-Volume zusammen gesichert werden. Die
Aufbewahrung auf demselben Server ersetzt kein externes Backup. Zugangsdaten
werden getrennt von veröffentlichten Releases aufbewahrt.
