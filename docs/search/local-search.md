# Lokale Archivsuche bedienen und entwickeln

Stand: 26. Oktober 2026. Diese Dokumentation beschreibt die implementierte lokale Testfassung. Sie ist keine öffentliche Freigabe und kein Nachweis einer abgeschlossenen Qualitäts- oder Gesamtprüfung.

## Suche öffnen

Die eigenständige Testwebsite ist für diese Adressen eingerichtet:

- Deutsch: <http://127.0.0.1:8082/de/suche-test>
- Englisch: <http://127.0.0.1:8082/en/search-test>

`/de/suche` und `/en/search` zeigen dasselbe Formular. Die Seiten funktionieren ohne JavaScript. Der Suchdienst läuft getrennt auf `127.0.0.1:8081`; seine PostgreSQL-Datenbank ist ausschließlich über `127.0.0.1:55473` erreichbar. Alle drei gehören zur lokalen Entwicklung. Die Testwebsite ersetzt weder den bestehenden Websiteprozess auf Port 8080 noch eine veröffentlichte Website.

Für Suchtests direkt Port 8082 benutzen. Der bestehende Apache-/MAMP-Weg ist dafür nicht vorgesehen: Dort müssen insbesondere die SSL-Zugriffsprotokolle noch so geprüft und angepasst werden, dass Suchtexte nicht über URL-Querystrings protokolliert werden.

## Suchmodi und Filter

| Einstellung | Wirkung |
| --- | --- |
| `lexical` | Wortsuche mit BM25. Geeignet für Namen, Titel und erkennbare Formulierungen. Ohne Reranking braucht diese Suche keinen externen Modellaufruf. |
| `semantic` | Ähnlichkeitssuche mit Qwen-Embeddings. Geeignet für Umschreibungen und inhaltliche Fragen. Bei nicht verfügbarer semantischer Suche kann der Dienst auf Wortsuche zurückfallen. |
| `hybrid` | Verbindet Wortsuche und semantische Kandidaten durch Reciprocal Rank Fusion. Dies ist die Voreinstellung. |
| Reranking | Optionaler zusätzlicher Modellaufruf, der die gefundenen Kandidaten neu ordnet. Die Anzeige „Reranking verwendet“ zeigt, ob er tatsächlich erfolgreich eingesetzt wurde. |

Semantische und hybride Anfragen übertragen den Suchtext an DeepInfra. Angefordertes Reranking überträgt zusätzlich Texte der Kandidaten. Der Hinweis vor dem Formular beschreibt diese Übermittlung. Für Tests ohne externe Übermittlung `lexical` wählen und Reranking ausgeschaltet lassen. Der API-Schlüssel bleibt beim Suchdienst; die Website und der Browser benötigen ihn nicht.

„Textstimme“ filtert `text_voice`: `leven`, `third_party`, `editorial` oder `pastiche`. Die Quellenstimme `source_voice` wird separat angezeigt. Eine redaktionelle Zusammenfassung einer Konzertkritik kann daher die Quellenstimme `third_party`, aber die Textstimme `editorial` tragen. Der aktuelle Export schließt die Pastiche aus; ihr Filter kann entsprechend keine Treffer liefern.

Die Jahresfilter beziehen sich auf das **Erscheinungsjahr des Dokuments**, nicht auf das Datum eines darin erwähnten Konzerts. „Sprache der Zielseiten“ wählt deutsche oder englische Dokumentlinks; sie beschränkt nicht die Sprache der durchsuchten Texte. Die tatsächliche Textsprache steht am Treffer. Eine Anfrage darf höchstens 1024 UTF-8-Bytes enthalten. Das Formular zeigt höchstens 20 Treffer; diese Anzahl ist keine Gesamtzählung aller passenden Dokumente.

Diese Beispiele eignen sich zum Vergleichen der Modi, ohne bestimmte Treffer oder eine vollständige Antwort vorauszusetzen:

| Anfrage | Versuch |
| --- | --- |
| `Doll by Doll` | Zunächst `lexical`, anschließend `hybrid`; Titel und Textstellen vergleichen. |
| `Norwegen` | Wortsuche mit und ohne Textstimmenfilter vergleichen. |
| `Welche Erinnerungen beschreibt Leven an seine Kindheit?` | `semantic` und `hybrid` vergleichen, danach Textstimme `leven` wählen. |
| `Verlust und Trauer` | Inhaltliche Suche mit und ohne Reranking vergleichen. |
| `Fife` | `lexical` suchen und Erscheinungsjahre eingrenzen; die Jahresauswahl nicht als Ereigniszeitraum lesen. |

## Ergebnisse lesen

Maßgeblich ist der **verwendete Modus** in der Ergebnisanzeige, nicht allein die Auswahl im Formular. `degraded`, der angezeigte Grund und `reranked` machen Rückfallbetrieb und ausgebliebenes Reranking sichtbar. Hinzu kommen die Suchdauer, die Version des Suchdienstes und die `content_version` des Inhaltsstands.

Ein Treffer öffnet die gespeicherte Textstelle unter `/de/suche/textstelle?id=…` beziehungsweise `/en/search/passage?id=…`. Dort stehen der vollständige gespeicherte Text, Kennungen, Stimmen, Textart und vorhandene weitere Metadaten. Der Link „Originalseite öffnen“ führt separat zum Dokument. Es werden keine Absatzanker auf der Originalseite erfunden. Der gelesene Suchtext gehört zum gepinnten Inhaltsstand; eine inzwischen geänderte Originalseite muss damit nicht wortgleich sein.

„Keine Textstellen gefunden“ ist ein reguläres Ergebnis. Fehler werden davon getrennt dargestellt:

| Status | Bedeutung |
| --- | --- |
| 400 | Ungültige Anfrage oder Filter. |
| 404 | Die angeforderte Textstelle existiert in diesem Inhaltsstand nicht. |
| 409 | Website und Suchdienst verwenden unterschiedliche Inhaltsstände. |
| 429 | Die begrenzte Suchkapazität ist ausgelastet. |
| 503 | Suche, Datenbank oder interne Verbindung ist nicht verfügbar beziehungsweise die Antwort nicht verwendbar. |

Suchseiten senden `Cache-Control: no-store`, `noindex` und `Referrer-Policy: no-referrer`. Die Go-Komponenten protokollieren keine Suchtexte. GET-Anfragen bleiben dennoch in der Browseradresse sichtbar und können im Browserverlauf stehen. Die normale Website benötigt für ihre übrigen Seiten keine Datenbankverbindung zum Suchdienst.

## Lokale Prozesse verwalten

Die Befehle im Repository-Hauptverzeichnis ausführen. Voraussetzungen sind Go, Python 3, Docker Desktop mit dem Kontext `desktop-linux` und für den persistenten Betrieb die macOS-Benutzersitzung. Das Werkzeug [ops/search/local.py](../../ops/search/local.py) verwaltet ausschließlich die lokale Suchumgebung. Sein Compose-Projekt heißt `jackieleven-search-dev` und besitzt ein eigenes Datenvolume.

Bei bereits importiertem und veröffentlichtem Inhaltsstand:

```sh
python3 ops/search/local.py db-up
python3 ops/search/local.py grant-reader
python3 ops/search/local.py install
python3 ops/search/local.py install-test
```

`grant-reader` setzt die lesende Datenbankrolle auf einem bereits angelegten Suchschema auf. `install` baut den Suchdienst und startet ihn als Benutzer-LaunchAgent. `install-test` baut und startet den separaten Website-LaunchAgent auf Port 8082. Die Prozesse werden durch `launchd` in der Benutzersitzung betreut. Das lokale Startwerkzeug aktiviert den DeepInfra-Zugriff für den Suchdienst; der Schlüssel muss dafür bereits geschützt hinterlegt sein.

Weitere Befehle:

```sh
python3 ops/search/local.py status
python3 ops/search/local.py restart
python3 ops/search/local.py stop-test
python3 ops/search/local.py stop
```

`status` zeigt Datenbank und Suchdienst. `restart` baut und startet den Suchdienst erneut; für die Testwebsite erneut `install-test` verwenden. `stop-test` und `stop` stoppen die jeweiligen geladenen Benutzerjobs, löschen aber weder Datenbank noch Importzustand. Die angelegten LaunchAgent-Dateien bleiben vorhanden. Die Datenbank lässt sich gesondert mit `db-stop` stoppen.

Zur Funktionsprüfung dienen <http://127.0.0.1:8081/healthz> und <http://127.0.0.1:8081/readyz>. `healthz` bestätigt nur den laufenden HTTP-Prozess. `readyz` prüft den gebundenen Datenbestand und die Datenbank, nicht die Verfügbarkeit von DeepInfra. Erst eine Suchanfrage mit Kontrolle von Modus und Rückfallanzeige prüft den gewünschten Suchweg.

Wer die Website unmittelbar als Entwicklungsprozess startet, setzt `JACKIE_SEARCH_URL=http://127.0.0.1:8081` und `JACKIE_SEARCH_MANIFEST` auf den absoluten Manifestpfad. Gleichwertige Website-Flags heißen `-search-url` und `-search-manifest`; `-base-path` unterstützt einen URL-Präfix. Die Website akzeptiert nur einen Loopback-HTTP-Ursprung und folgt keinen Weiterleitungen. Ihr HTTP-Client hat eine Gesamtfrist von elf Sekunden und begrenzte Antwortgrößen.

## Importzustand und Manifestwechsel

Der anfängliche Export liest Website-Revision `ea653b6` und Archiv-Revision `7d353a4`. Dieser ausgewählte Bestand umfasst 572 Dokumente, 7993 Textstellen und 965 Archiv-Entitäten. Die Zahlen beschreiben diesen Export, nicht den Umfang eines vollständig erschlossenen Archivs. Änderungen der Arbeitskopien gelangen nicht automatisch in den Index.

Importdetails und Wiederaufnahme beschreibt [tools/search/README.md](../../tools/search/README.md). Vor dem ersten Import die private Python-Umgebung mit den festgelegten Abhängigkeiten einrichten:

```sh
uv venv .dev/runtime/search/venv
uv pip install --python .dev/runtime/search/venv/bin/python \
  -r tools/search/requirements.txt
```

Der lokale Einstieg ist `index`. Er lädt die private Datenbankkonfiguration und gibt dem Importer den geschützten Schlüsseldateipfad mit; Zugangsdaten müssen nicht in Shellbefehle kopiert werden. Das Archiv wird standardmäßig im Nachbarverzeichnis `../jackieleven-archive` erwartet.

```sh
python3 ops/search/local.py index --plan
python3 ops/search/local.py db-up
python3 ops/search/local.py index --workers 4
```

`--plan` schreibt bereits den privaten Export und das Kennungsregister, erzeugt aber keine Embeddings und führt keine Datenbank- oder Provideraufrufe aus. Ohne `--plan` erzeugt `index` standardmäßig Embeddings; bis zu vier Batches werden gleichzeitig verarbeitet. `--workers 1` reduziert die Parallelität. Für einen Stand ohne Embeddings:

```sh
python3 ops/search/local.py index --lexical-only
```

Neue Quellstände ausdrücklich festlegen, beispielsweise zunächst für eine Planung:

```sh
python3 ops/search/local.py index --plan \
  --website-revision ea653b6 --archive-revision 7d353a4
```

Die beiden Revisionen durch die gewünschten, vorhandenen Git-Revisionen ersetzen und für den anschließenden Import dieselben Argumente ohne `--plan` verwenden. Nach dem ersten Import `grant-reader`, `install` und `install-test` wie oben ausführen. Keine Schlüsseldatei ausgeben, keine DSN mit Passwort in Befehlsargumente kopieren und weder Zugangsdaten noch privaten Laufzeitbestand committen.

Der dauerhafte private Zustand liegt unter `.dev/runtime/search/`: insbesondere `registry.sqlite3`, die wiederverwendbaren Vektoren unter `artifacts/`, die kanonischen Exporte unter `exports/` und `manifest.json`. Hinzu kommen die Datenbanktabellen für Importfortschritt und veröffentlichte Builds. Das Kennungsregister, die Artefakte, aufbewahrte Manifeste und das Datenbankvolume gehören zusammen in die Sicherung. Sie sind keine wegwerfbaren Builddateien. Ein unterbrochener Import kann mit denselben Eingaben wiederholt werden; bereits validierte Artefakte werden wiederverwendet.

Der Importer ersetzt das Manifest erst nach einem fertigen Datenbank-Build. Website und Suchdienst lesen es **nur beim Start** und halten danach ihren Inhaltsstand fest. Nach jedem Manifestwechsel deshalb beide Prozesse neu starten:

```sh
python3 ops/search/local.py install
python3 ops/search/local.py install-test
```

Anschließend `readyz` und eine Suche kontrollieren. Solange erst ein Prozess den neuen Stand geladen hat, kann die Website 409 melden. Für ein Rollback ein zuvor gesichertes Manifest wieder als aktives Manifest bereitstellen und dieselben beiden Befehle ausführen. Der dazugehörige frühere Build muss noch in der Datenbank vorhanden sein; ein altes Manifest allein stellt keine gelöschten Daten wieder her.

## Grenzen und weitere Prüfung

Die Suche liefert Textstellen aus dem ausgewählten Bestand. Sie beantwortet keine Vollständigkeitsfragen wie „alle belegten Konzerte in Norwegen 2004“ und erzeugt keine belegte Gesamterzählung. Archiv-Entitäten bleiben als strukturierte Daten erhalten; daraus folgt noch keine vollständig ausgebaute Suche über sämtliche Aussagen und Beziehungen.

Semantische Ähnlichkeit ist kein Beleg für sachliche Richtigkeit. Eine brauchbare Bewertung braucht nachvollziehbare Anfragen, relevante Textstellen und einen getrennten Testsatz. Die Beispiele oben sind Bedienbeispiele, keine abgeschlossene Evaluation. Laufzeiten, Rückfallhäufigkeit und Trefferqualität müssen am realen Bestand gemessen werden. Provideraufrufe können kostenpflichtig sein; Modellverfügbarkeit und Laufzeiten sind nicht durch die lokale Datenbank abgesichert.

Der lokale Startweg aktiviert den lesenden MCP-Endpunkt `http://127.0.0.1:8081/mcp` mit den Werkzeugen `search`, `get_passage` und `get_entity`. Auch dort gelten Inhaltsstand, Stimmen und die genannten externen Übermittlungen. Das ist kein Nachweis der Kompatibilität mit einem öffentlichen OpenAI-Connector. Eine Anbindung externer Assistenten, öffentliche Erreichbarkeit, Proxy- und Zugriffsprotokolle sowie ein öffentlicher Betrieb benötigen eine eigene Freigabe und Prüfung. `noindex` und Loopback-Adressen sind kein Ersatz für diese Arbeit. Der verbindliche technische Schnittstellenvertrag steht in [implementation-contract.md](implementation-contract.md).

`local.py index` sichert veröffentlichte Manifeste zusätzlich unter `.dev/runtime/search/manifests/<content_version>.json`. Für einen lokalen Rollback bei unverändertem Website-Inhalt das gewünschte Manifest nach `manifest.json` kopieren, dann `install` und `install-test` ausführen. Dazu müssen die alten Datenbankzeilen erhalten bleiben. Bei geändertem Website-Inhalt gehört auch dessen passende Revision zum Rollback.

Funktions- und Ausfallprüfung: `python3 ops/search/check.py` beziehungsweise `python3 ops/search/check-failures.py`. Mit `check.py --external` werden zusätzlich echte Anbieteraufrufe geprüft. Ein externer Ausfall kann diese ausdrücklich strenge Prüfung fehlschlagen lassen, während die Oberfläche korrekt Rückfallbetrieb anzeigt. Ergebnisse und fachliche Grenzen stehen im [Abnahmebericht](acceptance.md).

## Öffentliche Vorschau

Die gruppierte Oberfläche, der vollständige veröffentlichte Datenbestand und
der getrennte Betrieb auf Hetzner sind in [staging-search.md](staging-search.md)
beschrieben. Die technische Testseite bleibt lokal unter `/de/suche-test` bzw.
`/en/search-test`; `/de/suche` und `/en/search` zeigen die öffentliche Ansicht.
