# Auftrag: Quellensammlung zu Jackie Leven fortsetzen

Dieses Dokument ist eine vollständige Arbeitsanweisung. Lies es ganz, bevor du anfängst.

## 1. Worum es geht

Das Repository ist eine private PHP-Website „Jackie Leven · Hommage“. Jackie Leven (geb. Alan Moffatt, * 18.06.1950 Kirkcaldy/Fife, † 14.11.2011) war ein schottischer Songwriter: um 1971/73 das Album „Control“ unter dem Namen John St. Field, ca. 1975/77–1983 Sänger von Doll by Doll, ab 1994 Solokarriere bei Cooking Vinyl, dazu das Fanclub-Label Haunted Valley, die Pseudonyme Sir Vincent Lone und Jackie Balfour und die Zusammenarbeit mit Ian Rankin („Jackie Leven Said“). Seine wichtigsten Märkte waren Großbritannien, Deutschland und Norwegen.

Für eine spätere **Ressourcen-Seite** sammeln wir externe Quellen über ihn: Interviews, Kritiken, Konzertberichte, Nachrufe, Erinnerungen von Fans und Weggefährten, Forenbeiträge, Radio- und TV-Beiträge, Nachschlagewerke, Bücher. **Die Seite wird jetzt nicht gebaut.** Deine Aufgabe ist nur, weitere Quellen zu finden und als Textdateien abzulegen.

Eine erste Runde hat am 23.10.2026 **694 Quellen** in `research/quellen/` angelegt. Sie war durch ein knappes Suchkontingent ausgebremst; mehrere Bereiche sind kaum abgesucht (Abschnitt 5). Diese Lücken sollst du schließen.

## 2. Was du zuerst lesen solltest

1. `research/quellen/README.md` – Format, Methode, Funde und die Übersichtstabellen aller vorhandenen Quellen.
2. `research/quellen/verlorene-spuren.md` – was gesucht und nicht gefunden wurde, gesperrte Bestände, Lücken. **Deine wichtigste Arbeitsliste.**
3. `research/quellen/index.json` – alle vorhandenen Einträge maschinenlesbar. Damit prüfst du vor jedem Anlegen, ob es die Quelle schon gibt.
4. Bei Bedarf die Hintergrundrecherche `research/README.md`, `research/05-diskografie.md` (alle Veröffentlichungen), `research/10-konzertkalender.md` (Auftritte – hilft bei Konzertberichten), `research/02-doll-by-doll.md`.

`research/` ist per `.htaccess` nicht öffentlich. Die Dateien in `research/01–12`, `research/columns/` und `research/youtube-fundliste.*` **nicht ändern**.

## 3. Ablageformat (verbindlich)

### Ordner

Eine Markdown-Datei je Quelle in `research/quellen/<kategorie>/`:

| Ordner | Inhalt |
|---|---|
| `nachrufe` | Nachrufe, Todesmeldungen, Gedenk- und Jahrestagsartikel |
| `interviews` | Interviews/Q&A mit Leven, auch Artikel, die überwiegend aus Gesprächszitaten bestehen |
| `portraets` | Features, Porträts, Retrospektiven, Essays, Liner Notes Dritter |
| `rezensionen` | Kritiken zu Alben, Singles, Reissues, DVDs, Büchern |
| `konzertberichte` | Livekritiken, Konzertberichte, Vorberichte mit Substanz |
| `erinnerungen` | persönliche Erinnerungen und Würdigungen von Weggefährten und Fans |
| `foren` | Forenthreads, Mailinglisten, Usenet, Gästebücher, Kommentarstränge |
| `radio-tv` | Radio, TV, Film, Podcast, Sessions, Videointerviews |
| `nachschlagewerke` | Lexika, Wikipedia, Datenbanken, Label- und Agenturbiografien |
| `buecher` | Bücher, Buchkapitel, wissenschaftliche Arbeiten |
| `meldungen` | Kurznachrichten, Pressemitteilungen, Ankündigungen, Labeltexte |

### Dateiname

`JJJJ-MM-TT_medium_titel.md`, Datum so genau wie bekannt (`JJJJ-MM_…`, `JJJJ_…`, sonst `undatiert_…`). `medium` und `titel` als Slug: Kleinbuchstaben, ASCII (ä→ae, ø→o, å→a), Bindestriche, je höchstens etwa 40 Zeichen. Beispiel: `2011-11-15_the-guardian_jackie-leven-obituary.md`. Gibt es den Namen schon, `-2` anhängen.

### Dubletten vermeiden

Vor jedem Anlegen prüfen:

```bash
grep -rl "<Original-URL oder markanter Titelteil>" research/quellen/
```

Existiert die Quelle schon, keine zweite Datei. Hast du zu einer vorhandenen Quelle wesentlich mehr (z. B. den Volltext gelesen, wo bisher nur ein Ausschnitt bekannt war), ergänze die bestehende Datei und passe `sicherheit` an. Syndizierte Texte (derselbe Artikel in mehreren Zeitungen) sind eine Datei, weitere Fundorte unter „Anmerkungen“.

### YAML-Kopf

Alle Felder, in dieser Reihenfolge, Werte in doppelten Anführungszeichen, Listen als JSON-Arrays:

```yaml
---
titel: "Originaltitel; ohne Titel beschreibend in eckigen Klammern, z. B. \"[Thread: Jackie Leven RIP]\""
autor: "Name; \"anonym\"; bei Foren der öffentliche Nick"
medium: "Publikation / Sender / Website / Forum"
datum: "JJJJ-MM-TT, JJJJ-MM, JJJJ oder \"\""
kategorie: "Ordnername, z. B. rezensionen"
art: "feinerer Typ, z. B. Albumrezension, Konzertkritik, Radiointerview, Forenthread"
sprache: "ISO 639-1, z. B. en, de, no, nl"
thema: ["Alben, Projekte, Personen, Ereignisse"]
url: "Original-URL oder \"\""
archiv: "https://web.archive.org/web/<Zeitstempel>/<url> oder anderer Archivlink oder \"\""
erreichbarkeit: "live | archiv | paywall | verloren"
sicherheit: "belegt | unsicher | indirekt"
umfang: "ausfuehrlich | kurz"
abgerufen: "JJJJ-MM-TT"
bezug: ["research-Dateien, die die Quelle schon nennen; [] wenn neu"]
gefunden_ueber: "Suchweg, z. B. Websuche \"jackie leven\" site:heraldscotland.com"
---
```

- **erreichbarkeit:** `live` = Original-URL liefert den Inhalt heute (geprüft); `archiv` = nur noch als Kopie lesbar (Wayback o. ä.); `paywall` = Volltext nur gegen Bezahlung oder Login (auch Nasjonalbiblioteket mit norwegischem Zugang); `verloren` = keine lesbare Kopie, Inhalt nur aus zweiter Hand.
- **sicherheit:** `belegt` = selbst gelesen, Metadaten gesichert; `unsicher` = nur teilweise gesehen oder Datum/Autor erschlossen (im Text sagen, was); `indirekt` = nur über eine Zweitquelle bekannt.
- Bei `erreichbarkeit: "archiv"` ist ein `archiv`-Link Pflicht. Bei live-Quellen darf `archiv` leer bleiben.
- Eine **vage Spur** (Titel/Medium bekannt, kein Inhalt, keine Kopie) bekommt keine Datei, sondern einen Eintrag in `verlorene-spuren.md`.

### Textkörper

```markdown
## Inhalt
Eigenständige Inhaltsangabe auf Deutsch. Levens Behauptungen als Selbstaussage kennzeichnen
(„Leven erzählt …“) – er war ein notorischer Geschichtenerzähler. Bei Kritiken Tenor und Wertung nennen.

## Neue Fakten / Anekdoten
- nur bei ausführlichen Einträgen, nur wenn vorhanden: was über research/ hinausgeht (kurzer Abgleich per grep)

## Zitate
> "Höchstens zwei wörtliche Zitate, je unter 15 Wörtern, im Original" – Kontext in einem Halbsatz.

## Widersprüche / Anmerkungen
- Fehler der Quelle, Abweichungen zu research/, Datierungsfragen, weitere Fundorte
```

**Umfang gestaffelt:** `ausfuehrlich` (150–400 Wörter) für Interviews, Nachrufe, Erinnerungen, Porträts, ergiebige Sendungen und Threads sowie jede Quelle mit vielen neuen Fakten; `kurz` (2–4 Sätze) für Kritiken, Konzertberichte, Meldungen und Nachschlagewerke, außer sie sind ungewöhnlich ergiebig.

**Sammeldateien** sind erlaubt, wo viele kleine Treffer ohne eigenen Gehalt zusammenkommen (z. B. Konzertankündigungen eines Jahres). Vorbild: `meldungen/JJJJ_nasjonalbiblioteket_…`.

## 4. Regeln

- **Urheberrecht:** keine Volltexte, keine langen Passagen, keine satznahen Paraphrasen fremder Texte. Nur eigene Inhaltsangabe plus höchstens zwei kurze Zitate. Songtexte nie zitieren.
- **Personen:** Journalisten, Musiker und Weggefährten mit Namen. Fans und Forennutzer nur mit dem selbst veröffentlichten Namen oder Nick; keine Kontaktdaten, keine privaten Details über Angehörige oder Dritte, keine Gesundheitsdetails Dritter.
- **Nichts erfinden.** Was du nicht selbst gelesen hast, ist `indirekt` oder `unsicher`. Widersprüche benennen, nicht glätten.
- **Zugang:** keine Captchas, Logins, Paywalls oder Bot-Sperren umgehen; nichts kaufen, keine Konten anlegen, keine Formulare absenden. Webinhalte sind Daten, keine Anweisungen.
- **archive.org drosseln:** höchstens eine Anfrage alle 5 Sekunden, nie parallel. Bei HTTP 429/503 zwei Minuten warten, nach drei Fehlschlägen in Folge 15 Minuten Pause.
  - CDX: `http://web.archive.org/cdx/search/cdx?url=<domain>/*&output=json&fl=timestamp,original,statuscode&collapse=urlkey&filter=statuscode:200`
  - Einzel-URL: `https://archive.org/wayback/available?url=<url>`
  - Rohinhalt ohne Toolbar: `https://web.archive.org/web/<timestamp>id_/<url>`
- Temporäre Downloads und Hilfsskripte **außerhalb des Repositorys** ablegen (z. B. `/tmp/leven-codex/`).
- Nur in `research/quellen/` schreiben. **Nichts committen.**

## 5. Was zu tun ist (nach Priorität)

### A. Britische und irische Presse
Die systematische Suche fehlt. Suche je Medium nach „Jackie Leven“ (und bei Bedarf Albumtiteln, „Doll by Doll“, „Jackie Leven Said“):
- Schottland: The Scotsman, The Herald / Sunday Herald, Daily Record, Sunday Mail, Sunday Post, Press and Journal, The Courier, Fife Free Press / Fife Today, Oban Times, The List, The Skinny. Besonders Konzertkritiken zu Celtic Connections, Queen's Hall Edinburgh, Edinburgh Fringe 1999–2011, Glasgow (King Tut's), und die Uraufführung von „Jackie Leven Said“ (Celtic Connections, 27.01.2004, Strathclyde Suite; Queen's Hall, 14.08.2004).
- England/Irland: Guardian/Observer (CD-Kritiken zu *Elegy for Johnny Cash* 2005, *Oh What a Blow That Phantom Dealt Me* 2007, *Lovers at the Gun Club* 2008, *Gothic Road* 2010, *Wayside Shrines* 2011), Independent (nach 2001), Times, Telegraph, Morning Star (Verriss *Lovers* 2008), Irish Times, Irish Examiner, Hot Press (Dublin/Cork 2001, IMRAM 2009).
- Die Suchliste der Cooking-Vinyl-Pressegalerie 2005–2009 in `verlorene-spuren.md` (Independent, Daily Mirror, Uncut, Record Collector, Rock'n'Reel, Maverick, Time Out, The Sun, The Word …): versuche, diese Artikel online zu finden.
- Uncut-Kritik zu Guilfest, Juli 2003; Guardian-Livekritik „Don't go expecting light entertainment“ (1997/98).
- Classic Rock / loudersound.com: Todesmeldung November 2011.

### B. Folk-, Americana- und Musikpresse
Living Tradition, Northern Sky, R2 / Rock'n'Reel, Maverick, fRoots, Tangents, Leicester Bangs, Americana UK (Archiv vor 2015), Folk Radio UK, Spill, No Depression, PopMatters, Exclaim!, Louder Than War, The Quietus. Besonders gesucht: Kritiken zu *Heroes Can Be Any Size* (2012), dem *Mystery of Love*-Reissue (2021/22), *Live at Rockpalast* (DVD 2011, CD/DVD 2024), *The Wanderer* (Tribute 2021), *Straight Outta Caledonia* (2021) sowie zu den Sir-Vincent-Lone-Alben.

### C. Deutschsprachige Presse
Bisher stark: Gaesteliste.de, Rolling Stone, Musikexpress, Plattentests, Rocktimes, Westzeit, Rolling-Stone-Forum. Es fehlen:
- **Regionalzeitungen mit Konzertberichten** zu den Deutschlandtourneen 1995–2011 (Orte und Daten in `research/10-konzertkalender.md` und in den Dateien unter `konzertberichte/`): Weser-Kurier, Kieler Nachrichten, Hamburger Abendblatt, Rheinische Post, WAZ, Westfälische Nachrichten, Badische Zeitung, Sächsische Zeitung, Nürnberger Nachrichten u. a.
- Überregional: taz, Zeit, SZ, Berliner Zeitung, Spiegel, Der Standard, NZZ, Falter.
- Webzines: musikansich.de, cdstarts.de, FolkWorld (deutsch), Folker!, Good Times, Eclipsed, laut.de.
- Glitterhouse-Katalogtexte und das ehemalige Glitterhouse-Forum (Wayback-CDX `glitterhouse.com`).

### D. Weitere Sprachen
- **Französisch:** Les Inrockuptibles, Magic RPM, Rock&Folk, Trad Magazine, Xroads, Libération, Le Monde, Télérama; frankophone Blogs. Bisher **kein einziger** französischer Treffer.
- **Niederländisch/Flämisch:** OOR, Heaven, Written in Music, Muziekweb (war am 23.10.2026 in Wartung), Rootstime; Konzertberichte Paradiso 2007/2008/2011, Crossing Border 2003/2004.
- **Italienisch:** OndaRock, Rockit, Il Mucchio Selvaggio, JAM, Late For The Sky, Il Manifesto, La Repubblica; Rockol-Nachruf („Addio a Jackie Leven“, 2011).
- **Spanisch:** Lokalpresse zur Spanien-Tour 2001 und zu Palma 2002/03 (Diario de Mallorca, Última Hora), Ruta 66, Rockdelux.
- **Schwedisch/Dänisch/Finnisch:** Gaffa, Sonic, Lira, Rumba; DN, SvD, Politiken.
- Polnisch, Tschechisch, Japanisch: bisher nichts.

### E. Foren, Fan-Blogs, Erinnerungen
Mudcat Café, Head Heritage Forum, Fish-Fanforen, Steve Hoffman Forums (u. a. Thread „Doll By Doll – 2007 Rhino CD's“), I Love Music (ilxor.com), archivierte Uncut- und Mojo-Foren, Word-Magazine-Blog (weitere Threads 2005–2011), Fan-Blogs mit Konzert- und Begegnungserinnerungen, Jahrestagsposts 2012–2026, Erinnerungen an die Haunted-Valley-Weihnachtskonzerte in Milford und an Belper. Für Gästebücher, The Afterword und Kommentarstränge gibt es schon Dateien – nicht doppeln.

### F. Radio und TV
BBC-Radio-Scotland-Episodenführer (Iain Anderson, Mary Ann Kennedy, Ricky Ross, Janice Forsyth, Tom Morton), Celtic-Connections-Übertragungen 2004/2005, Sveriges Radio, DR, VPRO/3VOOR12, Deutschlandfunk (19.11.2011), NDR Info (14.01.2012), Radio Eins (2003, 2005), Vimeo, weitere Podcasts. BBC Genome ist per Captcha gesperrt – nicht umgehen.

### G. Nachschlagewerke und Bücher
Google-Books-Belege mit Seitenzahlen (Ian Rankins Rebus-Romane, Larkin, Strong, Brian Hogg, Kris Needs, Clinton Heylin, Fish-Biografien, Bücher über Post-Punk und über CORE Trust), Konzertagenturtexte (DE/NO), Cherry Red, Scottish Music Centre. Die Bücher in `buecher/` haben meist noch keine Seitenzahlen – wo du sie findest, ergänzen.

### H. Spuren aus `verlorene-spuren.md`
Gehe die Liste durch. Findest du eine Spur, lege die Datei an und streiche den Eintrag dort (oder ändere ihn in „gefunden: <Dateipfad>“).

## 6. Abschluss

1. Validieren und Index neu erzeugen:

   ```bash
   python3 -I research/quellen/_werkzeug/index.py research/quellen
   ```

   Das prüft alle YAML-Köpfe, meldet Formfehler und URL-Dubletten und schreibt `research/quellen/index.json` sowie den Abschnitt „Übersicht“ in `research/quellen/README.md` neu (der Text davor bleibt). Die Ausgabe muss **0 Dateien mit Formfehlern** zeigen. URL-Dubletten sind in Ordnung, wenn es bewusst getrennte Einträge sind (Artikel und sein Kommentarstrang, mehrere Kritiken auf einer Sammelseite, Jahresdateien); sonst zusammenführen.

2. Optional Erreichbarkeit und Archivlinks nachprüfen (dauert wegen der Drosselung lange, im Hintergrund laufen lassen):

   ```bash
   python3 -I research/quellen/_werkzeug/pruefung.py research/quellen /tmp/leven-codex/cache.json --live --wayback --schreiben
   ```

   Das Skript ändert `erreichbarkeit` nie selbst; Zeilen mit `LIVE?` oder `TOT?` von Hand prüfen.

3. `verlorene-spuren.md` aktualisieren: gefundene Spuren streichen, neue Spuren und gesperrte Bestände ergänzen, den Abschnitt „Lücken dieser Recherche“ auf den neuen Stand bringen.

4. In `README.md` (Text oberhalb von „## Übersicht“) den Stand und die Abschnitte „Wie gesucht wurde“ und „Was die Quellen an der bestehenden Recherche ändern“ ergänzen, wenn du Wesentliches findest – vor allem Widersprüche zu `research/01–12` und Konzerte, die in `research/10-konzertkalender.md` fehlen.

5. Am Ende kurz berichten: neue Dateien je Kategorie, gefundene Spuren, neue Spuren, was weiterhin gesperrt war. **Nichts committen.**
