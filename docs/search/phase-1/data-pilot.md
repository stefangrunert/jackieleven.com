# Datenpilot für die Suche, Phase 1

Stand: 26. Oktober 2026. Der Pilot enthält **16 Dokumentkandidaten: 14 vorhandene Archivdokumente und zwei ausdrücklich vorgeschlagene Kolumnenidentitäten**. Davon liefern 15 Kandidaten 119 vorhandene Textstellen; der verbleibende Paywall-Eintrag ist eine negative Metadatenkontrolle. Er ist kein Suchrelease und enthält weder eine Pipeline noch neue HTML-Anker.

Maschinenlesbarer Bestand: [pilot-manifest.json](pilot-manifest.json). Gemeinsamer Vertragsvorschlag: [data-contract.md](data-contract.md). Reproduzierbare lokale Prüfung: [data-check.py](data-check.py).

## Gebundene Quellenbasis

- Website-Basis: `3fd28a9` (vollständige Commit-ID im Manifest); Messort/Arbeitsbaum `/Users/stefan/.codex/worktrees/search-pilot-data/jackieleven`, Aufgabenbranch `codex/search-pilot-data`.
- Archiv: `7d353a4ce8043e284619fe409bfe87238dae2257`, ausschließlich lesend unter `/Users/stefan/www/jackieleven-archive`.
- 96 Eingabedateien sind mit Repository, relativem Pfad, Git-Blob und SHA-256 gebunden. Darunter befinden sich Quellnotizen, ausgewählte Archivdokumente/Ereignisse und direkte Metadatenabhängigkeiten, veröffentlichter Katalog, drei Originalseitenbilder, Sprachrouten, Vorlagen, Schema und Abdeckungsregister. `local_root` bezeichnet den historischen Messort und ist über Prüferargumente ersetzbar.
- Keine Anbieteraufrufe, kein Nachladen externer Originale, kein Lesen/Kopieren von API-Schlüsseln, keine Archivänderung. Vorhandene Angaben `live`/`paywall` sind historische Quellenmetadaten, kein aktueller Erreichbarkeitstest.

Die örtlichen Recherchedateien wurden gelesen; die DE/EN-Textlagen und Originalzitate des Websitekatalogs wurden voneinander getrennt. Drei lokale Originalseitenbilder wurden zusätzlich visuell geprüft: NME vom 28.10.1972, Druckseiten 24/33, und Record Mirror vom 20.06.1981, Seite 18. Die zwei ausgewählten Kolumnentranskriptionen wurden vollständig gelesen. Für andere Presseartikel liegt hier kein vollständiger Originaltext als Transkription vor: vorhandene Zusammenfassungen und Auszüge sind nicht zu Volltexten umgedeutet worden. Eine erneute unabhängige Originalprüfung aller historischen Erschließungen ist nicht Teil dieses Nachweises.

## Auswahl und tatsächliche Verfügbarkeit

„DE/EN“ bezeichnet redaktionelle Zusammenfassungen der Website. Die Sprache des Originals steht getrennt. Kennungen, Dateipfade, konkrete JSON-Pointer/Zeilenbereiche, Textprüfsummen, Archivbelegverweise und Ziele stehen pro Zeile im Manifest; keine fremden Volltexte werden in die Lieferdateien dupliziert.

| Pilot | Quelle | Vorhandene Texte/Originalsprache | Zweck und Grenze |
|---|---|---|---|
| D01 | NME, 28.10.1972, Gig Guide | DE/EN; englische Originalseiten als Bilder | Drei Folkclub-Ankündigungen; `primary_document` und `inferred`. Archiv-ID enthält `gig-guide`, Website-ID nicht. Keine Durchführung ableiten. |
| D02 | Ya, 28.01.1976, La Boîte Madrid | DE/EN; zwei spanische Originalauszüge samt DE/EN-Übersetzungen | `paywall`, nur BNE-Suchauszüge; kein vollständiger Wortlaut, ungenauer Konzertmonat. Doppelte Zitate werden nicht doppelt indexiert. |
| D03 | Record Mirror, 28.10.1978, Roundhouse | DE/EN + englische Originalzitate | Frontmatter anonym/Byline fehlt; Inhalt und Archiv nennen Alex Skorecki. Widerspruch bleibt sichtbar. |
| D04 | Sounds, 23.02.1980, Marquee | Nur bibliografisch nutzbar; Originalsprache EN | Titel „Shattered Dolls“, kein einsehbares Urteil. `stufe=weitere`: keine Detailseite und null Passagen. Unsichere Zusammenlegung zum 05.02.1980. |
| D05 | Record Mirror, 09.08.1980, Torrington | DE/EN + englische Originalzitate | Notiz über abgeschnittenes OCR/Byline steht neben später ausgebautem Inhalt mit Graham Stevens. Kein automatischer Unsicherheitsabbau. |
| D06 | Record Business, 15.06.1981, Venue | DE/EN + englischer Originalauszug | Datum 08.06.1981? und Identität mit D07 erschlossen. |
| D07 | Record Mirror, 20.06.1981, Venue | DE/EN + englische Originalzitate; Originalscan lokal | Scan bestätigt Robin Smiths Doll-by-Doll-Text; „Crystal Balls Up“ gehört zum Nachbarartikel. Alte ID bleibt nur aus Linkstabilität. |
| D08 | Nordlands Framtid, 15.04.1997, Bodø | DE/EN + norwegische Originalzitate (`no`) | Konzertbericht über Den Siste Glæde. Überlieferter Bühnenwitz bleibt Aussage im Bericht Dritter. |
| D09 | Nordlandsposten, 15.04.1997, Bodø | DE/EN + norwegische Originalzitate (`no`) | Zweite Stimme zur selben Veranstaltung. Archiv hält außerdem frühe Terminmenge 05./06./13.04. fest. Überschrift im Recherchevermerk unsicher. |
| D10 | Guardian, 03.02.2003, Korks Otley | DE/EN + englische Originalzitate | Publikationsdatum ist kein Konzerttag. Rückblick auf Levens Bühnenerzählung nicht als unabhängig belegte Biografie ausgeben. |
| D11 | Gaesteliste, 23.02.2003, Gloria Köln | DE/EN + deutsche Originalzitate | DE-Original plus EN-Zusammenfassung; Namens-/Titelfehlschreibungen nicht zu neuen Entitäten machen. |
| D12 | Whisperin & Hollerin, Leeds 19th Feb | DE/EN + englische Originalzitate | 2005 ist erschlossen; Datum im Dateinamen hat keine höhere Beweiskraft. |
| D13 | KindaMuzik, 22.09.2010, Paradiso | DE/EN + niederländische Originalzitate | Bericht über 19.09.2010; unbenannter Begleitmusiker bleibt unbenannt. Herkunftsbehauptung als Zuschreibung des Rezensenten. |
| D14 | theArtsDesk, 13.08.2011, Fringe | DE/EN + englische Originalzitate | Nur Leven-Teil der Sammelkritik. Cabaret Voltaire/11.08.2011 stammt aus ungeprüftem Kalender, im Archiv `inferred`. |
| D15 | Deep Pool, Februar 2003 | Vollständige englische Originaltranskription lokal; drei Pilotabsätze | Levens Stimme: Otley-Aufenthalt, geplantes Tromsø, Tour. Neue Archiv-Dokumentkennung nur vorgeschlagen; Tromsø-Zukunftsplan ist kein Durchführungsbeleg. |
| D16 | Blog, Bergen/Odda, Capture Dezember 2009 | Vollständige englische Originaltranskription lokal; drei Pilotabsätze | Reise, phantastischer Gletschertunnel, Odda. Capture-Monat ist kein Veranstaltungsdatum; Ich-Erzählung ist kein unabhängiger Beleg. Archivkennung nur vorgeschlagen. |

Die Auswahl deckt fünf Originalsprachen (`en`, `de`, `no`, `es`, `nl`) und drei **vorhandene** Archivbelegtypen (`third_party`, `primary_document`, `inferred`) ab. `self_statement` ist eine spätere Bindungsmöglichkeit für die Kolumnen, im ausgewählten Manifest aber noch kein bestehender Archivbeleg. Norwegisch wird nicht stillschweigend von `no` zu `nb` präzisiert. Pastiche, vollständige Fremdtexte und neu erschlossene Ereignisse wurden nicht hinzugefügt.

D08/D09 liefern die Überschneidung mit dem unabhängigen Testplan zu Bodø 1997. Andere dort untersuchte Fälle (Tromsø 2000, Public/Sinus 2007, Sir Vincent Lone, Kevin Foster/O’Foster) bleiben bewusst außerhalb dieses kleinen Importpiloten. Sie sind weiterhin sinnvolle zusätzliche Evaluationsfälle, sobald passende Quellen und Identitätsbindungen freigegeben sind.

## Quelle → Aussage/Entität → Website

48 ausgewählte Belegverweise verbinden die 14 Archivdokumente mit Ereigniszeit, Spielstätte und Durchführungsstatus. Mehrfach durch D06/D07 beziehungsweise D08/D09 belegte Aussagen führen zu insgesamt 42 unterschiedlichen Aussagekennungen. Diese Stichprobe ersetzt keinen vollständigen Graphenexport. Ganze Quelldateien sind gehasht, damit zusätzliche Belege, Notizen und konkurrierende Aussagen beim späteren Import erhalten bleiben können.

Besonders prüfbare Ketten:

- D01 → `event/1972-10-27-portsmouth-star-inn`, `st-886f2bd92670`, Status `announced`, `primary_document` → `/de/stimmen/1972-10-28-nme-john-st-field-folkclubs`. Die beiden weiteren Termine stehen in eigenen Ereignissen; Wochentage führen teils zu `inferred`-Datierungen.
- D06/D07 → `event/1981-06-08-london-the-venue`, `st-6d1e5b18eb22`, EDTF `1981-06-08?`, `inferred` → zwei verschiedene Kritiker-Seiten. Nicht zu einer einzigen Stimme fusionieren.
- D08/D09 → `event/1997-04-13-bodo-den-siste-glaede`, `st-483d637aef04` → zwei verschiedene Quellen-Seiten. Die ganze Ereignisdatei enthält außerdem `st-7a54fe0fa988` mit unsicherer Terminmenge. Diese Alternative ist in der Stichprobenauswahl nicht erneut als eigene Referenz enthalten, muss im späteren Export erhalten bleiben.
- D14 → `st-975cb783ec84` (Zeit) und `st-327363694cc8` (Spielstätte), beide `inferred` → ArtsDesk-Quellenseite. Der Originalkritik keine selbst nicht enthaltenen Orts-/Tagesangaben unterschieben.
- D04 → zusammengelegtes Marquee-Ereignis, aber als Websiteziel nur `/de/stimmen?auswahl=0#1980-02-23-sounds-doll-by-doll-marquee-london` im geschlossenen Metadatenblock. Kein `.../stimmen/<id>`-Detailziel und kein Passage-Treffer.

Zwölf Zitatverweise haben eine exakte Teilzeichenketten-Übereinstimmung mit vorhandenen Originalauszügen. Das Manifest nennt die Kandidaten, lässt die fachliche Bindung aber offen: Textübereinstimmung allein beweist nicht die ganze Aussage. Aktuell sind keine `passage`-Verweise im geprüften Archivbestand dieser Auswahl gesetzt.

## Ziele, Rechte und Prüfgrenzen

Die Pfade sind aus tatsächlichen Katalogeinträgen, `sourcePage`, `routePath`, Sprachdateien und Vorlagen abgeleitet. Die Detailseiten rendern DE/EN-Zusammenfassungen sowie Originalzitate; Originalsprache und UI-Sprache können auseinanderfallen. Kolumnen werden in beiden Oberflächensprachen auf Englisch gezeigt. Das vorliegende Ergebnis ist eine Quellcode-/Dateiprüfung, noch kein HTTP-/Browsernachweis.

Vorhandene Abschnitte heißen `#quelle`, teils `#beleg`, bei Kolumnen `#quellenhinweis`. **Keine der 119 vorgeschlagenen Passagekennungen ist schon ein HTML-Anker.** Bei den Kolumnen wäre außerdem eine Freigabe der neuen Archividentität nötig. Diese Lücken verhindern einen sofort als fertig bezeichneten Belegdurchstich; der Vertragsentwurf beschreibt die nächsten Schritte.

Die Archivlizenz `LICENSE-DATA.md` nennt CC BY-NC 4.0 für die eigenen Daten und nimmt Fremdzitate, Leven-Texte und Fremdbilder aus. D08/D09 tragen im Websitekatalog `ccbyncnd`, geprüft am 23.10.2026; das wird als vorhandener Metadatenwert erhalten, nicht als neue umfassende Nutzungserlaubnis interpretiert. Viele Quellen haben `lizenz=null`. Zugriff (`frei`, `online`, `abo`) ist keine Lizenz. Der Pilot dupliziert keine Volltexte, lädt nichts herunter und trifft keine neue rechtliche Bewertung.

## Prüfungen und Wiederaufnahme

Der Prüfer arbeitet ausschließlich lesend über `git show <commit>:<path>` und ersetzt bei Bedarf die historischen Root-Pfade:

```sh
/Users/stefan/www/jackieleven-archive/.venv/bin/python \
  docs/search/phase-1/data-check.py \
  --website-root /Users/stefan/.codex/worktrees/search-pilot-data/jackieleven \
  --archive-root /Users/stefan/www/jackieleven-archive
```

Er benötigt Python und PyYAML (im bereits vorhandenen Archiv-venv verfügbar; nichts installiert). Er prüft JSON, gebundene Revisionen/Hashes, alle Textselektoren und Einzeltexthashes, eindeutige vorgeschlagene Passage-IDs, vorhandene Archiv-/Aussage-/Referenzkennungen, tatsächlich übernommene Belegtypen und Zitatkandidaten, Website-Datensatzzuordnungen, Detail-/Katalogpfade, Kolumnenallowlist und die fehlenden Absatzanker. Das Bestehen bestätigt keine Originalrechte, fachlich richtige Aussagen oder bereits funktionierenden HTTP-Beleglinks.

Offen bleiben die Register-/Kennungsfreigabe, verbindlicher Teilgraph und Belegprüfung, die Umsetzung präziser Anker samt HTTP-Test sowie der eigentliche wiederaufnehmbare Import. Bei Fortsetzung zuerst Commit/Worktree prüfen, dann den Prüfer wiederholen und den Vertrag gemeinsam festschreiben. Keine laufenden Dienste oder Versuchsprozesse gehören zu diesem Arbeitspaket.
