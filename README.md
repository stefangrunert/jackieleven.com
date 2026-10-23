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

## Interimsseite auf jackieleven.com

Seit dem 23. Oktober 2026 zeigt `https://jackieleven.com/` eine eigenständige, statische
Interimsseite auf dem vorhandenen Hetzner-Server `77.42.46.154` (SSH-Port `29742`).
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
