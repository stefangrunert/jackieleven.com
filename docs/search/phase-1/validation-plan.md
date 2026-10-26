# Validierungsplan für Phase 1

Stand: 26. Oktober 2026

Basis Website: `3fd28a91f7bae2355492b24979ec9688f593c216`

Basis Archiv: `7d353a4ce8043e284619fe409bfe87238dae2257`

Status: Prüfplan; die beschriebenen Such- und Ausfalltests wurden noch nicht ausgeführt.

## Zweck und Prüfgrenze

Dieser Plan bereitet die unabhängige Abnahme des ersten Daten- und Suchpiloten vor. Er trennt vier Fragen: Ist der Import aus fest gebundenen Eingaben reproduzierbar? Werden fachliche Unterschiede wie Ankündigung, Durchführung und Unsicherheit erhalten? Halten Suchdienst und Website den Versionsvertrag ein? Bleiben gewöhnliche Seiten und das Formular bei Suchausfall und Suchlast benutzbar?

Die kleine Fallmenge in `validation-cases.json` ist eine quellenbasierte Ausgangsmenge, kein vollständiger Goldstandard. Sie darf für den technischen Durchstich und die erste fachliche Fehlersuche verwendet werden. Aussagen über allgemeine Suchqualität, nDCG, Recall oder die Überlegenheit einer BM25-, Vektor- oder Hybridkonfiguration setzen den späteren, bewerteten Entwicklungs- und Testsatz voraus.

Der Plan verändert weder das öffentliche Archiv noch Produktionsdienste. Alle Mutationen der Importprüfung finden in Kopien oder eigens erzeugten Fixtures statt. Externe kostenpflichtige Anbieter bleiben ausgeschaltet; ein zählender Ersatzanbieter bildet Embedding-Erfolg, Verzögerung und Fehler deterministisch nach.

## Fest gebundene Prüfgrundlage

Die folgenden Quellen wurden für die Fallauswahl tatsächlich am genannten Stand gelesen:

- Architektur und Entwicklungsplan: `.dev/suche-architektur.html` am Website-Commit `3fd28a9`.
- Veröffentlichte redaktionelle Quellenansichten: `data/quellen.json`, insbesondere die Datensätze `1971-11-06-sounds-take-off-your-head-and-listen`, `1972-10-28-nme-john-st-field-folkclubs`, `1976-01-28-ya-folk-rock-escoces-john-st-field-la-boite`, `1997-04-15-nordlands-framtid-en-poetisk-grisegutt`, `1998-10-23-lofotposten-en-perfekt-kveld`, `2000-03-04-nordlys-grisete-sentimental`, `2007-04-05-musicomh-jackie-leven-troubadour-london` und `2007-09-17-puls-jackie-leven-pa-omfattende-norgesturne` am Website-Commit `3fd28a9`.
- Aktuelle Detaildarstellung: `templates/quelle.gohtml` sowie Routing in `internal/site/content.go` und `internal/site/server.go` am Website-Commit `3fd28a9`.
- Strukturierte Archivdaten: die in `validation-cases.json` genannten Dateien unter `data/document`, `data/event`, `data/person` und `data/persona` am Archiv-Commit `7d353a4`.

Die Website-Datensätze enthalten redaktionelle Zusammenfassungen auf Deutsch und Englisch sowie teilweise ausgewählte Zitate in der Quellsprache. Sie sind nicht mit vollständigen Originalartikeln gleichzusetzen. `source_voice` bezeichnet deshalb die Stimme des historischen Dokuments, während `passage_voice`, `text_kind` und `language` die konkret ausgegebene Textstelle beschreiben. Bei den ausgewählten Pressequellen ist das Dokument `third_party`; eine deutsche oder englische Zusammenfassung ist dagegen `editorial` und `summary`, ein direktes Zitat in der Quellsprache `third_party` und `original`. Eine deutsche Anfrage an ein norwegisches Dokument prüft mit dieser Ausgangsmenge vor allem richtige Dokument-, Sprach-, Textart- und Stimmenzuordnung. Sie beweist für sich allein noch keine rein semantische sprachübergreifende Leistung, wenn eine deutsche Zusammenfassung indexiert wurde.

## Noch fehlende Textstellenkennungen

Am Prüfstand gibt es kein `passages/manifest.txt`, und die Quellen-Detailseiten vergeben keine stabilen Absatzanker. Die vorhandenen Abschnittsanker `#beleg` und `#quelle` bezeichnen ganze Darstellungsabschnitte, nicht die erwarteten zitierbaren Textstellen. Deshalb verwendet die Fallmenge echte Dokumentkennungen, setzt `passage_id` aber ausdrücklich auf `null` und kennzeichnet den Zustand als `not_assigned`.

Vor einem Ende-zu-Ende-Test des Beleglinks muss der Datenvertrag für jeden Pilotbeleg eine stabile Textstellenkennung, Dokumentkennung, Quellart, Sprache, Stimme, Zieladresse und einen tatsächlich vorhandenen HTML-Anker liefern. Erst dann werden die offenen Felder in einem gesonderten, nachvollziehbaren Schritt belegt. Eine aus Dokumentkennung und Absatznummer erratene Kennung ist kein zulässiger Ersatz.

## Prüfumgebungen und Beobachtbarkeit

Die Datenprüfung benötigt nur einen fest gebundenen Export, den Importbefehl, ein leeres isoliertes Datenbankschema und lesenden Zugriff auf Importregister und Suchschema. Der Datenagent soll dafür normalisierte Exporte, Eingabemanifest, Hashregeln und Textstellenmanifest bereitstellen. Der Datenbank- beziehungsweise Suchdienstagent soll Startbefehl, Schemafassung, Readiness-Endpunkt, API-Vertrag und eine Methode zum Abfragen der aktiven Buildkennung liefern. Fehlt eine dieser Beobachtungsmöglichkeiten, ist der entsprechende Test blockiert und nicht stillschweigend bestanden.

Der Ersatzanbieter für Embeddings muss Aufrufe nach Profilkennung und Hash des vollständigen Eingabetexts zählen können. Er speichert keinen echten Suchtext außerhalb des Testlaufs. Für Wiederaufnahmeprüfungen muss sich der Import nach einer festgelegten Anzahl erledigter Elemente kontrolliert beenden lassen. Der Test liest danach Registerzustände und startet denselben Lauf erneut.

Jeder Lauf protokolliert mindestens: Quellrevisionen, Eingabemanifest-Hash, Pipeline- und Profilversion, Lauf- und Buildkennung, Beginn und Ende, Zustandszähler, Ersatzanbieteraufrufe, normalisierten Export-Hash, aktives Schema und Ergebnis jeder Abnahmebedingung. Diese Prüfprotokolle dürfen keine Geheimnisse oder Besuchersuchtexte enthalten.

## Zeitpunkt der Ausführung

Phase 1 liefert mit diesem Dokument und der Fallmenge die geprüfte Testgrundlage. Sie führt mangels implementiertem Import-, API- und Website-Durchstich die nachfolgenden Abnahmetests noch nicht aus. In Phase 2 werden Import, Wiederaufnahme, Änderungen, Löschung, HTTP-Vertrag und der getrennte Prozessausfall geprüft. Phase 3 verwendet die fachlichen Suchfälle für die tatsächliche Rang- und Konfigurationsbewertung; erst dort werden Suchqualitätswerte erhoben. Die Hostlast-, Betriebs- und Rollbackprüfungen gehören zur Betriebsabnahme in Phase 4. Die Kriterien stehen bereits hier, damit Daten- und Suchdienstimplementierung unabhängig gegen dieselben Erwartungen entwickelt werden können.

## Abnahme des Imports

### Reproduzierbarkeit und Idempotenz

1. Derselbe fest gebundene Snapshot wird zweimal in jeweils ein leeres Schema importiert. Beide Läufe müssen denselben normalisierten Export-Hash, dieselbe Mitgliedsliste und fachlich identische Tabelleninhalte erzeugen. Laufkennungen, Zeitstempel und technische Reihenfolgen werden vor dem Vergleich als nichtfachliche Felder ausgeschlossen.
2. Derselbe Snapshot wird anschließend noch einmal gegen den bereits vollständigen persistenten Indexierungsstand verarbeitet. Der neue Lauf darf keine fachlichen Zeilen ändern, keine Duplikate anlegen und beim Ersatzanbieter keinen Embedding-Aufruf für bereits validierte Kombinationen aus Profil und Eingabetexthash auslösen.
3. Die Reihenfolge der Eingabedateien wird in einer Fixture variiert. Normalisierter Export, Mitgliedsliste und Suchergebnis-Tie-Breaks bleiben gleich. Die Pipeline darf sich nicht auf Dateisystemreihenfolge oder Dateiänderungszeiten stützen.

Abnahme: alle drei Vergleiche sind gleich; der zweite Lauf meldet null unnötige Ersatzanbieteraufrufe; eindeutige Schlüssel und Referenzen bleiben gültig.

### Ergänzung, Änderung und Entfernung

Die folgenden Varianten entstehen nur in einer Kopie des Pilotbestands:

- **Ergänzung:** Ein neues freigegebenes Dokument mit neuer echter Fixture-Kennung wird in das Eingabemanifest aufgenommen. Nur dessen abhängige Segmente und fehlende Artefakte kommen hinzu; der vorige freigegebene Build bleibt bis zur Abnahme aktiv.
- **Textänderung:** Der Text einer bestehenden Fixture-Textstelle wird korrigiert. Dokument- und Textstellenkennung bleiben stabil, der Eingabetexthash ändert sich, und nur die abhängigen Segmente erzeugen neue Embedding-Artefakte.
- **Metadatenänderung:** Ein nicht eingebettetes Feld, etwa Beleglocator oder Zieladresse, wird geändert. Lesemodell und Linkziel ändern sich; bei identischem Einbettungstext und Profil bleibt die Zahl neuer Embedding-Aufrufe null. Falls das Feld laut Importvertrag im Kontextkopf liegt, muss es stattdessen ausdrücklich als Textänderung behandelt werden.
- **Abhängige Änderung:** Eine Personenbezeichnung, die in `names` oder Kontextkopf abgeleitet wird, wird in der Fixture geändert. Der Import muss alle abhängigen Segmente neu bestimmen, auch wenn ihre Dokumentdatei unverändert blieb.
- **Entfernung:** Ein zuvor freigegebenes Element fehlt im vollständigen neuen Eingabemanifest beziehungsweise ist ausdrücklich nicht mehr freigegeben. Es fehlt im neuen Build, seine Identitätsverweise und Linkziele werden geprüft, und der alte Build bleibt bis zur Freigabe unverändert. Ein Lesefehler, eine unvollständige Inventur oder ein fehlgeschlagener Import darf nicht als Entfernung gelten. Die Fixture kennzeichnet zusätzlich, ob es sich um eine gewöhnliche Snapshotänderung oder um eine verpflichtende Inhaltsrücknahme handelt.

Abnahme: Der Diff des neuen Builds enthält ausschließlich die erwarteten fachlichen Änderungen. Im neuen Build entfernte Inhalte erscheinen dort weder in Suche noch Auflösung oder Cache. Bei einer gewöhnlichen Snapshotänderung darf ein ausdrücklich freigegebener Rollback auf den älteren Snapshot dessen damalige Mitgliedschaft wiederherstellen. Eine verpflichtende Inhaltsrücknahme sperrt dagegen auch alte Suchstände, gespeicherte Texte, Vektoren und Caches für die Veröffentlichung; kein Rollback darf den zurückgezogenen Inhalt erneut öffentlich machen. Der vorherige Build bleibt bei jedem fehlgeschlagenen Variantenlauf aktiv, sofern er nicht wegen einer solchen Rücknahme gesperrt wurde.

### Abbruch und Wiederaufnahme

Ein Lauf wird nach mindestens einem dauerhaft gespeicherten Artefakt und mindestens einem noch reservierten Element beendet. Nach Ablauf beziehungsweise kontrollierter Freigabe der Reservierung wird dieselbe Laufkennung fortgesetzt.

Abnahme:

- Bereits als `done` bestätigte Arbeit wird nicht erneut ausgeführt.
- Eine abgelaufene `running`-Reservierung wird erneut bearbeitbar; ein alter Bearbeiter kann sie danach nicht widersprüchlich abschließen.
- Ein validiertes Embedding ist vor `done` dauerhaft gespeichert und auf Dimension, endliche Zahlen und Prüfsumme geprüft.
- Wiederholungen sind begrenzt; dauerhafte Fehler enden sichtbar in `failed` statt in einer Endlosschleife.
- Nach Fortsetzung entsprechen Export und Build dem ununterbrochenen Referenzlauf.
- Ein älterer, später fertiggestellter Lauf kann keinen neueren freigegebenen Build aktivieren.

Ein Netzwerkabbruch nach möglicherweise erfolgreicher Anbieterverarbeitung wird gesondert als Grenze dokumentiert: Ohne bestätigte Idempotenz des Anbieters wird kein genau-einmaliger kostenpflichtiger Aufruf behauptet.

## Fachliche Prüfung des Lesemodells

Vor einer Rangbewertung werden die Fälle direkt gegen Export beziehungsweise Datenbank geprüft. Jede erwartete Dokument- und Entitätskennung muss auflösbar sein; referenzierte Belege müssen zum gebundenen Dokument gehören. `announced`, `took_place`, `probable` und `uncertain` bleiben unterscheidbar. Eine Ankündigung darf weder durch das Feld `took_place_at` noch durch eine rangierte Textähnlichkeit als nachgewiesene Durchführung erscheinen.

Beim Bodø-Fall vom April 1997 bleibt der unsichere frühe Datumsstand `[1997-04-05,1997-04-06,1997-04-13]` mit seinem Vorbericht erhalten; die nachträglichen Kritiken belegen den 13. April und die Durchführung. Beim Bodø-Fall vom September 2007 bleiben `Public` und `Sinus` zwei angekündigte, ungeklärte Datensätze. Weder Zusammenführung noch Auswahl einer Spielstätte darf ohne zusätzlichen Beleg erfolgen.

Namen werden ebenfalls quellengebunden geprüft. `Sir Vincent Lone` ist eine Persona, die über die belegte `performs_as`-Aussage mit `person/jackie-leven` verbunden ist. `Kevin O’Foster` ist die Schreibweise der Quelle; das Archiv führt `Kevin O. Foster` als Variante von `person/kevin-foster`. Die Suche darf Varianten auflösen, muss aber im Belegzitat die Quellschreibweise bewahren. Für jeden ausgegebenen Text prüft der Test zusätzlich den in der JSON-Datei referenzierten Stimmenvertrag: Dokumentstimme, Passagenstimme, Textart und Sprache müssen gemeinsam zulässig sein. Eine redaktionelle Paraphrase darf nicht als Originalstimme des Kritikers oder Jackie Levens erscheinen.

## Suchfälle und Bewertung

`validation-cases.json` ist gültiges JSON und enthält pro Fall Anfrageart, fachliche Absicht, tatsächlich geprüfte Quellen, positive beziehungsweise ausgeschlossene Erwartungen und die offene Textstellenlage. Die erwartete Rangstufe `must_return` bedeutet für diesen Pilot: Mindestens ein genanntes Dokument steht innerhalb des angegebenen Grenzwerts, sofern dessen im Fall benannter Text tatsächlich zum Pilotindex gehört. Sie bedeutet nicht, dass alle anderen Treffer irrelevant sind. `must_not_assert` betrifft die fachliche Darstellung unabhängig vom Rang.

Die Fälle werden zunächst gegen BM25 und den deterministischen Namens-/Strukturpfad ausgeführt. Semantische Varianten kommen erst hinzu, wenn ein lokaler Ersatzvektorpfad oder ausdrücklich genehmigte Anbieterprüfung vorhanden ist. Ergebnisse werden mit Konfiguration, Inhaltsversion und Suchrelease gespeichert. Ein fehlendes Pilotdokument ist ein Korpusbefund, kein Nulltrefferbeweis für die Suchtechnik.

Der enge Negativfall behauptet nur, dass die gebundenen Quellen kein stattgefundenes Oslo-Konzert am 27. September 2007 belegen. Das System soll eine leere strukturierte Ergebnismenge oder eine als schwach beziehungsweise unbelegt gekennzeichnete Antwort liefern. Ein beliebiger semantischer Nachbar darf nicht als Tatsache ausgegeben werden.

## HTTP- und Versionsvertrag

Die Vertragstests starten Suchdienst und Website als getrennte Prozesse. Ein Stub kann den jeweils anderen Partner ersetzen, muss aber echte HTTP-Grenzen, Fristen und JSON-Decodierung verwenden.

| Fall | Abnahme |
| --- | --- |
| Gültige Anfrage an `/v1/search` | Status 200; Antwort enthält `api_version`, `data_version`, `content_version`, `search_release`, `mode`, `degraded` und `hits`; Kennungen entsprechen dem gebundenen Readiness-Stand. |
| Echte Nulltreffermenge | Status 200 und `hits: []`; nicht 404 oder 503. |
| Abweichende erwartete Inhaltsversion | Status 409 und stabiler Code `content_version_mismatch`; keine Treffer aus dem fremden Stand. |
| Fremde Inhaltsversion in einer 200-Antwort eines Stubs | Der Website-Client verwirft die Antwort und zeigt keine Treffer an. |
| Nicht unterstützte API-Fassung oder inkompatibler Vertrag | Kontrollierter 4xx-Fehler beziehungsweise fehlgeschlagene Readiness; niemals stillschweigende Interpretation als v1. Das genaue Fehlerformat wird mit OpenAPI festgeschrieben. |
| Embedding oder Reranking fällt aus | Status 200 mit lokal ermittelten Treffern, eingeschränktem `mode`, `degraded: true` und stabilem Grund. |
| Ungültige Anfrage | Status 400 mit stabilem Fehlercode; keine SQL-, Dateipfad- oder Anbieterinterna. |
| Kapazitätsgrenze | Status 429, soweit sinnvoll mit `Retry-After`; begrenzte Warteschlange. |
| Postgres oder Suchdienst nicht erreichbar | Suchweg 503; Website stellt dies nicht als Nulltreffer dar. |
| Zu große, verspätete oder ungültige Dienstantwort | Website-Client bricht innerhalb seines Budgets ab, begrenzt die gelesenen Bytes und zeigt eine verständliche Suchfehlermeldung. |

Jeder Erfolgstreffer wird zusätzlich gegen Dokumentkennung, Stimme, Quellsprache, Textart, Zieladresse und – sobald vorhanden – Textstellenkennung geprüft. HTML und JSON müssen dieselbe fachliche Suchsemantik verwenden; unterschiedliche Oberflächenbudgets werden als Konfiguration ausgewiesen.

## Ausfall- und Lastprüfung

Vor dem Lastlauf werden bei ruhendem Suchdienst Basiswerte für eine gewöhnliche Inhaltsseite und einen lokalen Formularlauf mit Test-Mailtransport erhoben. Der Lastgenerator verwendet markierte synthetische Suchtexte, begrenzte Parallelitätsstufen und keine externen Anbieter. Er steigert die Last bis zur konfigurierten Suchgrenze; eine weitere Stufe prüft kontrollierte 429- beziehungsweise 503-Antworten statt unbegrenzten Wartens.

Parallel werden wiederholt geprüft:

- eine gewöhnliche, dateibasierte Inhaltsseite liefert den erwarteten 200-Status und unveränderten Kerninhalt;
- die Formularseite bleibt abrufbar, CSRF-/Validierungsfehler funktionieren, und eine gültige lokale Testeinsendung erreicht genau einmal den Stub-Mailtransport;
- Website-Prozess und Formular besitzen keine Datenbank- oder Anbieterschlüssel des Suchdienstes;
- es gibt keine Website-Panics, Prozessneustarts oder erschöpften Website-Verbindungspools;
- Suchanfragen halten ihre Gesamtfrist ein oder werden kontrolliert abgewiesen; nach Lastende erholt sich der Dienst ohne manuellen Registereingriff.

Abnahme: Gewöhnliche Seite und Formular haben in jeder Stufe eine Erfolgsquote von 100 Prozent. Ihre p95-Zeiten werden zusammen mit dem unbelasteten Ausgangswert berichtet; eine Freigabeschwelle wird vor dem Lauf als konkretes Hostbudget festgelegt und darf nicht nach Sichtung der Ergebnisse verschoben werden. Ohne vorab vereinbartes Hostbudget ist nur Erreichbarkeit, nicht eine Leistungsfreigabe, abnehmbar. Suchfehler dürfen weder Website noch Formular beenden. Dieselbe Prüfung wird mit beendetem Suchprozess, verweigerter Suchverbindung, ausgefallenem Postgres, langsamem Dienst, ungültigem JSON und ausgefallenem Ersatzanbieter wiederholt.

## Datenschutz- und Negativprüfungen

Ein einmaliger markierter Suchtext wird über HTML- und JSON-Suchweg geschickt. Anschließend werden die für den Test vereinbarten Go-, Proxy-, Datenbank- und Traceprotokolle durchsucht. Der Text darf dort nicht vorkommen; aggregierte Zähler dürfen ihn weder als Label noch als Attribut enthalten. Antworten tragen `Cache-Control: no-store`, HTML-Suchergebnisse zusätzlich `noindex`; die Suchwege verwenden `Referrer-Policy: no-referrer`. Diese Prüfung umfasst nur benannte lokale Protokolle. Eine Aussage über Cloudflare oder Produktion setzt einen eigenen dort ausgeführten Nachweis voraus.

Ungültige Filter, unbekannte Kennungen, SQL-artige Zeichenfolgen, sehr lange Anfragen und abgebrochene Clients werden mitgetestet. `fetch` akzeptiert nur bekannte Archivkennungen. Anfragewerte dürfen weder Schema noch Datenbankrolle wählen. Fehlermeldungen geben keine Geheimnisse, lokalen Pfade oder Rohabfragen aus.

## Bericht und Entscheidung

Der Abnahmebericht nennt für jeden Test `passed`, `failed`, `blocked` oder `not_run`, die genaue Build- und Inhaltsversion, den ausgeführten Befehl und einen knappen Beleg. `blocked` ist erforderlich, wenn Vertrag, Textstellenmanifest, isolierter Cluster oder Beobachtbarkeit fehlen; es ist kein Erfolg mit Einschränkung.

Der Validierungsbeitrag zu Phase 1 ist abnehmbar, wenn:

1. alle in der Fallmenge genannten Website- und Archivkennungen am gebundenen Quellstand geprüft sind;
2. Fallmenge und Plan Textlage, Stimme, Quellsprache, Ankündigung, Durchführung, Datumskonflikte, Namen und Negativfälle ohne erfundene Erwartungen wiedergeben;
3. die künftigen Kriterien für Reproduzierbarkeit, Idempotenz, Wiederaufnahme, Änderung, Entfernung, API-/Inhaltsversion und Betriebsisolierung so beobachtbar formuliert sind, dass Daten- und Suchdienstimplementierung getrennt bewertet werden können;
4. die maschinenlesbare Datei syntaktisch gültig ist und offene Passage-IDs ausdrücklich als offen markiert;
5. noch nicht ausgeführte Tests und verbleibende Blocker nicht als bestandene Prüfungen erscheinen.

Die spätere Erfüllung der in diesem Plan beschriebenen Durchstichkriterien kann erst nach den Ausführungen in Phase 2 bis 4 festgestellt werden. Der Phase-1-Beitrag bestätigt weder einen bereits funktionierenden technischen Durchstich noch vollständige Archivabdeckung, allgemeine Suchqualität oder Produktionsreife.
