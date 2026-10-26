# Lokale Suchabnahme · 26. Oktober 2026

> Historischer Bericht zur ersten lokalen Pilotphase mit 7.993 Passagen.
> Der erweiterte Bestand, die öffentliche Oberfläche und der Stagingbetrieb
> werden in [staging-search.md](staging-search.md) dokumentiert. Die unten
> genannten alten Rankingmessungen sind keine Abnahme des neuen Vollindex.


Die Suche ist lokal funktionsfähig und für die manuelle Prüfung eingerichtet. Einstieg: <http://127.0.0.1:8082/de/suche-test>, englisch unter `/en/search-test`. Die Produktionswebsite wurde nicht umgestellt. Dies ist die technische Abnahme eines ersten vollständigen Suchdurchstichs, keine Freigabe für öffentlichen Betrieb oder ein Nachweis überlegener Suchqualität.

## Tatsächlicher Bestand und Betrieb

- Website-Snapshot `ea653b6`, Archiv-Snapshot `7d353a4`.
- 572 Dokumente, 7.993 gespeicherte Textstellen, 965 vollständige Archivobjekte.
- 7.730 unterschiedliche Texte mit echten DeepInfra-Vektoren aus `Qwen/Qwen3-Embedding-8B`; 4.096 Ausgangsdimensionen, auf 1.024 gekürzt und L2-normalisiert, in PostgreSQL als `halfvec` gespeichert.
- Inhaltsversion `1b3daae24677b8f27d4428b84078b6950d0c82d9e6f22723557adfc8d8155339`; Profil `qwen3-8b-1024-v1` ohne generierten Kontextkopf.
- Eigener PostgreSQL-17.11-Container auf Loopback 55473 mit `pg_search 0.26.3` und `vector 0.8.6`; persistentes Volume, Grenze 1,5 GiB/1,5 CPUs. Zwei Benutzer-LaunchAgents betreuen Suchdienst 8081 und Testwebsite 8082. Docker Desktop muss laufen.
- Der Suchdienst verwendet eine ausschließlich lesende Rolle. Website und Browser erhalten keinen Datenbank- oder Anbieterschlüssel.

Der erste echte Import wurde zur Aufnahme zweier Textkorrekturen und zur Umstellung auf begrenzte parallele Batches unterbrochen. Bei der Fortsetzung wurden bereits gespeicherte Artefakte wiederverwendet. Die abschließende identische Wiederholung meldete **7.730 Cachetreffer, null fehlende Vektoren und null Embedding-Aufrufe**; der fertige Build wurde wiederverwendet. Unbeantwortete oder noch nicht persistierte Anbieteraufrufe können nach einem Abbruch erneut anfallen; eine exakt einmalige Abrechnung wird nicht behauptet.

## Durchgeführte Prüfungen

| Bereich | Ergebnis |
| --- | --- |
| Quelltreue | Alle 7.993 Textstellen gegen 1.075 gerenderte Referenzseiten geprüft; nach Korrektur zweier mehrzeiliger Markdown-Ausdrücke keine Abweichung. [Datenbericht](../../tools/search/validation.md). |
| Python-Pipeline | Registeridentität, Korrektur/Verschiebung/Löschung, Artefaktintegrität, begrenzte Parallelität und Wiederaufnahme getestet. Zwölf Tests insgesamt; neun ohne DB, drei zusätzlich mit echtem Test-DSN ausgeführt. |
| Datenbank und Rechte | BM25, exakte Kosinusdistanz, Textstimmenfilter, Textstelle, Entität, zwei getrennte Builds, Versionsabweichung, Leser-Schreibverbot und SQL-Abbruch geprüft. |
| Go | `go test ./...`, `go vet ./...` und Race-Prüfungen der Such-, API-, Client- und Website-Pakete bestanden. |
| Echte HTTP-Integration | `python3 ops/search/check.py --external`: 39 Prüfungen bestanden, einschließlich semantischer/hybrider Suche und tatsächlich ausgeführtem Reranking. |
| Ausfälle | `python3 ops/search/check-failures.py`: Anbieter deaktiviert → gekennzeichnete lexikalische Suche; nicht erreichbare DB → 503 statt leerer Trefferliste; Health/Readiness getrennt; bei ausgefallenem Suchdienst bleiben Startseite und Kontaktseite erreichbar. Es wurde dabei keine Testmail versendet. |
| Browser | DE-Formular, semantische Treffer, hybride Suche mit 20 Treffern und bestätigtem Reranking sowie genaue Textstellenansicht geprüft. Englisch und Präfixbetrieb zusätzlich durch HTTP-/Vertragstests und den Website-Agenten geprüft. |
| MCP | Lokaler Endpunkt aktiv; echte Aushandlung `2025-11-25` und Tool-Liste geprüft. SDK-Tests prüfen lesende Aufrufe, Host-/Origin-Grenzen und Kapazität. Werkzeuge: `search`, `get_passage`, `get_entity`. Keine öffentliche Clientanbindung behauptet. |
| Protokolle | Markierte Testbegriffe fehlen in den geprüften Go- und Datenbankprotokollen. Testwebsite umgeht das bisherige MAMP-SSL-Zugriffsprotokoll. Suchseiten setzen `no-store`, `noindex` und `no-referrer`; GET-Anfragen können im Browserverlauf verbleiben. |

Ein unabhängiger Agent prüfte Datenbindung, Importwiederaufnahme, API, Linkaufbereitung und Fehlerbehandlung. Korrigiert wurden die paarweise Query-Zuordnung des Rerankers, die unnötige Abhängigkeit reiner Vektorsuche von BM25 und der sichtbare Anbieterhinweis in Website und MCP.

Die Vollkorpusprüfung fand zusätzlich einen Fehler, der in einer kleinen Fixture nicht auffiel: Der Cast `$7::pdb.boost(3)` legte den Suchparametertyp so fest, dass dessen Verwendung als Text eine interne JSON-Darstellung durchsuchte. `$7::text::pdb.boost(3)` bindet zuerst den tatsächlichen Suchtext. Eine Fixture mit passenden JSON-Strukturwörtern und 18 wechselnde Anfragen auf derselben Datenbankverbindung prüfen diesen Fehler jetzt gezielt. Unbekannte Wörter liefern auch im vollständigen Bestand null lexikalische Treffer.

## Erste Relevanzbeobachtung

[Die zehn vorab festgelegten Pilotfragen](phase-1/validation-cases.json) wurden in allen drei Modi ausgeführt: **30 Anfragen ohne Rückfallbetrieb**. Die Rohbeobachtungen stehen in [pilot-search-results.json](pilot-search-results.json); Wiederholung mit `python3 ops/search/evaluate.py --external --output docs/search/pilot-search-results.json`.

Acht der zehn Fälle nennen ein bestimmtes erwartetes Dokument. Eines davon (Persona-Fall) ist als `stufe=weitere` absichtlich nicht indexiert; die Ergebnisdatei kennzeichnet dies mit `in_corpus=false`. Gezählt wird bei den sieben ausführbaren Fällen das Auftauchen des erwarteten Dokuments unter den ersten zehn **Textstellen**, nicht eine manuell bewertete Antwortqualität:

| Modus | Erwartetes Dokument unter Top 10 | Innerhalb der engeren Fallvorgabe |
| --- | --- | --- |
| Lexikalisch | 4 von 7 | 4 von 7 |
| Semantisch | 3 von 7 | 3 von 7 |
| Hybrid | 6 von 7 | 5 von 7 |

Der exakte norwegische Titel funktioniert lexikalisch und hybrid gut; die sprachübergreifende Anfrage profitiert von den Vektoren. Das erwartete Dokument für die Ankündigung/Ereignis-Unterscheidung fehlt in allen Modi im Top-10-Fenster. Der Persona-Fall ist eine ausgewiesene Korpuslücke, kein gemessener Rankingfehler. Die Namensvariante fällt hybrid auf Rang 9 statt des gewünschten Rangs 5. Das sind konkrete Ansatzpunkte für Ranking, Gruppierung und die spätere Verbindung strukturierter Aussagen. Andere Treffer können dennoch relevant sein; die Tabelle ist weder Recall über den gesamten Bestand noch ein vollständiger Goldstandard. Übersetzungen und unterschiedliche Absätze desselben Dokuments belegen derzeit eigene Trefferpositionen. Exakt identische kurze Texte desselben Dokuments, derselben Sprache, Stimme und Textart werden vor der Ergebniskürzung zusammengefasst. An der SQL-Auszuggrenze von 1.201 Zeichen wird vorsorglich nicht zusammengefasst, weil dahinter unterschiedliche Texte stehen könnten. Die Fälle 007 und 010 enthalten keine Dokumentrang-Vorgabe; ihre fachlichen Negativ-/Kennzeichnungsanforderungen sind damit nicht automatisch geprüft.

Ein einzelner sequenzieller Durchlauf ergab 4–20 ms für BM25 und 273–1929 ms für semantische Suche. Die unmittelbar anschließenden Hybridanfragen verwendeten bereits gecachte Anfragevektoren und lagen bei 33–38 ms. **Diese Werte sind kein Lasttest und kein fairer Geschwindigkeitsvergleich zwischen den Modi.** Separat gemessenes Reranking von 20 Exzerpten brauchte einmal rund 4,5 Sekunden; ein Browseraufruf mit anderer Anfrage und Reranking insgesamt rund 1,5 Sekunden. Deshalb gelten begrenzte Budgets von 3 Sekunden für Anfrage-Embeddings, 6 Sekunden für Reranking, 10 Sekunden im Suchkern und 11 Sekunden im Website-Client.

Bei einem zusätzlichen externen Prüflauf fiel das optionale Reranking einmal in den gekennzeichneten Rückfallbetrieb. Eine anschließende Einzelprüfung wurde wieder tatsächlich gerankt (835 ms Gesamtzeit). Die lokale Funktionsfähigkeit garantiert deshalb keine dauerhafte Verfügbarkeit des externen Anbieters.

Die unabhängige Live-QA bestätigte außerdem die genaue Textgleichheit von API und SSR-Reader sowie die Konfliktentität `event/2007-09-27-bodo-public`: Ankündigung und „Durchführung nicht belegt“ bleiben erhalten.

## Fachliche und betriebliche Grenzen

Die Suche findet gespeicherte Texte und erzeugt keine Antworten. Der Jahresfilter meint das Erscheinungsjahr, nicht das Konzertdatum. Quellenstimme und Stimme des angezeigten Texts bleiben getrennt. Das vollständige Archivobjekt ist über die Entitäts-API zugänglich; eine Abfragesprache über alle Beziehungen, belastbare Vollständigkeitsauskünfte und die automatisierte Bewertung strittiger Aussagen sind damit noch nicht umgesetzt.

Semantische Suche liefert nächste Nachbarn und kann auch bei einer unbeantwortbaren Frage Treffer zeigen. Ein leerer lexikalischer Trefferstand und ein Ausfall sind dagegen technisch getrennt. Pastiche wird nicht importiert. Fehlende Absatzanker auf Originalseiten werden durch eine genaue gespeicherte Textstellenansicht mit separatem Originallink überbrückt.

DeepInfra stellt einen veränderlichen Modellalias bereit. Dauerhafte Artefakte schützen vor unnötiger Wiederberechnung; sie garantieren keine bitgenau unveränderten Anbieterantworten in der Zukunft. Bei Anbieter-/Modelländerung sind Profilwechsel, Neuaufbau und erneute Relevanzprüfung erforderlich. Öffentliche Bereitstellung, Quoten, Proxyprotokolle, Produktionsbackup/Restore und ein ausreichend großer, zurückgehaltener Qualitätstestsatz bleiben eigene Freigabepunkte.

Bedienung, Start/Stop, neue Quellrevisionen und Manifestwechsel: [local-search.md](local-search.md). Architektur und laufender Stand: [suche-architektur.html](../../.dev/suche-architektur.html).
