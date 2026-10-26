# Phase 1: Grundlagen der Suche

Stand: 26. Oktober 2026. Integrationsbranch `codex/search-development`.

Die [Architektur mit Agentenplan und Arbeitsstand](../../../.dev/suche-architektur.html) ist das zusammenhängende Hauptdokument. Phase 1 liefert Daten-, Technik- und Prüfgrundlagen. Sie implementiert noch keinen produktiven Suchdienst oder Importer.

## Ergebnisse

| Arbeitspaket | Liefergegenstand | Tatsächlich geprüft |
|---|---|---|
| Datenpilot | [Bericht](data-pilot.md), [Vertragsentwurf](data-contract.md), [Manifest](pilot-manifest.json), [Prüfer](data-check.py) | 96 Dateihashes, 16 Dokumentkandidaten, 119 Textselektoren, 48 Belegverweise auf 42 Aussagen, 12 exakte Zitatkandidaten |
| Datenbankpilot | [Bericht](database-pilot.md), [Messbelege](database-evidence/manifest.txt), [Versuchsdateien](../../../ops/search-pilot/) | Beide Kandidaten auf PG 17.11/ARM64; 14 SQL-Assertions; 1.000 synthetische Zeilen, je 100 warme Einzelclient-Messungen |
| Unabhängige Validierung | [Prüfplan](validation-plan.md), [zehn Fälle](validation-cases.json) | Gebundene Quellen, Kennungen, Routen und Textlagen; spätere Import-/Such-/Lasttests ausdrücklich nicht ausgeführt |

Der Datenpilot enthält 14 bestehende Archivdokumente und zwei Kolumnen mit vorgeschlagenen Archividentitäten. Ein Metadateneintrag hat keinen indexierbaren Text. Die 119 Passagekennungen sind Vorschläge, keine bereits veröffentlichten HTML-Anker. Quellenstimme und tatsächliche Textstimme bleiben getrennt.

Website-Quellenbasis: `3fd28a91f7bae2355492b24979ec9688f593c216`. Archivbasis: `7d353a4ce8043e284619fe409bfe87238dae2257`. Keine Änderung oder Veröffentlichung im Archiv-Repository, keine DeepInfra-Aufrufe. Die bestehenden Website-Laufzeitdateien wurden in dieser Phase nicht geändert.

## Integrationsentscheidungen

- **ParadeDB 0.26.3 als vorläufiger Kandidat für Phase 2.** Die Funktionsprüfung spricht für den direkteren Mehrfeld-/Phrasenpfad. Relevanz, reale Archivtexte, Produktionsarchitektur amd64 und Belastbarkeit des Servers sind noch nicht abgenommen. pg_textsearch 1.5.1 bleibt dokumentierte Vergleichsoption.
- **Textstimme ist eine eigene Eigenschaft.** Der Vertrag verwendet `source_voice` und `text_voice`; redaktionelle Zusammenfassungen sind keine Originalzitate. Gruppierung zunächst nach `text_voice`.
- **Pipelinezustände:** `pending`, `running`, `done`, `failed`, mit gesonderten Wiederholungsdaten. `done` erfordert ein validiertes dauerhaftes Ergebnis. Die Benennung wurde zwischen Architektur und Vertragsentwurf angeglichen.
- **Freigabe ist nicht gleich Deployment.** Eine transaktionale Registerfreigabe ersetzt keine koordinierte Aktivierung von zwei Diensten und nginx; die Inhaltsversionsprüfung bleibt erforderlich.
- **Kein automatischer Ausbau des öffentlichen Archivs.** Für Kolumnenidentitäten, Passage-Register und Belegbindungen wird in Phase 2 eine nachvollziehbare Zuordnung vorbereitet.

## Abgleich von Pilotbestand und Prüffällen

Die Daten- und Validierungsagenten haben unabhängig ausgewählt. Das ergibt bewusst keine sofort vollständig ausführbare zehnteilige Suchsuite:

| Fall | Dokument im aktuellen Pilot | Noch erforderlich |
|---|---|---|
| `p1-date-conflict-006` | ja, D08/D09 | vollständige konkurrierende Aussagen im Teilgraph; echte Anker |
| `p1-announcement-only-008` | ja, D01 | Ankündigungsstatus erhalten; echte Anker |
| `p1-cross-language-inference-009` | ja, D02 | Originalauszüge, Übersetzungen und Unsicherheit getrennt erhalten |
| `001`, `002`, `003`, `004`, `005`, `007` | erwartete Dokumente außerhalb dieser Auswahl | kontrollierte Erweiterung des Pilotmanifests vor Ausführung |
| `p1-negative-010` | kein positiver Solltreffer | Negativraum explizit auf den freigegebenen Korpus begrenzen; Kontextdaten für die Ortsverwechslung ergänzen |

Fehlende Eingaben bedeuten `blocked` beziehungsweise `not_run`, keine fehlerhafte Suche und keinen bestandenen Test. Vor dem Rankingvergleich werden Korpus und erwartete Belege gemeinsam eingefroren. Eine deutsche Anfrage mit deutscher Zusammenfassung als Treffer ist noch kein Nachweis rein semantischer sprachübergreifender Leistung.

## Unabhängiger Review

Der Validierungsagent hat den Datencommit `cfc811ecceec7709e9542991f477136c1ed44153` zusätzlich unabhängig geprüft: keine Blocker für den Phase-1-Vorschlag. Neben dem lesenden Prüfer wurden alle 119 Entwurfs-IDs aus der Bootstrapregel reproduziert und Textstimmen/Sprachen sowie die drei direkten Testfallüberschneidungen gegengeprüft. Der Koordinator hat den Prüfer im Integrationsrepo erneut erfolgreich ausgeführt und die elf Quellprüfsummen des Datenbankversuchs mit den übernommenen Dateien abgeglichen.

Vor Phase 2 wird der verbindliche Validator um explizite Regeln für Übersetzungsstimme/Versionsgruppe und die Zuordnung des Kolumnenautors zu `source_voice=leven` ergänzt. Der aktuelle Bestand wurde dafür manuell geprüft; der Phase-1-Prüfer behauptet keine vollständige Schemaabdeckung. Die abweichenden Zustandsnamen und die ungenaue Überschneidungsbeschreibung wurden bei Integration korrigiert.

## Wiederaufnahme

Die drei Aufgabenbranches heißen `codex/search-pilot-data`, `codex/search-pilot-database` und `codex/search-pilot-validation`; die zugehörigen verwalteten Worktrees liegen unter `/Users/stefan/.codex/worktrees/search-pilot-*/jackieleven`. Sie bleiben für Nachprüfung und spätere Aufgaben erhalten. Der Integrationsbranch enthält ihre geprüften Liefergegenstände und die dokumentierten Vertragskorrekturen.

Lesende Quellenprüfung vom Integrationsrepo aus:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/stefan/www/jackieleven-archive/.venv/bin/python \
  docs/search/phase-1/data-check.py \
  --website-root /Users/stefan/www/jackieleven \
  --archive-root /Users/stefan/www/jackieleven-archive
```

Ein erneuter Datenbankversuch ist separat und nur bei Bedarf auszuführen:

```sh
python3 ops/search-pilot/run.py
```

Das erzeugt eigene temporäre Container/Volumes, verwendet synthetische Daten und räumt sie wieder auf. Der abgeschlossene Versuch hat seine Container, Volumes und sein Netz entfernt. Docker Desktop bleibt gestartet; Images und Paketdownloads bleiben im lokalen Cache. Keine laufende Pilotdatenbank muss für Phase 2 übernommen werden.

Nächster Entwicklungsschritt: den Datenvertrag als Schema und API-Vertrag festschreiben, Registerort und Identitäten zuordnen, einen vollständigen Pilot-Teilgraph erstellen und dann den lesenden BM25-Durchstich zwischen separatem Dienst und Website implementieren. Die detaillierten Schritte und Abnahmen stehen im Hauptdokument. Noch keine Test- oder Produktionsbereitstellung.
