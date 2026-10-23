# Jackie Leven

Eine private Hommage an den schottischen Songwriter **Jackie Leven** (18. Juni 1950, Kirkcaldy – 14. November 2011, Hampshire). Keine offizielle Seite, kein Nachlass, keine Plattenfirma.

Das Projekt besteht aus drei Teilen: einer Recherchegrundlage, einer erfundenen Autobiografie in seiner Stimme und einer PHP-Website, die beides zugänglich macht.

## Die Grundlage: seine eigenen Texte

Leven hat von Oktober 2002 bis Herbst 2011 auf seinen eigenen Websites geschrieben — erst die Monatskolumne *The Deep Pool* auf jackieleven.com, ab 2008 Blog und Rubriken auf jackieleven.co.uk. Beide Seiten sind offline; jackieleven.co.uk wurde 2024 vom Hoster gesperrt.

Über das Internet Archive ließen sich **76 dieser Texte wiederherstellen, rund 90.000 Wörter** — der einzige Ort, an dem er ausführlich mit eigener Stimme über sich spricht. Sie liegen wortgetreu in [`research/columns/`](research/columns/README.md), je eine Datei pro Beitrag, mit Rubrik, Datum, Quell-URL und Archivlink im YAML-Kopf.

Dieser Korpus ist zugleich die **Faktenbasis** und der **stilistische Maßstab** des Projekts.

## Startseite und Zeitreise

`/de/` und `/en/` sind der gemeinsame Einstieg. Die Startseite folgt dem gelieferten Entwurf „Startseite nachgebaut“ (Desktop 1200, Tablet 768, Phone 390): grafisches Konzertporträt mit einem Vers aus *My Philosophy*, fünf Lebensstationen und drei Auszüge zu Kolumnen, Zeitreise und Diskographie. Die Originaltexte bleiben englisch, die Beschriftungen sind übersetzt. Der Text über Ed führt zur zugehörigen Station; das Album führt zur Ausgabenseite. Das Cover ist in Schwarzweiß dargestellt. Der Hinweis auf die persönliche, unabhängige Hommage steht im Footer, ohne Lebensdaten.

`app/data/startseite.php` enthält die Auszüge und ihre Quellenzuordnung; die archivierten Originaldateien bleiben unverändert. Das im Archiv fehlende anfängliche T im Ed-Text ist entsprechend dem Entwurf ergänzt. Instrument Serif, Newsreader und Space Grotesk liegen samt OFL-Lizenzen unter `assets/fonts/`, die gelieferten Bilder unter `assets/bilder/startseite/`. Die Schriften und das mobile Menü werden nur auf der Startseite geladen. Ohne JavaScript bleiben alle Navigationslinks sichtbar; mit JavaScript lässt sich das Menü auf kleinen Bildschirmen öffnen und per Escape schließen. Die Jahresreihe ist dort horizontal scrollbar.

Die Zeitreise hat ihre eigene Übersichtsadresse: `/de/zeitreise` bzw. `/en/timeline`. Bestehende Stationsadressen bleiben gültig. Der Namenszug im Kopf führt zur Startseite; „Zeitreise“ im Menü und die Verweise in der Biografie führen zur Zeitreise.

```sh
php werkzeug/startseite.php           # Sprachfassungen, Quellenbezug, Navigation und Routen
```

## Mitmachen und Kontaktformular

`/de/mitmachen` und `/en/contribute` laden zu Erinnerungen, Ergänzungen und Mitarbeit ein.
Die Startseite und der gemeinsame Footer verlinken die Einladung. Das PHP-Formular sendet
nur an `stefan@jackieleven.com`, mit `Jackie Leven · Hommage <jackieleven@unpubli.sh>` als
Absender und der Besucheradresse als `reply_to`. Es veröffentlicht keine Einsendungen und
versendet keine automatischen Antworten an Besucher. Fotos kommen zunächst per E-Mail.

Der Versand läuft über die Resend REST API (PHP cURL, JSON). Voraussetzung sind PHP 8.1+,
cURL, mbstring und Sessions. Den Schlüssel mit **Sending access**, eingeschränkt auf
**unpubli.sh**, in `JACKIE_RESEND_API_KEY` hinterlegen oder `app/config.example.php` nach
`app/config.local.php` kopieren und dort eintragen. Die lokale Datei ist von Git ausgeschlossen;
`app/` wird durch `.htaccess` gesperrt. Bei nginx muss derselbe Zugriffsschutz eingerichtet
werden. Schlüssel niemals in das Repository oder den Browsercode schreiben. Die bestehenden
Cloudflare-MX-Einträge brauchen dafür keine Änderungen.

Das Formular verwendet Sitzungstoken, ein unsichtbares Zusatzfeld, Mindest-Ausfüllzeit,
eine Pause nach erfolgreichem Versand und ein gemeinsam gesperrtes Limit von fünf
Versandversuchen je Stunde/IP. Der Zähler liegt außerhalb des Webroots im temporären
Verzeichnis; `JACKIE_CONTACT_STATE_DIR` kann ein eigenes beschreibbares, privates
Verzeichnis festlegen. Er enthält Zeitpunkte und täglich wechselnde Hashes, keine
Nachrichteninhalte. Alte Zähler werden nach zwei Tagen beim nächsten Versuch entfernt.
Bei mehreren Servern muss dieser Speicher gemeinsam genutzt werden. Fehler erhalten die
Eingaben; ein Resend-Idempotenzschlüssel schützt identische Wiederholungen nach Zeitüberschreitungen.
Ohne Schlüssel bleibt der Senden-Knopf deaktiviert und die direkte E-Mail-Adresse sichtbar.

```sh
php werkzeug/kontakt.php               # Eingaben, CSRF, Rate-Limit, Ausgabe, DE/EN; ohne Versand
```

Die öffentliche Domain zeigt weiterhin die statische Interimsseite. Diese Änderung baut das
Formular in die vollständige PHP-App ein und veröffentlicht sie nicht automatisch.

## The Deep Pool auf der Website

Unter `/de/deep-pool` und `/en/deep-pool` beginnt die Lektüre direkt mit der ersten Kolumne vom Oktober 2002. Nur dort steht eine kurze Einführung über dem Artikel. Ein Zeitstrahl nach dem Vorbild der Zeitreise führt durch alle Texte und markiert den aktuellen Beitrag: auf großen Bildschirmen seitlich, auf schmalen als waagerechtes Band. Oben und unten führen schlichte Links zum vorherigen und nächsten Text sowie zu „Alle Texte“. Die vollständige Jahresübersicht liegt unter `/de/deep-pool/archiv` bzw. `/en/deep-pool/archive`. Jede Leseseite enthält den englischen Originaltext, Datum und Autor; Herkunft, Archivlink und aufklappbare Hinweise stehen unter dem Text. Neue redaktionelle Titel oder Inhaltsbeschreibungen sind nicht ergänzt.

`app/data/kolumnen.php` legt den veröffentlichten Bestand fest: 73 Beiträge bis einschließlich der Todesanzeige vom November 2011. Die drei später archivierten Beiträge von 2012 bleiben in der Recherche, erscheinen aber nicht auf der Website. `app/columns.php` liest die Originaldateien, ohne sie zu verändern. Bekannte Erscheinungsmonate aus den frühen Archiv-URLs werden berücksichtigt; ansonsten sind die späteren Datierungen ausdrücklich als Archivdatum gekennzeichnet. Die Todesanzeige trägt eine entsprechende Autorenangabe der Website-Betreiber. Wiederholte Seitenleistenbilder und zwei Navigationsreste in der September-Kolumne 2007 erscheinen nicht in der Lesefassung. Doppelte Monats- und Rubrikkopfzeilen am Anfang der alten Kolumnen werden durch den Lesekopf ersetzt; die Prosa bleibt unverändert.

```sh
php werkzeug/kolumnen.php              # Bestand, Wortlaut, Chronologie und Navigation
```

## Diskographie

Die **Diskographie** unter `/de/diskografie` bzw. `/en/discography` führt durch 88 Einträge von 1973 bis 2024: John St. Field, Doll by Doll, Concrete Bulletproof Invisible, Jackie Leven, Sir Vincent Lone und Jackie Balfour, außerdem Haunted Valley, Kooperationen und spätere Ausgaben. Der Jahreszeitstrahl folgt der Leseposition; die Auswahl nach Projekt und Veröffentlichungsart aktualisiert auch die Jahresnavigation. Bestehende Sprunglinks zu einzelnen Einträgen bleiben gültig; Sprachwechsel erhalten die Auswahl. Ohne JavaScript bleibt der gesamte Katalog lesbar.

Cover und Titel öffnen eine eigene Ausgabenseite, beispielsweise `/de/diskografie/1999-greek-notebook`. Sie zeigt Fakten, Titelliste und belegte Credits ohne Hintergrundtexte. Ihr Zeitstrahl führt zu einzelnen Ausgaben; Vor- und Zurückblättern folgt der aktuellen Filterauswahl. Die Rückkehr zur Übersicht erhält Filter, geöffnete Quellen und Leseposition – auch über den Zurück-Knopf des Browsers. Dafür werden der Verlaufseintrag und der Sitzungsspeicher im Browser verwendet; ohne JavaScript bleiben Detailseiten und Navigation zugänglich.

`app/data/diskografie-details.json` ergänzt die 88 Katalogeinträge um ausgabenspezifische Fakten und Quellen: 85 Titellisten mit insgesamt 881 Trackeinträgen sowie Credits für 22 Ausgaben. LP-Seiten, mehrere CDs und abweichende Titelreihenfolgen werden getrennt geführt. Für *The Last Flick of the Golden Wrench*, *The Meeting of Remarkable Men* und *Live from a Cornish Pub in Germany* ist keine vollständige Titelliste hinterlegt; dies steht auf der jeweiligen Seite. Bestehende Katalogeinträge, die mehrere Single-Varianten bündeln, zeigen diese als getrennte Titellisten. Quellen sind unter anderem die aktuelle Diskographie von Stuart Briers und Bob Astridge, konkrete MusicBrainz-Ausgaben und die Labelkataloge von MIG und Guerssen.

`app/data/diskografie.json` enthält die Ausgaben, zweisprachige Anmerkungen, Quellen und Coveradressen. Grundlage ist `research/05-diskografie.md`, ergänzt um Labelnachweise und Jackies Ankündigungen. Insbesondere: *Live from a Cornish Pub in Germany* ist durch seinen Septembertext 2008 belegt; *Troubadour Heart* war 2008 zunächst direkt erhältlich und kam 2009 regulär heraus; die Rockpalast-Ausgabe von 2024 enthält CD und DVD. Unveröffentlichte bzw. nicht gesichert erschienene Projekte sind ausdrücklich gekennzeichnet. Cover werden aus den verlinkten Label- und Musikkatalogen eingebunden; digitale Cover belegen keine historischen Erscheinungsdaten.

```sh
php werkzeug/diskografie.php          # Katalog, Details, Titellisten, Navigation, Quellen und DE/EN
```

## Hörlinks und YouTube-Liedbeispiele

`app/data/diskografie-hoerlinks.json` führt geprüfte digitale Albumangebote mit
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

`app/data/youtube-titel.json` ordnet 343 Liedtiteln je eine Liste von YouTube-Aufnahmen zu:
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
Album, und den Kanal. `diskografie_youtube()` liefert das Hörbeispiel,
`diskografie_youtube_fassungen()` die ganze Liste. Auf den derzeitigen Titellisten haben damit
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
Ausgabe, als Karte je Konzert. Grundlage ist `app/data/live-videos.json`: Konzert (Titel, Datum in
der belegten Genauigkeit, Herkunft `official` oder `fan`, zugehörige Ausgaben) mit Videos, Kanal,
Dauer und den enthaltenen Stücken samt Startsekunde. Auf der Ausgabe des Konzerts selbst stehen alle
Stücke, sonst nur die gemeinsamen Lieder; ein Klick auf ein Stück springt im Player an die Stelle.
Derzeit ist nur der vollständige Rockpalast-Film von MIG offiziell; Fan-Mitschnitte (ZDF Disco 1981,
Cropredy 2004, Manchester 2009, Essen 2010, Glasgow 2011) sind erfasst, werden aber nur mit
`'fan_videos' => true` in `app/config.local.php` oder `JACKIE_FAN_VIDEOS=1` eingebettet. Hochgeladen
heißt nicht lizenziert: Bei Fan- und TV-Mitschnitten ist der Uploader selten Rechteinhaber.

Eingebettet wird nur, was `werkzeug/livevideos.php` als einbettbar gespeichert hat (`embeddable`,
`checked`). Das Werkzeug fragt mit einem Schlüssel für die YouTube Data API (`youtube_api_key` bzw.
`JACKIE_YOUTUBE_API_KEY`) Einbettfreigabe, Sichtbarkeit, Altersbeschränkung und Sperren für
Deutschland ab, ohne Schlüssel nur oEmbed. Verweigert YouTube das Abspielen trotzdem, ersetzt sich
die Karte durch einen Link. Ohne JavaScript sind alle Karten und Stücke gewöhnliche YouTube-Links.

Vor dem Klick lädt die Seite nichts von YouTube. Die Vorschaubilder legt das Werkzeug lokal unter
`assets/bilder/live/` an (480×270 WebP, derzeit 3–12 KB); sie tragen `loading="lazy"` und werden
erst beim Scrollen geholt, ab dem vierten Konzert stehen sie eingeklappt und laden erst beim Öffnen.
`assets/js/livevideos.js` wird nur auf Seiten mit Live-Videos eingebunden; die Player-API von YouTube
und der Player (`youtube-nocookie.com`) folgen erst beim ersten Klick, je Konzert ein Player.

```sh
php werkzeug/livevideos.php            # Einbettfreigabe prüfen, fehlende Vorschauen anlegen (Netz)
php werkzeug/livevideos.php --vorschau # alle Vorschaubilder neu erzeugen
```

## Stimmen: externe Quellen

`/de/stimmen` bzw. `/en/voices` zeigt, was andere über Jackie geschrieben und gesagt haben: 709 Interviews,
Kritiken, Porträts, Konzertberichte, Nachrufe, Erinnerungen, Sendungen, Foren und Bücher von 1978 bis heute,
im Zeitstrahl wie die Diskographie und filterbar nach Art, Sprache und Zugang (frei lesbar, online, Webarchiv,
Bezahlschranke, verloren). Grundlage ist die Recherche in `research/quellen/` (eine Datei je Quelle, eigene
Inhaltsangabe); das Konzept steht in `research/ressourcen-seite-konzept.md`.

`werkzeug/quellen.php` erzeugt daraus `app/data/quellen.json`. Öffentlich werden nur Kopfdaten, die eigene
Inhaltsangabe und kurze Zitate im Original; Fundweg, Sicherheit, Widersprüche und Verweise auf Arbeitsdateien
bleiben intern. Stufen: 27 ausgewählte Quellen (Liste im Werkzeug), das Verzeichnis mit eigener Detailseite und
„weitere Quellen“, die je Jahr eingeklappt direkt aufs Original verweisen; Quellen, die nur aus zweiter Hand
bekannt sind, bleiben intern. Ein Feld `stufe:` im YAML-Kopf einer Quelle geht der Regel vor. Rezensionen sind
über die Albumtitel den Ausgaben zugeordnet und erscheinen dort als „Pressestimmen“.

Norwegische Zeitungsartikel stellt die Nationalbibliothek je Ausgabe teils unter CC BY-NC-ND oder CC BY-NC
frei. `--lizenzen` fragt das über `api.nb.no` ab und speichert es in `app/data/quellen-lizenzen.json`; frei
lizenzierte Artikel sind als „frei lesbar“ gekennzeichnet und tragen Namensnennung und Lizenz. Die Inhaltsangaben
gibt es bisher nur auf Deutsch; die englische Seite zeigt sie mit Hinweis und `lang="de"`. Die Seiten laden
keine Bilder und nichts von außen; die Übersicht ist ungepackt rund 490 KB groß, der Server sollte gzip liefern.

```sh
php werkzeug/quellen.php              # öffentliche Daten aus research/quellen/ erzeugen
php werkzeug/quellen.php --lizenzen   # zusätzlich Lizenzen der Nationalbibliothek abfragen (Netz)
php werkzeug/stimmen.php              # Daten, Übersicht, Detailseiten, Lizenzen, Filter und Routen prüfen
```

## Verzeichnisse

| Pfad | Inhalt |
|---|---|
| [`research/`](research/README.md) | Biografisches Kompendium: zwölf Akten mit Fußnoten, Zeitleiste mit Datierungskonflikten, Konzertkalender (470 Auftritte), Website-Geschichte — dazu `columns/` als Primärquelle |
| [`autobiografie/`](autobiografie/00-rahmen.md) | Die Pastiche: 15 Kapitel in Levens Stimme, **nicht von ihm geschrieben**. Dazu Rahmen, Kapitelplan und das Sprachdokument; Übersetzungen einzelner Teile in `autobiografie/<sprache>/` |
| `werkzeug/` | `messen.py` misst die Kapitel gegen den Korpus, `pruefen.py` meldet KI-Satzformen, `zitate.php` prüft die Zitate der Website gegen ihre Quellen, `uebersetzung.py` die Übersetzungen der Pastiche gegen das Original |
| `app/`, `index.php`, `assets/` | Die Website: Front Controller, Views, Stationsdaten, CSS/JS |
| `sketches/` | Design-Entwürfe A–E; die Seite folgt Entwurf E |
| `.dev/` | Werkstattbericht über die Entstehung |

## Die Autobiografie ist erfunden

**Der Text in `autobiografie/` stammt nicht von Jackie Leven.** Er ist eine Pastiche, geschrieben auf Grundlage dessen, was Leven selbst über sich erzählt hat. Jedes Kapitel trägt diesen Hinweis und endet mit einem Abschnitt „Belegt / erfunden", der beides einzeln auflistet.

Die Kennzeichnung ist keine Formalie. Leven war ein notorischer Ausschmücker — Bob Dylan als angeblicher Ko-Autor, eine Auftragsmörderin als Song-Inspiration, ein eigener Whisky, den sein Labelchef „a complete scam" nannte. Seine echten Erinnerungen klingen bereits wie Erfindungen. Ungekennzeichnete erfundene Ich-Prosa daneben würde seine Biografie endgültig unlesbar machen.

Auf der Website steht das Buch unter „Biografie“: jede Kapitelseite mit Pastiche-Hinweis, „Pastiche“ im Seitentitel, ohne Zitatauszeichnung und mit `noindex`. Die Seite liest die Kapitel direkt aus `autobiografie/`. Siehe [`autobiografie/00-rahmen.md`](autobiografie/00-rahmen.md), Abschnitt „Auf der Website“.

## Die Website lokal starten

DocumentRoot ist das Projektverzeichnis; die Seite läuft unter `https://jackieleven.localhost` (MAMP-vhost, Alias von `https://jackieleven`). Den `.localhost`-Namen behandelt der Browser-Pane von Claude Code als lokale Entwicklungsumgebung. Die `.htaccess` leitet alles auf `index.php` und sperrt `research/`, `autobiografie/`, `werkzeug/`, `app/` sowie alles, was mit einem Punkt beginnt — darunter `.git/` mit dem ganzen Repository und `.dev/`. Arbeitsmaterial ist nicht Teil der Website.

```sh
python3 werkzeug/messen.py              # Kapitel gegen den Korpus messen
python3 werkzeug/pruefen.py 07 08       # Kandidaten für KI-Sprache, mit führender Null
```

## Sprachen

Die Seite läuft auf Deutsch und Englisch unter `/de/…` und `/en/…`. `/` leitet nach `Accept-Language` des Browsers weiter, sonst auf Deutsch. Auch die Pfade sind übersetzt (`/de/zeitreise/1950-kirkcaldy`, `/en/timeline/1950-kirkcaldy`); ein Pfad in der falschen Sprache wird umgeleitet, Adressen ohne Präfix aus der Zeit vor der Umstellung ebenfalls.

**Die Zitate werden nie übersetzt.** Sie stehen einmal in `app/data/stationen.php` und erscheinen in jeder Sprachfassung im englischen Original mit `lang="en"`.

Text liegt je nach Art an drei Orten:

| Was | Wo | |
|---|---|---|
| Oberfläche, Monatsnamen, URL-Pfade | `app/lang/<code>.php` | Pflicht |
| Stationstexte (Titel, Label, Begleittext, Bildunterschrift) | `app/data/texte/<code>.php` | optional |
| Fließtextseiten (Über, Biografie) | `app/views/<code>/` | optional |

Eine neue Sprache: die drei Stellen anlegen und dann den Code in `SPRACHEN` in `app/bootstrap.php` eintragen — vorher ist sie von außen nicht erreichbar. Was fehlt, fällt auf Deutsch zurück und wird mit `lang="de"` ausgezeichnet; eine halb übersetzte Sprache funktioniert also schon. Die englischen Label sind bewusst keine Wort-für-Wort-Übertragung: „Station · Kirkcaldy" ist deutsch, auf Englisch steht nur der Ort.

```sh
php werkzeug/zitate.php                 # jedes Zitat Zeichen für Zeichen gegen seine Quelle
```

## Deployment der vollständigen PHP-Website

Die vollständige Website ist seit dem **23. Oktober 2026** unter
`https://jackieleven.com` öffentlich, auf Deutsch und Englisch. Erstes Live-Release:
`20261023174647-26786`, auf Grundlage von Commit `9b69425`.

Das Release wird über eine Positivliste gebaut, niemals durch Kopieren des Repositorys.
`ops/release-files.json` nennt die erlaubten Code-, Daten-, CSS-, JavaScript- und
Schriftdateien. Dazu kommen nur die im Kolumnenkatalog freigegebenen Texte, die
15 veröffentlichten Buchkapitel samt vorhandenen Übersetzungen und die von der App
ausgewählten Bilder. Neue Laufzeitdateien müssen ausdrücklich in die Liste aufgenommen
werden; Bildentwürfe, unbenutzte Fotos, übrige Recherche, Git-Daten, Werkzeuge und
`app/config.local.php` werden nicht übernommen. Symlinks in Quelldateien sind nicht erlaubt.

Jedes Release enthält einen eigenen Ordner `public/` mit dem öffentlichen Einstieg und
den Assets. **Nur dieser Ordner ist der DocumentRoot.** PHP-Code und die für die
Lesefassungen benötigten Texte liegen daneben und sind nicht direkt per HTTP erreichbar.
`release-manifest.sha256` verzeichnet die übertragenen Dateien mit ihren Prüfsummen.
API-Schlüssel und optionale Einstellungen kommen auf dem Server aus der PHP-FPM-Umgebung
(`JACKIE_RESEND_API_KEY`, `JACKIE_FAN_VIDEOS`). Für das Kontaktlimit sollte
`JACKIE_CONTACT_STATE_DIR` auf ein dauerhaftes, privates und für PHP beschreibbares
Verzeichnis außerhalb der Releases zeigen.

```sh
node werkzeug/browserablaeufe.cjs             # Navigation und Video-Ladezustände
php werkzeug/release.php                     # Paket, alle Routen und Assets; ohne Upload
bash ops/deploy.sh --prepare /tmp/jackie-release  # neuer Ordner; bleibt zur Prüfung liegen
bash ops/deploy.sh --deploy                  # Upload und atomarer Wechsel von site-current
python3 ops/check-site.py                    # Öffentliche Seiten, Assets, SEO und Formular-Bereitschaft
```

Das Deploy-Skript lädt ausschließlich das vorbereitete Paket per SSH/rsync auf den
bisherigen Server. Vor dem Wechsel prüft es Prüfsummen, PHP-Version, benötigte
CLI-Erweiterungen, PHP-Syntax und Beispielaufrufe. Die Pakete liegen unter
`/var/www/jackieleven/site-releases/`; `site-current` zeigt auf das aktive Paket,
`site-previous` auf dessen Vorgänger. Der Wechsel erfolgt erst nach erfolgreichen Prüfungen.
PHP-CLI und PHP-FPM müssen dieselbe geeignete Version und Erweiterungen verwenden.

Der aktive nginx-VHost verwendet `ops/nginx-site.conf` mit dem DocumentRoot
`/var/www/jackieleven/site-current/public` und dem eigenen PHP-8.3-FPM-Pool
`jackieleven` (`/run/php/jackieleven.sock`). Der Systembenutzer `jackieleven` besitzt
die privaten Session- und Kontaktlimit-Verzeichnisse unter `/var/lib/jackieleven/`.
Der Resend-Schlüssel steht ausschließlich in der root-lesbaren Poolkonfiguration
`/etc/php/8.3/fpm/pool.d/jackieleven.conf`, außerhalb der Releases.

Für die erste Aktivierung oder bewusste Konfigurationsänderungen:
`python3 ops/activate-site.py --activate`. Das Skript liest den lokal ignorierten
Schlüssel aus `.dev/resend-api-key` und übergibt ihn über SSH-stdin, ohne Ausgabe
oder Kommandozeilenargument. `ops/install-site.py` sichert Konfigurationen unter
`/var/backups/jackieleven-site/`, prüft PHP-FPM und nginx und kontrolliert die
Seiten am Origin. Bei einem Fehler stellt es die vorherigen Konfigurationen wieder
her. Cloudflare-Netze werden über die offizielle IP-API abgerufen; nur deren
Besucher-IP-Header werden für das Kontaktlimit vertraut. Andere VHosts und
E-Mail-DNS-Einträge werden nicht geändert.

Die vorherige Interimsseite bleibt unter `/var/www/jackieleven/current` erhalten.
Die Konfigurationssicherung vor dem ersten Livegang liegt unter
`/var/backups/jackieleven-site/20261023174928074550/`. Für normale Inhaltsupdates
reicht `ops/deploy.sh --deploy`; die Aktivierung muss nicht wiederholt werden.

### Sicherheitskonfiguration

`ops/activate-site.py --activate` installiert außerdem die namensspezifischen
nginx-Regeln aus `ops/nginx-security.conf` und die Zustandsbereinigung. Direkte
öffentliche HTTP-/HTTPS-Aufrufe dieses VHosts erhalten 403; zugelassen sind die
veröffentlichten Cloudflare-Netze und Loopback für lokale Betriebsprüfungen.
Die Prüfung verwendet den ursprünglichen TCP-Peer (`$realip_remote_addr`), nicht
den vom Proxy gemeldeten Besucher. Die HTTP-ACME-Challenge bleibt für die
Zertifikatserneuerung erreichbar. Die Cloudflare-Netzliste wird bei jeder
Konfigurationsaktivierung neu geladen. Full (Strict) bleibt aktiv. Das ist eine
IP-basierte Zugangssperre, keine zonenspezifische gegenseitige TLS-Authentisierung.

Vor PHP gelten je Besucher 5 Anfragen/Sekunde mit Burst 30 und höchstens 10
gleichzeitige Anfragen. Die Kontaktpfade beider Sprachen teilen sich zusätzlich
10 Anfragen/Minute mit Burst 5, auch für ungültige Eingaben und GET-Aufrufe.
Abgewiesene Anfragen liefern 429. Statische Assets zählen nicht mit. Das
PHP-Versandlimit bleibt zusätzlich bestehen. Anfragerümpfe sind auf 128 KiB
begrenzt, ausreichend für die URL-kodierte maximale Nachrichtenlänge.

Die CSP erlaubt eigene Skripte und die konkret benötigten YouTube-API-Pfade;
Inline-JavaScript und eval bleiben gesperrt. Nur die vorgesehenen YouTube-Player
dürfen eingebettet werden, während die Hommage selbst nicht in fremden Frames
erscheinen darf. Bildquellen umfassen die vorhandenen Coverdienste und die
Nationalbibliothek. Inline-Stile bleiben für die Player erlaubt. Kamera,
Mikrofon, Standort, Zahlung und USB sind per Permissions-Policy deaktiviert.

`jackieleven-clean-state.timer` läuft stündlich mit bis zu fünf Minuten Streuung.
Der Dienst läuft als `jackieleven` und entfernt nur passende Sitzungsdateien
nach sechs Stunden sowie Zähler nach zwei Tagen. Gesperrte Dateien, Symlinks und
fremde Dateinamen bleiben erhalten. Die Bereinigung protokolliert nur Anzahlen.

```sh
python3 werkzeug/cleanup.py                   # Ablauf, Sperren, Symlinks, Aufbewahrung
php werkzeug/kontakt.php                      # Formularprüfung ohne Mailversand
python3 ops/check-site.py                     # normale Live-Prüfung
python3 ops/check-security.py --origin-ip 77.42.46.154
```

Die letzte Prüfung erzeugt acht absichtlich ungültige Formular-POSTs, prüft die
429-Sperre vor PHP und wartet auf deren Erholung. Nicht parallel zu anderen
Kontaktformular-Tests ausführen. Sie versendet keine Nachricht.

## Interimsseite auf jackieleven.com

Am 23. Oktober 2026 wurde zunächst eine eigenständige, statische Interimsseite auf
dem vorhandenen Hetzner-Server `77.42.46.154` (SSH-Port `29742`) eingerichtet.
Sie wurde am selben Tag durch die vollständige PHP-Website ersetzt.
Cloudflare hat zwei proxied A-Records für `@` und `www`; die Mail-Einträge bleiben bestehen.
TLS verwendet Full (Strict), ein automatisch erneuertes Let's-Encrypt-Zertifikat für beide
Namen und eine Weiterleitung von HTTP sowie `www` auf `https://jackieleven.com`.

`interim/` enthält die englischsprachige Seite. Das Deployment übernimmt ausschließlich diese
Dateien, zwei vorhandene Schriftdateien und deren Lizenzen. Auf dem Server liegen die
Versionen unter `/var/www/jackieleven/releases/`; `current` wählt die aktive Fassung,
`previous` die vorherige. Die vollständige PHP-Website wird damit nicht veröffentlicht.
Die Interimsseite trägt vorläufig `noindex`; `robots.txt` schließt Crawling aus.

```sh
bash ops/deploy-interim.sh --prepare  # Paket ohne Upload vorbereiten
bash ops/deploy-interim.sh            # Interimsseite hochladen und atomar aktivieren
python3 ops/check-interim.py          # Öffentliche Seite, Schriften und Weiterleitungen prüfen
```

Die nginx-Konfiguration steht in `ops/nginx-interim.conf`; die HTTP-Fassung dient nur der
ersten Zertifikatsausstellung. `ops/install-interim.py` installiert ausschließlich den eigenen
VHost, sichert dessen vorherigen Stand und prüft nginx vor dem Reload. Auf dem Server liegt
der VHost unter `/etc/nginx/sites-available/jackieleven.com`, seine Sicherungen unter
`/var/backups/jackieleven-nginx/`. Der Zertifikatshook `ops/renew-interim-cert.sh` ist unter
`/etc/letsencrypt/renewal-hooks/deploy/90-jackieleven-nginx` installiert.

## Rechte — bitte vor einer Veröffentlichung lesen

**Dieses Repository ist privat, und das hat Gründe.**

- **`research/columns/`** enthält die wiederhergestellten Originaltexte. Die Rechte daran liegen nicht bei uns. Die Rubrik „The Deep Pool“ macht den festgelegten Bestand als Lesefassung mit Quellen- und Rechtehinweis zugänglich; die Recherchedateien selbst bleiben gesperrt.
- **`assets/bilder/` und `sketches/assets/`** sind echte Pressefotos. Der Fotograf ist nicht ermittelt.
- **`research/09-alan-moffatt-genealogie.md`** enthält Registerdaten, Testamentsangaben und Familienspuren zu einer realen Person und ihren Angehörigen.
- **`autobiografie/`** darf nach dem eigenen Rahmen nirgends als Levens Wort erscheinen. Auf der Website steht es gekennzeichnet und mit `noindex`; vor einer Veröffentlichung ist zu entscheiden, ob das reicht.

Die Zeitreise verwendet kurze, wortgetreue Zitate mit Archivlinks. Die Rubrik „The Deep Pool“ gibt dagegen die Originalbeiträge einschließlich der darin enthaltenen Zitate und Liedpassagen wieder.


## Suchmaschinen und Vorschauen

`app/seo.php` verwaltet die Metadaten und die öffentliche Adresse
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
in `SEO_ORIGIN` und `seo_live()` angepasst werden. Fehlerseiten und HTML-Fragmente
sind ebenfalls `noindex`.

Prüfen: `php werkzeug/seo.php` und `php werkzeug/release.php`.
Die vollständige Website wird über `ops/nginx-site.conf` ausgeliefert; ihre
öffentliche Indexierung ist freigegeben. Die stillgelegte Interimsseite behält
ihre eigenen Indexierungssperren. `ops/check-site.py` prüft die öffentliche
Sitemap, robots.txt und Inhaltsseiten. Die Sitemap kann in der Google Search
Console eingereicht werden.
Eine Search-Console-Verifizierung wird nicht ohne den tatsächlichen
Verifizierungscode in den Quelltext eingetragen.
