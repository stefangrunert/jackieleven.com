# Entwurf: Dokument-, Textstellen- und Importvertrag

Stand 26. Oktober 2026. **Vorschlag für die gemeinsame Festschreibung vor Phase 2**, kein bereits implementiertes Exportformat. Grundlage sind die beiden im [Pilotmanifest](pilot-manifest.json) fixierten Git-Revisionen und die Architektur in `.dev/suche-architektur.html`. Der Pilot darf gegen diesen Entwurf geprüft werden; er ist selbst kein vollständiger Importrelease.

## Identität und Stimme

Ein Archivdokument ist das bibliografische Original: etwa die Guardian-Kritik. Die deutsche Zusammenfassung dieser Kritik ist redaktioneller Website-Text. Eine deutsche oder englische Zusammenfassung darf deshalb weder die Originalsprache noch die Stimme ihres Quelldokuments erben.

| Objekt | Erforderliche Felder im vorgeschlagenen Export | Bedeutung |
|---|---|---|
| `document` | `id`, `source_voice`, `document_type`, `title`, `original_language`, `source_inputs`, `source_access`, `rights`, `date_assertions` | `id` entspricht einer vorhandenen Archivkennung; Website-Kolumnen müssen zuvor ausdrücklich zugeordnet/neu erfasst werden. Zugang und Rechte bleiben getrennt. |
| `text_version` | `id`, `document`, `language`, `text_kind`, `text_voice`, `version_group`, `source_input`, `source_selector`, `raw_text_sha256` | Eine konkrete Fassung: Original, Übersetzung oder Zusammenfassung. `text_voice`: `leven`, `third_party`, `editorial`, `pastiche`. Im Phase-1-Manifest steht dieser Wert an jeder Einheit unter `text_units.text_voice`. |
| `passage` | `id`, `document`, `text_version`, `text`, `source_selector`, `raw_text_sha256`, `display_text_sha256`, `target`, `status` | Zitierbare, eigenständig identifizierte Stelle; Text und Ziel müssen im veröffentlichten Inhaltsstand übereinstimmen. |
| `evidence` | `subject`, `statement_id`, `predicate`, `reference_index`, `document`, `evidence_type`, `locator`, `quote`, `passage`, `binding_status` | Aussage und Quelle bleiben unverändert nachvollziehbar. `passage=null` ist zulässig, bedeutet aber „nicht präzise auflösbarer Beleg“. |
| `segment` | `id`, `document`, `text_version`, `passages`, `text`, `language`, `text_kind`, `text_voice`, `retrieval_profile` | Abgeleitete Indexeinheit. Keine Grenzen zwischen Dokumenten, Stimmen, Sprachen oder Fassungen überschreiten. |

`source_voice` beschreibt das Originaldokument; `text_voice` den tatsächlich gesuchten Text. Die Treffergruppe folgt `text_voice`. Der Quellenhinweis nennt zusätzlich das Original und seine Stimme. DE/EN-Zusammenfassungen erhalten gemeinsam eine `version_group`; der Gruppenwert behauptet keine Satz-für-Satz-Übersetzung. Originalzitat und seine ausdrücklich vorhandenen Übersetzungen teilen eine andere Gruppe. Auf DE- und EN-Seiten identisch dargestellte Originalzitate sind dieselbe Textfassung mit zwei Zielseiten, keine zwei Indexkopien.

Ein von einem Journalisten wiedergegebener Leven-Satz bleibt zunächst `third_party` als überliefernde Textstimme. `asserted_by`/Sprecher, Vermittlung und Archivbelegtyp werden separat erhalten; nicht jedes Zitat in einer Konzertkritik wird dadurch zur unmittelbar vorliegenden Selbstaussage. Pastiche wird nie Beleg einer historischen Aussage. Ihre spätere Aufnahme in die Suche bleibt offen und ist im vorliegenden Pilot nicht enthalten.

Datum ist kein einzelnes aus dem Dateinamen abgeleitetes ISO-Feld: Publikation, Archivaufnahme und Ereigniszeit sind getrennte Aussagen. EDTF-Unsicherheit, alternative Werte, `rank`, `certainty`, Notizen und Belegtypen bleiben erhalten. Fehlender Rang bedeutet laut Archivschema `normal`, nicht `preferred`; fehlende Gewissheit bedeutet unbekannt. Ein Datensatzname wie `event/1981-06-08-...` hebt das tatsächliche `1981-06-08?` nicht auf. Ein Status `announced` wird nicht zu `took_place`.

## Stabile Textstellen, wechselnde Segmente

Das Archivschema erwartet `document/<key>#<passage>`. Vorgeschlagen ist ein dauerhaft gepflegtes Sidecar-Verzeichnis mit einer Kennung `p-<opaque-id>` je semantisch zusammengehöriger Textstelle. Es liegt versioniert neben den Importdaten; wo es endgültig gepflegt wird, ist vor Phase 2 mit dem Archivverantwortlichen festzulegen. Diese Phase schreibt nicht in das Archiv.

Die 119 `proposed_passage_ref` im Manifest sind **reservierbare Entwurfskennungen**, keine vorhandenen Archivverweise, HTML-Anker oder öffentlichen `/id/`-Adressen. Für eine nachvollziehbare Erstvergabe wurden UUIDv5-Werte aus Dokumentkennung und damaligem JSON-Pointer beziehungsweise Zeilenbeginn abgeleitet (URL-Namespace; die ersten 20 Hexzeichen nach `p-`). Die genaue Regel steht im Manifest. Nach Annahme werden diese IDs im Register eingefroren. Sie dürfen bei einer späteren Verschiebung oder Korrektur ausdrücklich **nicht erneut aus Position oder Inhalt berechnet** werden. Kollisionen sind beim Einlesen ein Fehler; IDs werden nie wiederverwendet.

Zu jeder Registerzeile gehören aktuelle Quellselektoren, Fassung, vollständiger Text-/Kontexthash, Vorher-/Nachher-Kontext, Änderungsgrund und gegebenenfalls Vorgänger/Nachfolger. Reine Tippfehlerkorrektur oder Verschiebung erhält nach Zuordnungsprüfung die ID und erhöht ihre Inhaltsrevision. Ein sachlicher Ersatz, eine Teilung oder Zusammenführung bekommt neue IDs; alte IDs bleiben als Tombstones mit genau beschriebenen Nachfolgern erhalten. Mehrdeutige Zuordnungen werden zur Prüfung angehalten. Gleicher Text an zwei Orten ist kein Beweis derselben Textstelle. Vorhandene Belege müssen nach sachlichen Textänderungen neu geprüft werden.

Suchsegmente erhalten eigene, neu berechenbare IDs aus Dokument/Fassung, geordneter Passage-Mitgliedschaft, Segmentierungsprofil und normalisiertem Segmenttext. Ein neuer Zuschnitt verändert nur Segmente, nicht Passage-IDs. Die Zielgröße 150–400 Tokens aus dem Architekturentwurf gehört ins Segmentierungsprofil, nicht in die historische Identität eines Absatzes.

## Belegbindung und Zielvertrag

Das Phase-1-Manifest enthält 48 ausgewählte Belegverweise auf 42 unterschiedliche Aussagen, **keinen vollständigen Graphenexport**. Die Auswahl beschränkt sich auf Ereigniszeit, Spielstätte und Durchführungsstatus, jeweils für die ausgewählten Dokumente. Zwölf Verweise enthalten ein Zitat, das als exakte Teilzeichenkette in einem vorhandenen Originalauszug vorkommt; `candidate_passage_refs` hält diese Kandidaten fest. Das beweist Textübereinstimmung, noch nicht, dass der zitierte Satz die ganze Aussage trägt. Alle Bindungen bleiben `unbound`/`needs_semantic_review`. Ohne Zitat wird keine Bindung aus bloßer Themenähnlichkeit erzeugt. Auch eine redaktionelle Zusammenfassung ersetzt nicht die Originalfundstelle eines Archivbelegs.

Der vollständige Phase-2-Export muss alle Aussagen mit Rang, Gewissheit und sämtlichen Referenzen des vereinbarten Teilgraphen mitführen. Die im Pilot enthaltenen ganzen Entitätsdateien sind dafür Prüfgrundlage, nicht die Anweisung, deren gesamtes Umfeld ungeprüft zu veröffentlichen. Externe Graphabhängigkeiten werden entweder als eindeutig markierte Metadaten-Stubs mit IDs/Labels geladen oder explizit als außerhalb des Pilotumfangs ausgewiesen. Kein stilles Weglassen konkurrierender Datumsaussagen wie bei Bodø 1997 oder Marquee 1980.

`target` enthält sprachabhängige, produktionsrelative Pfade ohne Host und ohne Vorschaupräfix, einen tatsächlichen HTML-Anker und die gebundene Inhaltsversion. Der Website-Client setzt sein Präfix genau einmal davor. Er wählt eine passende UI-Sprache, verändert aber nicht die Sprache der zitierten Passage. Bei fehlender Übersetzung darf die vorhandene Originalfassung angezeigt werden, mit deren tatsächlicher Sprache. Seitenanker können nur als Abschnittspräzision deklariert werden; sie sind keine Absatzbelege.

Die derzeit vorhandenen Ziele im Manifest sind anhand von Router, Katalog und Vorlagen geprüft. Detailseiten bieten keine Absatzanker. Phase 2 muss `id="p-..."` an der tatsächlich gerenderten Stelle aus demselben Sidecar einfügen und per HTTP/DOM prüfen. Das gilt auch für Originalzitate, deren Duplikate der aktuelle Renderer unterdrückt. D02 enthält deshalb die zwei `beleg`-Originale und ihre Übersetzungen, nicht zusätzlich deren identische `zitate`-Einträge.

D04 besitzt wegen `stufe=weitere` keine Detailseite. Sein angegebenes Katalogziel mit `?auswahl=0#...` bezeichnet Metadaten innerhalb eines zunächst geschlossenen `<details>`-Elements; es ist kein lesbarer Textstellenbeleg. Es bleibt aus dem Passageindex ausgeschlossen. Bei D15/D16 fehlt noch die bestätigte Archiv-Dokumentidentität. Bis zu deren Zuordnung scheitert ein strikt archivkompatibler Import dieser zwei Kandidaten bewusst; Phase 1 erfindet keine bestehenden Dokumente.

## Eingabemanifest und reproduzierbarer Import

Ein künftiger Importlauf bindet `format_version`, beide vollständigen Git-Commits, eine explizite Dateipositivliste mit Byte-SHA-256, das Textstellenregister, Exporter-/Extraktions-/Normalisierungs-/Segmentierungsprofile sowie das optionale Embedding-Profil. Lokale Pfade sind Messorte, keine transportablen Identitäten. Der Prüfer nimmt `--website-root` und `--archive-root`; maßgeblich sind Git-Revision, relativer Pfad und Hash. Der Produktionsimport nimmt nur freigegebene Snapshots, keine wechselnden Arbeitsdateien.

Für Quellintegrität wird nichts normalisiert: Datei-SHA-256 über Bytes; JSON-Feldhash über den exakten dekodierten String in UTF-8; Markdown-Zeilenauswahl über inklusive Zeilen, verbunden mit LF ohne abschließendes LF. Das Manifest verwendet diese Regeln. Ein späterer `display_text_sha256` entsteht erst aus dem exakt definierten Website-Textadapter; Markdown-Auszeichnung, Navigation und Überschriften dürfen nicht versehentlich mitindexiert werden. Der Importer muss denselben Lesetext wie `LoadColumns`/`ColumnReadingText` und dieselben Duplikatregeln wie `templates.go` erhalten. Dafür noch keinen eigenen heuristischen Parser als verbindlich erklären.

Für einen normalisierten Export gilt: UTF-8, festgeschriebene Unicode-Regel, explizite Nullwerte, sortierte Objektschlüssel und deterministische ID-Sortierung der Mengen; Reihenfolgen mit Bedeutung (Absätze, Segmentpassagen, Referenzpositionen) bleiben unverändert. Die kanonische Serialisierung samt Testvektoren wird vor Phase 2 festgelegt. Zeitstempel und lokale Pfade gehören nicht in die Inhaltsidentität. Ein identischer Eingabesnapshot muss byteidentischen kanonischen Export liefern; externe Vektoren werden als Artefakte aufbewahrt und nicht als deterministisch neu erzeugbar vorausgesetzt.

| Änderung | Zu invalidierende Ableitungen | Wiederverwendbar |
|---|---|---|
| Passagewortlaut/Extraktion | Textrevision, Segmentzuschnitt, lexikalischer Index, betroffene Embeddings | Unveränderte andere Segmente |
| Autor/Datum/Quelltitel im Kontextkopf | Metadaten, Anzeige, tatsächlicher Embedding-Eingabetext | Vektoren nur, wenn der gesamte Eingabetext gleich bleibt |
| Entitätslabel/Alias/Beleg/Rang | Entitäts-/Belegexport, Filter, Anzeige; Kontextabhängigkeiten prüfen | Textvektoren ohne betroffene Eingabefelder |
| Nur Websitepfad/Anker | Zielzuordnung und Website-Inhaltsmanifest, Linkprüfung | Vektoren und unveränderte Segmenttexte |
| Segmentierungsprofil | Segmente und betroffene Indexeinträge | Textstellenregister; identische Embedding-Eingaben |
| Modell/Revision/Tokenizer/Pooling/Instruktion/Kürzung/Normierung/Anbieter | Neues Embedding-Profil und kompatibler Suchstand | Quelltexte/Belege; alte Artefakte für Rollback |
| Entfernung | Mitgliedsliste des neuen Builds; Tombstones/Belegprüfung | Aktiver alter Build bis zum freigegebenen Wechsel |

Die Abhängigkeiten bilden einen gerichteten Graphen: Eingabedateien → Dokument/Fassung/Beleg/Entität → Passagen → Segmente/Kontextkopf → Artefakte → Build. Ein Dateiwechsel löst Auswahl und Hashvergleich aus; er erzwingt nicht pauschal Embeddings für alle Einträge der großen `quellen.json`.

Das dauerhafte Register folgt der Architektur: `runs`, `run_items`, `artifacts`, `builds` außerhalb unveränderlicher Release-Schemas. Ein Item durchläuft `pending → running → validated`, andernfalls `retryable_error` oder `blocked`; `running` benötigt Lease und begrenzte Wiederholung. Artefakte werden zuerst unter temporärem Namen geschrieben, in Dimension/Profil/Prüfsumme geprüft und atomar registriert. Nach Absturz darf eine abgelaufene Lease Arbeit freigeben; bereits validierte Artefakte werden wiederverwendet. Ein bezahlter Anbieteraufruf, dessen Antwort vor sicherer Speicherung verloren geht, kann ohne Anbieter-Idempotenz erneut Kosten erzeugen: kein unbelegtes Exactly-once-Versprechen.

Ein Build nennt seine vollständige Mitgliedsliste, Inhaltsversion, Exporthash, Profile, Schemaformat, kompatible API-Fassung und Freigabestatus. Aktivierung erfolgt erst nach vollständiger Prüfung atomar; fehlgeschlagener Aufbau berührt den aktiven Build nicht. Website und Suchdienst müssen dieselbe freigegebene Kombination aus Texten, Passagen und Zielen bestätigen. Ohne diese Bindung keine Readiness. Ein vollständiger, fehlerfrei enumerierter Snapshot ist Voraussetzung für Löschungen; eine unerreichbare Quelldatei ist kein Löschauftrag.

## Vor Phase 2 festzuschreiben

1. Registerort und formale Bestätigung der vorgeschlagenen Passage- und Kolumnenkennungen.
2. Verbindliches JSON-Schema, kanonische Serialisierung und Textadapter inklusive Stimmen-/Sprachtestfällen.
3. Vollständiger Pilot-Teilgraph mit Stubs, allen konkurrierenden Aussagen und geprüften Belegbindungen.
4. Veröffentlichung der Absatzanker und HTTP-Prüfung einschließlich Vorschaupräfix, Sprachen und D04-Ausschluss.
5. Wiederaufnahme-, Ergänzungs-, Korrektur-, Löschungs- und Fehlbuildtests ohne Anbieteraufrufe; Embedding-Cache erst später mit freigegebenem Profil.
