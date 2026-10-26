# Postgres-/BM25-Pilot, Phase 1

Stand: 26. Oktober 2026. Basis: Website `3fd28a9`; Aufgabenbranch `codex/search-pilot-database`. Keine Archivdaten oder Produktionsdienste wurden verwendet. Die zehn Testtexte sind erfunden; historische Aussagen lassen sich daraus nicht ableiten.

## Ergebnis und Empfehlung

**Beide Kandidaten wurden tatsächlich installiert und abgefragt:** ParadeDB `pg_search 0.26.3` und `pg_textsearch 1.5.1`, jeweils mit PostgreSQL `17.11` auf Linux ARM64. Die 14 SQL-Assertions für Sprachformen, genaue Namen, Phrasen mit Gegenfällen, Metadatenfilter, Nulltreffer und Gewichtung bestehen. Der vollständige Lauf einschließlich eines kleinen Ressourcenversuchs lässt sich mit den Dateien unter `ops/search-pilot/` wiederholen.

Für den nächsten Durchstich empfehle ich **vorläufig ParadeDB**, weil eigene Analysefelder, Phrasen und Titelboost in einem Index direkt funktionieren. Das ist eine Empfehlung aus Funktionsprüfung und Integrationsaufwand, keine bestätigte Entscheidung über Relevanz oder Produktionstauglichkeit. `pg_textsearch` bleibt eine ernsthafte Alternative: im kleinen Versuch deutlich kleinere Indexdateien, bestehende PostgreSQL-Sprachanalyse und eine permissive PostgreSQL-Lizenz. Dafür müssen die Trefferbedingungen und die Kombination mehrerer Felder besonders sorgfältig festgelegt werden. Die [Projektbeschreibung](https://github.com/timescale/pg_textsearch) nennt die Lizenz; ParadeDB führt [AGPL-3.0](https://github.com/paradedb/paradedb/blob/v0.26.3/LICENSE).

Ein eigener Cluster ist für die nächste Stufe der sichere Ausgangspunkt. Beide Erweiterungen werden im Pilot vorgeladen; eine zusätzliche Datenbank im bestehenden Cluster würde diese Startkonfiguration und das Ressourcenbudget nicht isolieren. Die Produktionsinstallation wurde nicht geprüft oder verändert.

## Lokale Voraussetzungen und feste Versionen

Docker CLI `29.2.0`, Compose `v5.0.2` und Docker Desktop `4.60.1 (218372)` sind vorhanden; der Host ist `darwin/arm64`, die Engine `linux/arm64`. Die Engine war anfangs gestoppt. Der erste Aufruf innerhalb der Sandbox meldete fehlenden Socketzugriff; die freigegebene Wiederholung meldete einen nicht erreichbaren Daemon. Nach dem autorisierten `open -a Docker` war die Engine erreichbar. `psql` war nicht im Host-PATH; sämtliche DB-Werkzeuge liefen im Container.

| Bestandteil | Gebundene Fassung |
|---|---|
| ParadeDB-Image | `paradedb/paradedb:0.26.3-pg17@sha256:950f68abebc78e28fd2ecfc8ed915aa29d07b5dd8cba25b2f513ca4e211dda70` |
| Postgres-Basis für pg_textsearch | `postgres:17.11-bookworm@sha256:858bb5e98eed02eb8cafbcdc007f9a65d1b613972028944a8ec2133ccaf80d27` |
| pg_textsearch-Paket | `pg-textsearch-v1.5.1-pg17-arm64.zip`, SHA256 `e65f953e99f47c05dde88a031884cf36ea269bcb62377f554b76ddb4d13fdc3e` |
| Inhalt des Pakets | `pg-textsearch-postgresql-17_1.5.1-1_arm64.deb` |
| Gemessene ParadeDB-DB | PostgreSQL `17.11`, Debian Trixie; `pg_search 0.26.3`, `vector 0.8.6` |
| Gemessene pg_textsearch-DB | PostgreSQL `17.11`, Debian Bookworm; `pg_textsearch 1.5.1` |

Image-Digests stammen aus dem tatsächlichen Pull und Inspect, die Paketprüfsumme wurde gegen die [Release-Metadaten](https://github.com/timescale/pg_textsearch/releases/tag/v1.5.1) geprüft. `run.py` prüft sie bei jedem Lauf vor dem Entpacken. Der pgvector-Stand ist über das ParadeDB-Image gebunden. Dies ist ein ARM64-Pilot; amd64 und das Betriebssystem des Produktionsservers bleiben ungeprüft. Die Debian-Basis ist unterschiedlich, daher ist auch der Ressourcenvergleich nicht streng kontrolliert.

Installationserfahrung: Das vollständige ParadeDB-Image versucht standardmäßig zusätzlich `pg_cron` zu initialisieren. Mit ausschließlich `shared_preload_libraries=pg_search` scheiterte dieser Bootstrap. Der Pilot blendet deshalb `/docker-entrypoint-initdb.d` mit einem leeren tmpfs aus und lädt anschließend nur `pg_search CASCADE`. Das installiert auch `vector`, wie in der [Installationsanleitung ab Version 0.25.0](https://www.paradedb.com/docs/operate/deploy/self-hosted/extension) beschrieben. Der PostgreSQL-Basiscontainer mit dem geprüften pg_textsearch-DEB ließ sich ohne zusätzliche Pakete bauen.

## Isolation und Wiederholung

Voraussetzungen: laufende lokale Docker-Engine, Python 3, Internetzugriff für die beiden Images und das rund 1-MB-Erweiterungspaket. Es werden weder Datenbankkennwörter des Hosts noch Archivdateien gelesen. Das sichtbare Kennwort `synthetic-pilot-only` gilt ausschließlich für die wegwerfbaren Pilotdatenbanken.

Vom Repository-Stamm:

```sh
python3 ops/search-pilot/run.py
```

Die Skriptdatei enthält die vollständigen Befehle; wesentliche Einzelschritte sind:

```sh
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml config --quiet
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml build textsearch
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml up -d
# run.py kopiert ausschließlich die SQL-Dateien nach /pilot.
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml exec -T parade psql -X -v ON_ERROR_STOP=1 -U pilot -d pilot -f /pilot/parade.sql
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml exec -T textsearch psql -X -v ON_ERROR_STOP=1 -U pilot -d pilot -f /pilot/textsearch.sql
docker compose -p jackieleven-search-pilot -f ops/search-pilot/compose.yaml down --volumes --timeout 10
```

Projektname: `jackieleven-search-pilot`. Ports: `127.0.0.1:55471` und `127.0.0.1:55472`; Bindbarkeit wird vor Start geprüft und Docker prüft sie beim Start erneut. Eigenes internes Docker-Netz ohne ausgehenden Verkehr, eigene Volumes `jackieleven-search-pilot_parade-data` und `jackieleven-search-pilot_textsearch-data`. Je Container: 1 CPU, 1 GiB Speicherlimit, 256 MiB `/dev/shm`, 10 Verbindungen, 128 MiB `shared_buffers`, 4 MiB `work_mem`, 64 MiB Wartungsspeicher. Bei pg_textsearch zusätzlich 64 MiB für den Memtable-Cache; dieses Budget ist keine harte Grenze für den gesamten Prozess.

Das Skript verweigert entfernte Docker-Endpunkte und bereits vorhandene Ressourcen mit seinem Projektnamen. Es verändert keine fremden Container. SQL-Fehler brechen ab; Assertions verwenden IDs statt instabiler Scoregleichheit. Die SQL-Verarbeitung und Benchmarkabfragen haben eine 10-Sekunden-Frist. Ein `finally`-Block entfernt die eigenen Container, Volumes und das Netz auch nach einem Fehler oder SIGTERM/KeyboardInterrupt. Bei einem harten Prozess-/Hostabbruch zuerst den Projektzustand prüfen; erst dann gezielt den oben gezeigten `down`-Befehl verwenden.

Lokale Ergebnisse liegen ignoriert unter `ops/search-pilot/results/`. Der geprüfte Lauf ist als unveränderlicher Textstand unter [database-evidence](database-evidence/) versioniert. Downloads bleiben ignoriert unter `ops/search-pilot/downloads/`; Images bleiben im Docker-Cache. Keine laufende Datenbank ist zur Wiederaufnahme notwendig.

## Gemessene Funktion

| Prüfung | Erwartung / gemessen | Einordnung |
|---|---|---|
| Deutsch: Sänger/Lied/Stadt | IDs 3, 4 bei beiden | ParadeDB-Sprachfeld mit deutschem Stemmer; pg_textsearch-Teilindex mit `german` und explizitem FTS-Prädikat |
| Englisch: sing/song | ID 1 bei beiden | Englisch gestemmt; Ausgabe der Token/Lexeme liegt bei |
| Name genau `Jackie Leven` | IDs 1, 3, 4, 5 | ParadeDB mit Literal-Feld; pg_textsearch-Kandidat verwendet gewöhnliche SQL-Gleichheit und separaten Btree, keine BM25-Namensfunktion |
| Titelphrase `The Deep Pool` | IDs 1, 5 | ID 2 enthält im selben Feld `The Deep Blue Pool`, ID 8 `Pool Deep The`: beide ausgeschlossen |
| Phrase + Stimme + Jahr | ID 1 | Pastiche und späteres Jahr ausgeschlossen |
| Unbekanntes Wort | keine Treffer mit expliziter Trefferbedingung | Bei pg_textsearch reicht eine bloße Score-Sortierung nicht zuverlässig |
| Titelgewicht 4 | ID 6 rückt vor ID 7 | ParadeDB: nativer Query-Boost; pg_textsearch: experimentelle gewichtete Summe zweier Indexscores |

Die deutschen Analysen ergeben in beiden Fällen `sang`, `spielt`, `lied`, `stadt`; englisch entstehen `sing`, `song`, `river`. Das bestätigt nur diese Beispiele. ParadeDB bewahrt mit `pdb.literal` den ganzen Namen einschließlich Großschreibung; PostgreSQL `simple` zerlegt den Namen in kleingeschriebene Wörter. Deshalb bleibt exakte Namensgleichheit bewusst ein eigener Pfad. Diakritische Varianten, Aliasauflösung und Fehlertoleranz sind noch keine bestandenen Suchfälle.

Die Sprachprüfungen sind Funktionsproben, kein identisch parametrisierter Relevanzvergleich: ParadeDB verwendet hier Match-any, der PostgreSQL-FTS-Prädikatpfad Match-all. Die Phrase ist bei ParadeDB eine Indexabfrage. Bei pg_textsearch ist sie PostgreSQL-FTS mit `phraseto_tsquery`; die Erweiterung unterstützt solche Prädikate, darf Positionen aber nachprüfen. Eine erfolgreiche Phrase belegt daher nicht allein einen ausschließlich nativen BM25-Phrasenpfad. Die [versionsgebundene Anleitung](https://github.com/timescale/pg_textsearch/blob/v1.5.1/README.md) beschreibt die Sprachkonfiguration, Teilindizes und Rechecks. Feldscoreaddition ist ausdrücklich weder BM25F noch eine empfohlene spätere Hybridfusion.

Ein relevanter Korrektheitsbefund: Der natürliche pg_textsearch-Plan für die kleine gefilterte Rangabfrage war ein sequenzieller Scan mit Sortierung und lieferte fünf Zeilen, obwohl nur eine lexikalisch passte. Der erzwungene BM25-Indexplan lieferte eine. Bei erzwungenem sequenziellem Scoring liefert auch ein unbekanntes Wort Zeilen mit Score null. Der Suchdienst muss deshalb ein explizites Trefferprädikat verwenden; seine Nulltreffersemantik darf nicht vom Planner abhängen. In der ParadeDB-Planprobe war ein `Custom Scan` sichtbar, mit `voice <> 'pastiche'` als Heap-Filter. SQL-Filter allein beweisen also noch keine vollständige Index-Pushdown-Optimierung.

## Ressourcenmessung und Grenzen

Nach den zehn Funktionstestdatensätzen wurden 99 Kopien ergänzt: insgesamt 1.000 synthetische Zeilen. Anschließend wurden die Indizes neu aufgebaut und analysiert. Für beide Kandidaten liefen dieselbe Titelphrase und derselbe Stimme-/Jahrfilter mit `LIMIT 5`: 10 Aufwärmtransaktionen, dann 100 Transaktionen mit einem lokalen Socket-Client. `pgbench`-Einzellatenzen und Auswertung liegen im Belegverzeichnis. Die Zahlen enthalten keine HTTP-, TCP-, Embedding- oder Rerankingzeit.

| Messung, finaler Lauf | ParadeDB | pg_textsearch |
|---|---:|---:|
| Tabellenbytes, 1.000 Zeilen | 180.224 | 180.224 |
| Suchindexbytes | 3.129.344 (ein Index) | 131.072 (vier BM25-Indizes zusammen) |
| Datenbankbytes | 12.203.699 | 8.148.659 |
| Latenz p50 | 0.2960 ms | 0.4175 ms |
| Latenz p95 | 0.416 ms | 0.492 ms |
| Höchste beobachtete Einzellatenz | 2.578 ms | 1.537 ms |

Docker-Stats nach dem Lauf:

```text
jackieleven-search-pilot-parade-1 CPU=0.06% Memory=33.09MiB / 1GiB PIDs=6
jackieleven-search-pilot-textsearch-1 CPU=0.05% Memory=26.55MiB / 1GiB PIDs=6
```


Die Speichernutzung ist ein einmaliger Docker-Stats-Wert nach der Last, kein Peak und keine Zusage für RAM-Bedarf unter Parallelität. Datenbankgrößen enthalten Basiskataloge und unterschiedliche Erweiterungen. Indexumfang und Analysekonfiguration unterscheiden sich. Die 1.000 kurzen Duplikate simulieren weder lange Kolumnen noch ein realistisches Vokabular. Aus diesen Werten folgt keine Kapazitätszusage für den geteilten 4-GB-Server und kein belastbarer Geschwindigkeitsgewinner. CPU unter Last, kalte Caches, p95 unter Parallelität, mehrere Releases und Indexbuild-Peaks bleiben offen.

## Nur recherchiert oder noch offen

- Die offiziellen Dokumentationen beschreiben [deutsches/englisches Snowball-Stemming](https://www.paradedb.com/docs/reference/token-filters/stemming), [Literal-Felder](https://www.paradedb.com/docs/reference/tokenizers/available-tokenizers/literal) und [Boosting](https://www.paradedb.com/docs/reference/full-text/relevance-tuning); die oben bezeichneten Fälle wurden zusätzlich ausgeführt. Andere Tokenizerkombinationen wurden nicht bewertet.
- pg_textsearch verwendet negative Scores (kleiner ist besser), ParadeDB positive Scores (größer ist besser). Diese Werte werden nicht kandidatübergreifend addiert. Der reale Testsatz muss Sprachwahl, Titel, Belege, Stopwörter, kurze Anfragen, Katalognummern, fehlende Treffer und Pastiche getrennt bewerten.
- Ein Versionsupgrade wurde nicht ausgeführt. Die [pg_textsearch-Upgradeanleitung auf main](https://github.com/timescale/pg_textsearch/blob/main/UPGRADING.md), abgerufen am 26.10.2026, verlangt Neustart mit neuer Bibliothek und SQL-Update; versionsabhängig auch Reindexierung. Sie war unter dem Release-Tag v1.5.1 nicht verfügbar und ist daher ausdrücklich ergänzende, bewegliche Dokumentation. Ein Rückwechsel der Binary macht Indexformatänderungen nicht rückgängig. Für beide Kandidaten vor Produktion: frischen Releaseindex aus gebundenen Daten bauen, Versionswechsel, Abbruch, Rollback und Wiederaufbau tatsächlich testen.
- Produktions-OS, Architektur, Paketinstallation, freier RAM, pgvector-Kompatibilität und Rechte wurden nicht geprüft. Der Pilot darf nicht in den bestehenden Produktionscluster übertragen werden, ohne diese gesonderte Abnahme.

## Zustand bei Übergabe

Der finale Skriptlauf entfernte seine beiden Container, beide Datenvolumes und sein Netz geordnet. Docker Desktop bleibt geöffnet; heruntergeladene Images und das geprüfte Paket bleiben als Cache erhalten. Fremde Dienste wurden nicht beendet oder geändert. Nächster Schritt: realen Phase-1-Pilotbestand und unabhängige Erwartungen in denselben isolierten Aufbau laden, Analyse-/Treffersemantik angleichen und erst danach den BM25-Kandidaten bestätigen.
