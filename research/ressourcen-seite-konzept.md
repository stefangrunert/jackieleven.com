# Konzept: Seite mit externen Quellen

Stand: 23. Oktober 2026. Arbeitsgrundlage für eine öffentliche Seite mit Stimmen über Jackie Leven aus externen Quellen: Interviews, Rezensionen, Konzertberichte, Porträts, Nachrufe, Erinnerungen, Radio/TV, Bücher, Foren. Das Material entsteht in `research/quellen/` (eine Datei je Quelle, YAML-Kopf, eigene Inhaltsangabe). Diese Datei legt fest, wie daraus die Seite wird. Erste Fassung gebaut am 23.10.2026 (`/de/stimmen`, siehe README); offen sind englische Texte, Volltexte und Ausschnitte der frei lizenzierten Artikel, „Was fehlt“ und die redaktionelle Sichtung der Stufen.

## Entscheidungen

- **Hauptachse: Zeitstrahl.** Wie die Diskographie: Jahresleiste von 1978 bis heute, darin die Quellen, filterbar nach Art, Sprache und Zugänglichkeit. Die Seite erzählt so, wie Jackie über die Jahre gesehen wurde, und passt zu Zeitreise und Diskographie.
- **Drei Stufen statt alles oder nichts.**
  - *Ausgewählt* (etwa 20–30): die aufschlussreichsten Quellen, hervorgehoben im Zeitstrahl und mit ausführlicher Detailseite.
  - *Verzeichnis*: alle weiteren belastbaren Quellen mit Kurztext und Detailseite.
  - *Weitere Quellen*: weniger aufschlussreiche Einträge (Kurzmeldungen, Ankündigungen, Listen, beiläufige Erwähnungen) der Vollständigkeit halber, je Jahr eingeklappt, ohne eigene Detailseite.
  - *Intern*: bleibt in `research/` – unsichere Zuordnungen, reine Suchprotokolle, Forenbeiträge Privater mit Namen, interne Anmerkungen.
- **Sprachen: Deutsch und Englisch für alle eigenen Texte.** Kurztext und Inhaltsangabe entstehen in beiden Sprachen. Zitate und Volltexte bleiben im Original.
- **Norwegische Zeitungsartikel unter CC BY-NC-ND.** Die Nationalbibliothek gibt viele Ausgaben unter dieser Lizenz frei (Beispiel: [Bergensavisen, 26.10.1998](https://www.nb.no/items/URN:NBN:no-nb_digavis_bergensavisen_null_null_19981026_72_289_1); in der Katalog-API als `accessInfo.license: "ccbyncnd"`, `accessAllowedFrom: "EVERYWHERE"`). Daraus folgt:
  - Volltext und Zeitungsausschnitt dürfen unverändert gezeigt werden, ganz oder in Teilen, mit Namensnennung (Autor, Zeitung, Datum, Link zur Nationalbibliothek, Lizenzname mit Link).
  - Nur nicht kommerziell: Die Seite bleibt ohne Werbung und Verkauf; vor jeder Änderung daran die Lizenzlage neu prüfen.
  - Keine Bearbeitung: **keine Übersetzung des Volltexts veröffentlichen.** Unsere Inhaltsangabe in eigenen Worten ist erlaubt und ersetzt die Übersetzung. OCR-Fehler zu korrigieren, damit der Text dem Original entspricht, ist keine Bearbeitung.
  - Die Lizenz gilt je Ausgabe, nicht pauschal: Sie wird für jede Fundstelle über die API geprüft und gespeichert. Ohne Lizenz gilt die normale Regel (Inhaltsangabe, kurzes Zitat, Link).
  - Prüfung vom 23.10.2026 über alle 1.691 NB-Fundstellen in `research/quellen/` (einschließlich Sammeldateien): 652 CC BY-NC-ND, 123 CC BY-NC, 894 urheberrechtlich geschützt (nur in der Bibliothek bzw. in Norwegen lesbar), 20 „Bokhylla“ (nur Norwegen), 2 ohne Antwort.
  - Frei sind vor allem Regionalzeitungen von Amedia und Polaris (Bergensavisen, Drammens Tidende, Nordlys, Tromsø/iTromsø, Lofotposten, Østlendingen, Halden Arbeiderblad, Nordlands Framtid, Varden, Nordlandsposten, Haugesunds Avis, Dalane Tidende). Geschützt sind die großen Blätter: Dagbladet, Bergens Tidende, Adresseavisen, Aftenposten, VG, Stavanger Aftenblad, Fædrelandsvennen.
  - **CC BY-NC** (Dagsavisen, Rogalands Avis, Arbeiderbladet, Fremtiden) erlaubt Bearbeitungen: Hier dürfen wir Übersetzungen veröffentlichen, gekennzeichnet als Übersetzung mit Hinweis auf die Änderung.
- **Alle übrigen Quellen:** eigene Inhaltsangabe, höchstens kurze Zitate mit Quellenangabe, Link zum Original und, wo nötig, zum Webarchiv. Bezahlschranke und Verlust werden gekennzeichnet.

## Aufbau der Seite

**Übersicht** (`/de/stimmen` bzw. `/en/voices`, Name noch offen):
- Einleitung mit Zahlen und Hinweis auf die Herkunft (eigene Zusammenfassungen, Originale verlinkt).
- Jahresleiste links, wie in der Diskographie; Filter für Art, Sprache und Zugänglichkeit (Volltext hier · online · nur im Archiv · Bezahlschranke · verloren).
- Je Jahr: ausgewählte Quellen als größere Karten, das Verzeichnis als kompakte Zeilen (Datum · Medium · Art · Sprache · Titel · ein bis zwei Sätze), darunter eingeklappt „Weitere Quellen (n)“.
- Ohne JavaScript bleibt alles lesbar; Filter erhalten Leseposition und Sprachwechsel wie in der Diskographie.

**Detailseite je Quelle** (`/de/stimmen/1998-03-06-nordlys-live-med-leven`):
- Kopf: Titel im Original, Medium, Autor, Datum, Art, Sprache, Zugänglichkeit.
- Inhaltsangabe (DE/EN), Zitate im Original, bei Ausgewählten auch „Was man hier erfährt“ (neue Fakten, Anekdoten).
- Bei CC-lizenzierten Artikeln: Originaltext (korrigierte OCR) und Zeitungsausschnitt als lokales Bild, darunter die Namensnennung mit Lizenz.
- Links: Original, Webarchiv, Nationalbibliothek; Bezüge zu Ausgaben der Diskographie, Stationen der Zeitreise, Deep-Pool-Kolumnen und Konzerten.
- Zeitstrahl-Navigation zur vorherigen und nächsten Quelle wie bei den Ausgaben.

**Was fehlt:** die verlorenen Spuren aus `research/quellen/verlorene-spuren.md` als eigener Abschnitt, mit Aufruf zur Mitarbeit („Wer hat MOJO Nr. 43?“) und Link auf `/de/mitmachen`.

**Verknüpfung mit bestehenden Seiten:**
- Ausgabenseiten der Diskographie bekommen „Pressestimmen“: die Rezensionen zu dieser Ausgabe (Zuordnung über die Albumtitel im Feld `thema`, von Hand geprüft).
- Zeitreise-Stationen verweisen auf passende Quellen, die Station 2011 auf die Nachrufe.

## Datenmodell

`research/quellen/` bleibt die interne Recherchebasis. Ergänzt werden redaktionelle Felder im YAML-Kopf:

| Feld | Inhalt |
|---|---|
| `stufe` | `auswahl` · `verzeichnis` · `weitere` · `intern` |
| `kurz_de`, `kurz_en` | ein bis zwei Sätze für Übersicht und Karten |
| `inhalt_en` | englische Fassung der Inhaltsangabe |
| `ausgaben`, `stationen`, `kolumnen` | Bezüge über die IDs der Website |
| `lizenz` | z. B. `cc-by-nc-nd` mit Prüfdatum; leer = keine freie Lizenz |
| `volltext` | Pfad zum korrigierten Originaltext, nur bei freier Lizenz |
| `ausschnitt` | Bildregion der Seite (IIIF-Koordinaten), nur bei freier Lizenz |

Ein Werkzeug (`werkzeug/quellen.php`) erzeugt daraus `app/data/quellen.json` mit ausschließlich öffentlichen Feldern; interne Abschnitte (Widersprüche, Fundweg, Sicherheit) gelangen nie auf die Seite. Ein Prüfskript stellt sicher: keine interne Quelle öffentlich, jede CC-Quelle mit vollständiger Namensnennung, kein übersetzter CC-Volltext, Bilder lokal und mit `loading="lazy"`, keine externen Anfragen beim Seitenaufruf.

## Arbeitsschritte

1. Recherche abschließen (läuft), Index und Spurenliste übernehmen.
2. Lizenzen der norwegischen Fundstellen per API prüfen und eintragen.
3. Sichtung: Stufe je Quelle, Auswahl der hervorgehobenen Quellen, Bezüge zu Ausgaben und Stationen.
4. Texte: Kurztexte DE/EN, englische Inhaltsangaben.
5. Volltexte der CC-Artikel: OCR abrufen, gegen das Seitenbild korrigieren, Ausschnitte als WebP anlegen.
6. Seite bauen: Übersicht, Detailseiten, Filter, Verknüpfungen, Prüfskript.

## Offen

- Name der Seite (Vorschläge: „Stimmen“ / „Voices“, „Echo“, „Presse & Stimmen“).
- Umgang mit Gästebuch und Foren: Kondolenzen und Beiträge Privater nur zusammengefasst oder ohne Namen; einzelne Personen nur mit Einverständnis.
- Darstellung der Bücher (65 Einträge, oft nur Erwähnungen): eher unter „Weitere Quellen“.
