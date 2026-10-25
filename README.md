# Jackie Leven

Eine private Hommage an den schottischen Songwriter **Jackie Leven** (18. Juni 1950, Kirkcaldy – 14. November 2011, Hampshire). Keine offizielle Seite, kein Nachlass, keine Plattenfirma.

Das Projekt besteht aus drei Teilen: einer Recherchegrundlage, einer erfundenen Autobiografie in seiner Stimme und einer Website, die beides zugänglich macht. Die Website läuft als eigenständiger Go-Server.

## Lokal starten (Go 1.26)

```sh
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8080
go test -race ./...
go vet ./...
```

Die Go-Version ist unter `http://127.0.0.1:8080/de/` erreichbar. Sie verwendet ausschließlich die Go-Standardbibliothek. JSON-Daten und Go-Templates werden beim Start geladen, Markdown bleibt die Inhaltsquelle. Für den historischen Abgleich bleibt die eingefrorene Referenz außerhalb dieses Branches erhalten.

- [Migrationsstand und Wiederaufnahme](docs/go-migration.md)
- [Architektur und bewusste Entscheidungen](docs/go-architecture.md)
- [HTTP-Abgleich und Normalisierungen](werkzeug/parity.md)
- [Release und Linux-Betrieb](ops/GO-BETRIEB.md)
- [Separate Live-Testinstanz unter unpubli.sh/jackieleven](ops/GO-PREVIEW.md)

Die Live-Testinstanz läuft unter <https://unpubli.sh/jackieleven/de/>. Der Branch enthält ausschließlich die Go-Anwendung; die produktive Bestandsseite bleibt bis zur gesonderten Abnahme unverändert.

## Die Grundlage: seine eigenen Texte

Leven hat von Oktober 2002 bis Herbst 2011 auf seinen eigenen Websites geschrieben — erst die Monatskolumne *The Deep Pool* auf jackieleven.com, ab 2008 Blog und Rubriken auf jackieleven.co.uk. Beide Seiten sind offline; jackieleven.co.uk wurde 2024 vom Hoster gesperrt.

Über das Internet Archive ließen sich **76 dieser Texte wiederherstellen, rund 90.000 Wörter** — der einzige Ort, an dem er ausführlich mit eigener Stimme über sich spricht. Sie liegen wortgetreu in [`research/columns/`](research/columns/README.md), je eine Datei pro Beitrag, mit Rubrik, Datum, Quell-URL und Archivlink im YAML-Kopf.

Dieser Korpus ist zugleich die **Faktenbasis** und der **stilistische Maßstab** des Projekts.

## Startseite und Zeitreise

`/de/` und `/en/` sind der gemeinsame Einstieg. Die Startseite folgt dem gelieferten Entwurf „Startseite nachgebaut“ (Desktop 1200, Tablet 768, Phone 390): grafisches Konzertporträt mit einem Vers aus *My Philosophy*, fünf Lebensstationen und drei Auszüge zu Kolumnen, Zeitreise und Diskographie. Die Originaltexte bleiben englisch, die Beschriftungen sind übersetzt. Der Text über Ed führt zur zugehörigen Station; das Album führt zur Ausgabenseite. Das Cover ist in Schwarzweiß dargestellt. Der Hinweis auf die persönliche, unabhängige Hommage steht im Footer, ohne Lebensdaten.

`data/startseite.json` enthält die Auszüge und ihre Quellenzuordnung; die archivierten Originaldateien bleiben unverändert. Das im Archiv fehlende anfängliche T im Ed-Text ist entsprechend dem Entwurf ergänzt. Instrument Serif, Newsreader und Space Grotesk liegen samt OFL-Lizenzen unter `assets/fonts/`, die gelieferten Bilder unter `assets/bilder/startseite/`. Die Schriften und das mobile Menü werden nur auf der Startseite geladen. Ohne JavaScript bleiben alle Navigationslinks sichtbar; mit JavaScript lässt sich das Menü auf kleinen Bildschirmen öffnen und per Escape schließen. Die Jahresreihe ist dort horizontal scrollbar.

Die Zeitreise hat ihre eigene Übersichtsadresse: `/de/zeitreise` bzw. `/en/timeline`. Bestehende Stationsadressen bleiben gültig. Der Namenszug im Kopf führt zur Startseite; „Zeitreise“ im Menü und die Verweise in der Biografie führen zur Zeitreise.

## Mitmachen und Kontaktformular

`/de/mitmachen` und `/en/contribute` laden zu Erinnerungen, Ergänzungen und Mitarbeit ein.
Die Startseite und der gemeinsame Footer verlinken die Einladung. Das Formular sendet
nur an `stefan@jackieleven.com`, mit `Jackie Leven · Hommage <jackieleven@unpubli.sh>` als
Absender und der Besucheradresse als `reply_to`. Es veröffentlicht keine Einsendungen und
versendet keine automatischen Antworten an Besucher. Fotos kommen zunächst per E-Mail.

Der Versand läuft über die Resend REST API mit dem HTTP-Client der Go-Standardbibliothek.
Die Konfiguration erfolgt ausschließlich über `JACKIE_RESEND_API_KEY`,
`JACKIE_TURNSTILE_SITEKEY` und `JACKIE_TURNSTILE_SECRET` in der Prozessumgebung.
Schlüssel gehören weder ins Repository noch in den Browsercode. Die Testinstanz auf
unpubli.sh verwendet absichtlich keine Versandzugänge.

Das Formular verwendet Sitzungstoken, ein unsichtbares Zusatzfeld, Mindest-Ausfüllzeit,
eine Pause nach erfolgreichem Versand und ein gemeinsam gesperrtes Limit von fünf
Versandversuchen je Stunde/IP. Der Zähler liegt außerhalb des Webroots im temporären
Verzeichnis; `JACKIE_CONTACT_STATE_DIR` kann ein eigenes beschreibbares, privates
Verzeichnis festlegen. Er enthält Zeitpunkte und täglich wechselnde Hashes, keine
Nachrichteninhalte. Alte Zähler werden nach zwei Tagen beim nächsten Versuch entfernt.
Bei mehreren Servern muss dieser Speicher gemeinsam genutzt werden. Fehler erhalten die
Eingaben; ein Resend-Idempotenzschlüssel schützt identische Wiederholungen nach Zeitüberschreitungen.
Ohne Schlüssel bleibt der Senden-Knopf deaktiviert und die direkte E-Mail-Adresse sichtbar.

Das Kontaktformular der Go-Testinstanz ist sichtbar deaktiviert, solange die Anbieterzugänge fehlen.

## The Deep Pool auf der Website

Unter `/de/deep-pool` und `/en/deep-pool` beginnt die Lektüre direkt mit der ersten Kolumne vom Oktober 2002. Nur dort steht eine kurze Einführung über dem Artikel. Ein Zeitstrahl nach dem Vorbild der Zeitreise führt durch alle Texte und markiert den aktuellen Beitrag: auf großen Bildschirmen seitlich, auf schmalen als waagerechtes Band. Oben und unten führen schlichte Links zum vorherigen und nächsten Text sowie zu „Alle Texte“. Die vollständige Jahresübersicht liegt unter `/de/deep-pool/archiv` bzw. `/en/deep-pool/archive`. Jede Leseseite enthält den englischen Originaltext, Datum und Autor; Herkunft, Archivlink und aufklappbare Hinweise stehen unter dem Text. Neue redaktionelle Titel oder Inhaltsbeschreibungen sind nicht ergänzt.

`data/kolumnen.json` legt den veröffentlichten Bestand fest: 73 Beiträge bis einschließlich der Todesanzeige vom November 2011. Die drei später archivierten Beiträge von 2012 bleiben in der Recherche, erscheinen aber nicht auf der Website. `internal/site/markdown.go` liest die Originaldateien, ohne sie zu verändern. Bekannte Erscheinungsmonate aus den frühen Archiv-URLs werden berücksichtigt; ansonsten sind die späteren Datierungen ausdrücklich als Archivdatum gekennzeichnet. Die Todesanzeige trägt eine entsprechende Autorenangabe der Website-Betreiber. Wiederholte Seitenleistenbilder und zwei Navigationsreste in der September-Kolumne 2007 erscheinen nicht in der Lesefassung. Doppelte Monats- und Rubrikkopfzeilen am Anfang der alten Kolumnen werden durch den Lesekopf ersetzt; die Prosa bleibt unverändert.

## Diskographie

Die **Diskographie** unter `/de/diskografie` bzw. `/en/discography` führt durch 88 Einträge von 1975 bis 2024: John St. Field, Doll by Doll, Concrete Bulletproof Invisible, Jackie Leven, Sir Vincent Lone und Jackie Balfour, außerdem Haunted Valley, Kooperationen und spätere Ausgaben. Der Jahreszeitstrahl folgt der Leseposition; die Auswahl nach Projekt und Veröffentlichungsart aktualisiert auch die Jahresnavigation. Bestehende Sprunglinks zu einzelnen Einträgen bleiben gültig; Sprachwechsel erhalten die Auswahl. Ohne JavaScript bleibt der gesamte Katalog lesbar.

Cover und Titel öffnen eine eigene Ausgabenseite, beispielsweise `/de/diskografie/1999-greek-notebook`. Sie zeigt Fakten, Titelliste und belegte Credits ohne Hintergrundtexte. Ihr Zeitstrahl führt zu einzelnen Ausgaben; Vor- und Zurückblättern folgt der aktuellen Filterauswahl. Die Rückkehr zur Übersicht erhält Filter, geöffnete Quellen und Leseposition – auch über den Zurück-Knopf des Browsers. Dafür werden der Verlaufseintrag und der Sitzungsspeicher im Browser verwendet; ohne JavaScript bleiben Detailseiten und Navigation zugänglich.

`data/diskografie-details.json` ergänzt die 88 Katalogeinträge um ausgabenspezifische Fakten und Quellen: 85 Titellisten mit insgesamt 881 Trackeinträgen sowie Credits für 22 Ausgaben. LP-Seiten, mehrere CDs und abweichende Titelreihenfolgen werden getrennt geführt. Für *The Last Flick of the Golden Wrench*, *The Meeting of Remarkable Men* und *Live from a Cornish Pub in Germany* ist keine vollständige Titelliste hinterlegt; dies steht auf der jeweiligen Seite. Bestehende Katalogeinträge, die mehrere Single-Varianten bündeln, zeigen diese als getrennte Titellisten. Quellen sind unter anderem die aktuelle Diskographie von Stuart Briers und Bob Astridge, konkrete MusicBrainz-Ausgaben und die Labelkataloge von MIG und Guerssen.

`data/diskografie.json` enthält die Ausgaben, zweisprachige Anmerkungen, Quellen und Coveradressen. Grundlage ist `research/05-diskografie.md`, ergänzt um Labelnachweise und Jackies Ankündigungen. Insbesondere: *Live from a Cornish Pub in Germany* ist durch seinen Septembertext 2008 belegt; *Troubadour Heart* war 2008 zunächst direkt erhältlich und kam 2009 regulär heraus; die Rockpalast-Ausgabe von 2024 enthält CD und DVD. Unveröffentlichte bzw. nicht gesichert erschienene Projekte sind ausdrücklich gekennzeichnet. Cover werden aus den verlinkten Label- und Musikkatalogen eingebunden; digitale Cover belegen keine historischen Erscheinungsdaten.

## Hörlinks und YouTube-Liedbeispiele

`data/diskografie-hoerlinks.json` führt geprüfte digitale Albumangebote mit
Spotify-, Apple-Music-, Qobuz-, Amazon-Music- und Bandcamp-Links. Die ersten 14
Albumangebote sind um 15 Qobuz- und zehn Amazon-Angebote sowie zwei Bandcamp-
Veröffentlichungen ergänzt: *Straight Outta Caledonia* und *The Wanderer – A Tribute*.
Die Qobuz-/Amazon-Zuordnung stützt sich auf die sichtbaren Künstlerkataloge, Bandcamp
auf die konkreten Veröffentlichungsseiten. Die Links sind an den beobachteten Store
gebunden; regionale Erreichbarkeit und Abspielbarkeit können abweichen.

Insgesamt haben 44 Ausgaben ein Albumangebot. Zuletzt kamen Spotify- und Apple-Music-Links
für 16 weitere Ausgaben hinzu, darunter *For Peace Comes Dropping Slow*, alle vier Teile von
*The Haunted Year*, die drei Sir-Vincent-Lone-Alben, *Chip Pan Fire*, *Heroes Can Be Any Size*,
*Live Or Die* und der Rockpalast-Mitschnitt; *Straight Outta Caledonia* hat beide Dienste
zusätzlich erhalten. Grundlage sind Apples Katalogsuche und die Diskografieseiten bei Spotify.
*Songs for Lonely Americans* (2004) verweist auf die gleichlautende Digitalfassung von 2006,
die Rockpalast-Ausgaben von 2011 und 2024 teilen sich eine Digitalfassung. *Live Or Die* enthält
digital nur die 25 Lieder, ohne die zehn gesprochenen Zwischenstücke der CDs.

Auch *Control* und die fünf Doll-by-Doll-Alben sind über Spotify verknüpft,
einschließlich der zugehörigen Neuauflagen. YouTube-Beispiele decken deren
sämtliche Liedtitel ab; die abweichenden Titel „Human Face“ / „The Human Face“
und „Palace of Love“ / „The Palace of Love“ werden gemeinsam zugeordnet.

Die Albumlinks stehen als eigene, einfarbige SVG-Symbole vor der Titelliste,
mit englischen Tooltips und zugänglichen Beschriftungen. Qobuz ermöglicht auch
Downloads, Bandcamp Downloads und angebotene physische Ausgaben. Preise und
Lagerbestände werden nicht auf der Website gespeichert. Historische Titellisten
und Erscheinungsjahre bleiben bestehen. *Gothic Road* enthält digital zwei zusätzliche
Titel; Bandcamp führt die 22 Stücke des Tribute-Albums in anderer Reihenfolge.

`data/youtube-titel.json` ordnet 343 Liedtiteln je eine Liste von YouTube-Aufnahmen zu:
zuerst das Hörbeispiel (Studioaufnahme bevorzugt, offizielle Topic- und Labelkanäle vor
Fan-Uploads), danach insgesamt 135 Livefassungen. Die Zuordnung folgt dem Lied, **nicht der
konkreten Aufnahme**: dieselben Links erscheinen bei jedem Vorkommen, auch über Studio-/Livefassungen
und Wiederveröffentlichungen hinweg. Das Hörbeispiel steht als YouTube-Symbol in der Zeile; die
Livefassungen folgen chronologisch in einer kleinen Zeile „Live“ unter dem Liedtitel, mit Ort und
Jahr (etwa „Bremen 1999 · Kiel 2003 · Rockpalast 2004“). Offizielle Livealben ohne belegtes
Aufnahmedatum erscheinen mit ihrem Titel („Munich Blues“). Je Konzert steht höchstens eine Fassung.
Ortsnamen mit eigener deutscher Schreibung stehen zweisprachig (`label` als `{de, en}`).

Quellen der Livefassungen sind die Album-Playlists der Topic-Kanäle (*The Haunted Year*, *For Peace
Comes Dropping Slow*, *Live Or Die*, *Revenge of Memory*), der offizielle Rockpalast-Konzertfilm von
MIG mit Zeitsprung zum jeweiligen Titel sowie Fan- und TV-Mitschnitte, deren Ort und Datum Titel oder
Beschreibung belegen. Längere Mitschnitte ohne Zeitmarken bleiben in der Fundliste. Satzzeichen,
Live-/Edit-Zusätze, „(Spoken)“, „(bonus track)“, „(Full Version)“, „(From Live Show)“ und
wenige belegte Schreibvarianten werden normalisiert; „Intro“ bleibt ohne Link, weil verschiedene
Einleitungen denselben Titel tragen. Der Tooltip nennt das tatsächliche Video, gegebenenfalls das
Album, und den Kanal. `internal/site/content.go` ordnet Hörbeispiele und Livefassungen den Liedtiteln zu. Auf den derzeitigen Titellisten haben damit
813 von 881 Trackeinträgen auf 84 Ausgabenseiten ein Hörbeispiel, dazu kommen 876 Livelinks.

Die Recherche liegt unter `research/youtube-fundliste.md`, als strukturierte Daten unter
`research/youtube-fundliste.json` und als lokal durchsuchbare Tabelle unter
`research/youtube-fundliste.html`. Stand 23. Oktober 2026: 785 unterschiedliche Videos aus
Suchergebnissen, Kanal- und Albumseiten der Topic-Kanäle und einer gezielten Suche je Liedtitel,
einschließlich Topic-Audio, offiziellen Audio-/Standbild-Videos, Fan-Uploads, Konzerten mit Ort
und Datum, Interviews und Alias-Projekten. Die Liste vermerkt, welches Video in der App als
Hörbeispiel oder Livefassung dient, und führt am Ende die 46 Liedtitel ohne auffindbare Aufnahme.
Kategorien folgen den sichtbaren Metadaten und Videobeschreibungen; die in der App verwendeten
Videos waren am Stichtag erreichbar, eine Rechteprüfung gibt es nicht. Die Sammlung beansprucht
keine Vollständigkeit. Fremde Suchtreffer und Mix-Links sind entfernt.

Es werden keine Player, externen Musikskripte oder automatischen Plattformabfragen beim
Seitenaufruf geladen. Die Dienste werden erst beim Anklicken geöffnet. Ein angezeigter Link
ist keine Zusicherung, dass jedes Video in jedem Land und ohne Anmeldung abspielbar ist.

### Live-Videos auf den Ausgabenseiten

Unter der Titelliste zeigt der Abschnitt „Live-Videos“ Konzertmitschnitte zu den Liedern der
Ausgabe, als Karte je Konzert. Grundlage ist `data/live-videos.json`: Konzert (Titel, Datum in
der belegten Genauigkeit, Herkunft `official` oder `fan`, zugehörige Ausgaben) mit Videos, Kanal,
Dauer und den enthaltenen Stücken samt Startsekunde. Auf der Ausgabe des Konzerts selbst stehen alle
Stücke, sonst nur die gemeinsamen Lieder; ein Klick auf ein Stück springt im Player an die Stelle.
Derzeit ist nur der vollständige Rockpalast-Film von MIG offiziell; Fan-Mitschnitte (ZDF Disco 1981,
Cropredy 2004, Manchester 2009, Essen 2010, Glasgow 2011) sind erfasst, werden aber nur mit
`JACKIE_FAN_VIDEOS=1` eingebettet. Hochgeladen
heißt nicht lizenziert: Bei Fan- und TV-Mitschnitten ist der Uploader selten Rechteinhaber.

Eingebettet wird nur, was `werkzeug/livevideos.py` als einbettbar gespeichert hat (`embeddable`,
`checked`). Das Werkzeug fragt mit einem Schlüssel für die YouTube Data API (`JACKIE_YOUTUBE_API_KEY`) Einbettfreigabe, Sichtbarkeit, Altersbeschränkung und Sperren für
Deutschland ab, ohne Schlüssel nur oEmbed. Verweigert YouTube das Abspielen trotzdem, ersetzt sich
die Karte durch einen Link. Ohne JavaScript sind alle Karten und Stücke gewöhnliche YouTube-Links.

Vor dem Klick lädt die Seite nichts von YouTube. Die Vorschaubilder legt das Werkzeug lokal unter
`assets/bilder/live/` an (480×270 WebP, derzeit 3–12 KB); sie tragen `loading="lazy"` und werden
erst beim Scrollen geholt, ab dem vierten Konzert stehen sie eingeklappt und laden erst beim Öffnen.
`assets/js/livevideos.js` wird nur auf Seiten mit Live-Videos eingebunden; die Player-API von YouTube
und der Player (`youtube-nocookie.com`) folgen erst beim ersten Klick, je Konzert ein Player.

```sh
python3 werkzeug/livevideos.py            # Einbettfreigabe prüfen, fehlende Vorschauen anlegen (Netz)
python3 werkzeug/livevideos.py --vorschau # alle Vorschaubilder neu erzeugen
```

## Stimmen: externe Quellen

`/de/stimmen` bzw. `/en/voices` zeigt, was andere über Jackie geschrieben und gesagt haben: 741 Interviews,
Kritiken, Porträts, Konzertberichte, Nachrufe, Erinnerungen, Sendungen, Foren und Bücher von 1971 bis heute,
im Zeitstrahl wie die Diskographie und filterbar nach Art, Sprache und Zugang (frei lesbar, online, Webarchiv,
Bezahlschranke, verloren). Grundlage ist die Recherche in `research/quellen/` (eine Datei je Quelle, eigene
Inhaltsangabe); das Konzept steht in `research/ressourcen-seite-konzept.md`.

`werkzeug/quellen.py` erzeugt daraus `data/quellen.json`. Öffentlich werden Kopfdaten, die eigene,
ausführliche Inhaltsangabe und wörtliche Zitate im Original, auch längere; Fundweg, Sicherheit, Widersprüche und
Verweise auf Arbeitsdateien bleiben intern. Quellen, die einen verbreiteten Irrtum widerlegen (etwa das
Erscheinungsjahr von *Control*), tragen zusätzlich einen Abschnitt **Korrektur** und einen **Beleg** mit dem
Originalwortlaut und einer Übersetzung. Stufen: 34 ausgewählte Quellen (Liste im Werkzeug und YAML-Köpfe), das Verzeichnis mit eigener Detailseite und
„weitere Quellen“, die je Jahr eingeklappt direkt aufs Original verweisen; Quellen, die nur aus zweiter Hand
bekannt sind, bleiben intern. Ein Feld `stufe:` im YAML-Kopf einer Quelle geht der Regel vor. Rezensionen sind
über die Albumtitel den Ausgaben zugeordnet und erscheinen dort als „Pressestimmen“.

Norwegische Zeitungsartikel stellt die Nationalbibliothek je Ausgabe teils unter CC BY-NC-ND oder CC BY-NC
frei. `--lizenzen` fragt das über `api.nb.no` ab und speichert es in `data/quellen-lizenzen.json`; frei
lizenzierte Artikel sind als „frei lesbar“ gekennzeichnet und tragen Namensnennung und Lizenz. Die englischen
Fassungen stehen in `data/quellen-en.json`, je Quelle mit einer Prüfsumme des deutschen Texts; ändert sich
dieser, gilt die Übersetzung als veraltet. Die englische Seite fällt nie auf Deutsch zurück, und
`werkzeug/inhalte.py` schlägt fehl, solange einer Quelle mit eigener Seite die englische Fassung fehlt.
Ausgewählte Detailseiten zeigen kompakte Faksimile-Ausschnitte mit Quellenverweisen; rote Rahmen sind als
redaktionelle Ergänzung gekennzeichnet. `werkzeug/quellen-auszuege.py` erzeugt die lokalen WebP-Dateien und
`data/quellen-auszuege.json` aus den erhaltenen markierten Originalen und `research/faksimiles/web-auszuege.json`.
Die Vorschauen sind auf 24 rem Breite und 26 rem Höhe begrenzt, werden verzögert geladen und lassen sich
anklicken. Die Übersicht lädt diese Bilder nicht; der Server sollte gzip liefern.

```sh
python3 werkzeug/quellen.py              # öffentliche Daten aus research/quellen/ erzeugen
python3 werkzeug/quellen.py --lizenzen   # zusätzlich Lizenzen der Nationalbibliothek abfragen (Netz)
python3 werkzeug/quellen-auszuege.py  # kompakte Faksimile-Ausschnitte erzeugen (Pillow)
python3 werkzeug/inhalte.py           # Kataloge und Übersetzungen prüfen
```

## Verzeichnisse

| Pfad | Inhalt |
|---|---|
| [`research/`](research/README.md) | Biografisches Kompendium: zwölf Akten mit Fußnoten, Zeitleiste mit Datierungskonflikten, Konzertkalender (470 Auftritte), Website-Geschichte — dazu `columns/` als Primärquelle |
| [`autobiografie/`](autobiografie/00-rahmen.md) | Die Pastiche: 15 Kapitel in Levens Stimme, **nicht von ihm geschrieben**. Dazu Rahmen, Kapitelplan und das Sprachdokument; Übersetzungen einzelner Teile in `autobiografie/<sprache>/` |
| `werkzeug/` | `messen.py` misst die Kapitel gegen den Korpus, `pruefen.py` meldet KI-Satzformen, `zitate.py` prüft die Zitate der Website gegen ihre Quellen, `uebersetzung.py` die Übersetzungen der Pastiche gegen das Original |
| `cmd/`, `internal/site/` | Go-Server, Routing, Leser, SEO und Kontakt |
| `data/`, `templates/`, `assets/` | JSON-Kataloge, Go-Templates, CSS/JS, Bilder und Schriften |
| `sketches/` | Design-Entwürfe A–E; die Seite folgt Entwurf E |
| `.dev/` | Werkstattbericht über die Entstehung |

## Die Autobiografie ist erfunden

**Der Text in `autobiografie/` stammt nicht von Jackie Leven.** Er ist eine Pastiche, geschrieben auf Grundlage dessen, was Leven selbst über sich erzählt hat. Jedes Kapitel trägt diesen Hinweis und endet mit einem Abschnitt „Belegt / erfunden", der beides einzeln auflistet.

Die Kennzeichnung ist keine Formalie. Leven war ein notorischer Ausschmücker — Bob Dylan als angeblicher Ko-Autor, eine Auftragsmörderin als Song-Inspiration, ein eigener Whisky, den sein Labelchef „a complete scam" nannte. Seine echten Erinnerungen klingen bereits wie Erfindungen. Ungekennzeichnete erfundene Ich-Prosa daneben würde seine Biografie endgültig unlesbar machen.

Auf der Website steht das Buch unter „Biografie“: jede Kapitelseite mit Pastiche-Hinweis, „Pastiche“ im Seitentitel, ohne Zitatauszeichnung und mit `noindex`. Die Seite liest die Kapitel direkt aus `autobiografie/`. Siehe [`autobiografie/00-rahmen.md`](autobiografie/00-rahmen.md), Abschnitt „Auf der Website“.

## Inhalte prüfen

Die [Pflegewerkzeuge](werkzeug/README.md) benötigen Python 3.10 oder neuer. Bildaufbereitung benötigt zusätzlich Pillow; die Go-Laufzeit selbst verwendet diese Werkzeuge nicht.

Der Server liefert nur freigegebene Routen und Dateien unter `/assets/` aus.
Recherche, Templates, Daten und Punktdateien sind keine öffentlichen Verzeichnisse.

```sh
python3 werkzeug/messen.py              # Kapitel gegen den Korpus messen
python3 werkzeug/pruefen.py 07 08       # Kandidaten für KI-Sprache
python3 werkzeug/zitate.py              # Originalzitate gegen Quellen prüfen
python3 werkzeug/inhalte.py             # Kataloge und Quellen prüfen
```

## Sprachen

Die Seite läuft auf Deutsch und Englisch unter `/de/…` und `/en/…`. `/` leitet nach `Accept-Language` des Browsers weiter, sonst auf Deutsch. Auch die Pfade sind übersetzt (`/de/zeitreise/1950-kirkcaldy`, `/en/timeline/1950-kirkcaldy`); ein Pfad in der falschen Sprache wird umgeleitet, Adressen ohne Präfix aus der Zeit vor der Umstellung ebenfalls.

**Die Zitate werden nie übersetzt.** Sie stehen einmal in `data/stationen.json` und erscheinen in jeder Sprachfassung im englischen Original mit `lang="en"`.

Text liegt je nach Art an drei Orten:

| Was | Wo | |
|---|---|---|
| Oberfläche, Monatsnamen, URL-Pfade | `data/lang/<code>.json` | Pflicht |
| Stationstexte (Titel, Label, Begleittext, Bildunterschrift) | `data/texte/<code>.json` | optional |
| Fließtextseiten (Über, Biografie) | `templates/<code>/` | optional |

Zusätzliche Sprachen benötigen neben diesen Inhalten die passenden Sprach-, Routen- und Fallbackregeln in `internal/site/` sowie entsprechende Tests. Aktuell sind Deutsch und Englisch unterstützt. Die englischen Label sind bewusst keine Wort-für-Wort-Übertragung: „Station · Kirkcaldy“ ist deutsch, auf Englisch steht nur der Ort.

```sh
python3 werkzeug/zitate.py                 # jedes Zitat Zeichen für Zeichen gegen seine Quelle
```

## Tests, Release und Betrieb

```sh
go test -race ./...
go vet ./...
node werkzeug/browserablaeufe.cjs
python3 -B -m unittest discover -s ops -p 'test_*.py'
python3 ops/prepare-go-release.py /tmp/jackieleven-go-release --goos linux --goarch amd64
```

Das Zielverzeichnis muss neu sein. `ops/go-release-files.json` begrenzt das Paket auf
Binärdatei, veröffentlichte Texte, JSON-Daten, Templates und benötigte Assets.
Der Builder schreibt Revision, Buildstatus und SHA-256-Prüfsummen. Ein Release
wird vor Auslieferung eigenständig gestartet und gegen den gespeicherten
Seitenvertrag geprüft; ein Quellbaumtest allein genügt nicht.

Die [Betriebsanleitung](ops/GO-BETRIEB.md) beschreibt den Go-Dienst hinter nginx,
private Zustandsdateien und den Versionswechsel. Die [Vorschauanleitung](ops/GO-PREVIEW.md)
dokumentiert die bereits installierte Hetzner-Testinstanz und ihre Rücknahme.
Der Branch enthält keine Werkzeuge mehr, die die alte Serverlaufzeit installieren.
Die statischen Entwürfe in `sketches/` und die frühere Interimsseite in `interim/`
bleiben als Gestaltungsmaterial erhalten.

## Rechte — bitte vor einer Veröffentlichung lesen

**Dieses Repository ist privat, und das hat Gründe.**

- **`research/columns/`** enthält die wiederhergestellten Originaltexte. Die Rechte daran liegen nicht bei uns. Die Rubrik „The Deep Pool“ macht den festgelegten Bestand als Lesefassung mit Quellen- und Rechtehinweis zugänglich; die Recherchedateien selbst bleiben gesperrt.
- **`assets/bilder/` und `sketches/assets/`** sind echte Pressefotos. Der Fotograf ist nicht ermittelt.
- **`research/09-alan-moffatt-genealogie.md`** enthält Registerdaten, Testamentsangaben und Familienspuren zu einer realen Person und ihren Angehörigen.
- **`autobiografie/`** darf nach dem eigenen Rahmen nirgends als Levens Wort erscheinen. Auf der Website steht es gekennzeichnet und mit `noindex`; vor einer Veröffentlichung ist zu entscheiden, ob das reicht.

Die Zeitreise verwendet kurze, wortgetreue Zitate mit Archivlinks. Die Rubrik „The Deep Pool“ gibt dagegen die Originalbeiträge einschließlich der darin enthaltenen Zitate und Liedpassagen wieder.


## Suchmaschinen und Vorschauen

`internal/site/seo.go` verwaltet die Metadaten und die öffentliche Adresse
`https://jackieleven.com`. Jede Inhaltsseite hat einen Canonical-Link, DE/EN-
Sprachverweise, eine Beschreibung sowie Open-Graph-/Twitter-Vorschaudaten.
JSON-LD beschreibt die Website als unabhängige Hommage und die Seite als Inhalt
über Jackie; es bezeichnet die Website nicht als offizielle Künstlerseite.
Filter- und Kontextparameter werden nicht in die kanonische Adresse übernommen.

`/sitemap.xml` wird aus den veröffentlichten Routen erzeugt, inklusive
Sprachvarianten. Weiterleitungen, Filtervarianten und die mit `noindex`
versehenen Pastiche-Kapitel sind ausgeschlossen. Die Biografie-Einstiegsseite
bleibt auffindbar; `data-nosnippet` schließt ihren erfundenen Erzähltext aus
Suchvorschauen aus. Die Sitemap verwendet keine erfundenen Änderungsdaten.

Nur Anfragen an den Host `jackieleven.com` sind für die Indexierung freigegeben.
Andere Hosts (einschließlich localhost und Vorschauumgebungen) liefern `noindex`
und eine sperrende `robots.txt`. Die öffentliche Domain muss bei einer Änderung
in der Konstanten `origin` und der Hostprüfung in `internal/site/server.go` angepasst werden. Fehlerseiten und HTML-Fragmente
sind ebenfalls `noindex`.

Prüfen: `go test ./internal/site` und die Releaseprüfungen oben.
`ops/nginx-go-site.conf` ist die Vorlage für den späteren Produktivbetrieb;
`ops/check-site.py` prüft eine vollständig konfigurierte produktive Instanz.
Die aktuelle Vorschau verwendet einen eigenen Dienst und eigene nginx-Regeln.
Eine Search-Console-Verifizierung wird erst mit dem tatsächlichen Verifizierungscode ergänzt.
