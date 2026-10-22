# Jackie Leven

Eine private Hommage an den schottischen Songwriter **Jackie Leven** (18. Juni 1950, Kirkcaldy – 14. November 2011, Hampshire). Keine offizielle Seite, kein Nachlass, keine Plattenfirma.

Das Projekt besteht aus drei Teilen: einer Recherchegrundlage, einer erfundenen Autobiografie in seiner Stimme und einer PHP-Website, die beides zugänglich macht.

## Die Grundlage: seine eigenen Texte

Leven hat von Oktober 2002 bis Herbst 2011 auf seinen eigenen Websites geschrieben — erst die Monatskolumne *The Deep Pool* auf jackieleven.com, ab 2008 Blog und Rubriken auf jackieleven.co.uk. Beide Seiten sind offline; jackieleven.co.uk wurde 2024 vom Hoster gesperrt.

Über das Internet Archive ließen sich **76 dieser Texte wiederherstellen, rund 90.000 Wörter** — der einzige Ort, an dem er ausführlich mit eigener Stimme über sich spricht. Sie liegen wortgetreu in [`research/columns/`](research/columns/README.md), je eine Datei pro Beitrag, mit Rubrik, Datum, Quell-URL und Archivlink im YAML-Kopf.

Dieser Korpus ist zugleich die **Faktenbasis** und der **stilistische Maßstab** des Projekts.

## The Deep Pool auf der Website

Unter `/de/deep-pool` und `/en/deep-pool` beginnt die Lektüre direkt mit der ersten Kolumne vom Oktober 2002. Nur dort steht eine kurze Einführung über dem Artikel. Ein Zeitstrahl nach dem Vorbild der Zeitreise führt durch alle Texte und markiert den aktuellen Beitrag: auf großen Bildschirmen seitlich, auf schmalen als waagerechtes Band. Oben und unten führen schlichte Links zum vorherigen und nächsten Text sowie zu „Alle Texte“. Die vollständige Jahresübersicht liegt unter `/de/deep-pool/archiv` bzw. `/en/deep-pool/archive`. Jede Leseseite enthält den englischen Originaltext, Datum und Autor; Herkunft, Archivlink und aufklappbare Hinweise stehen unter dem Text. Neue redaktionelle Titel oder Inhaltsbeschreibungen sind nicht ergänzt.

`app/data/kolumnen.php` legt den veröffentlichten Bestand fest: 73 Beiträge bis einschließlich der Todesanzeige vom November 2011. Die drei später archivierten Beiträge von 2012 bleiben in der Recherche, erscheinen aber nicht auf der Website. `app/columns.php` liest die Originaldateien, ohne sie zu verändern. Bekannte Erscheinungsmonate aus den frühen Archiv-URLs werden berücksichtigt; ansonsten sind die späteren Datierungen ausdrücklich als Archivdatum gekennzeichnet. Die Todesanzeige trägt eine entsprechende Autorenangabe der Website-Betreiber. Wiederholte Seitenleistenbilder und zwei Navigationsreste in der September-Kolumne 2007 erscheinen nicht in der Lesefassung. Doppelte Monats- und Rubrikkopfzeilen am Anfang der alten Kolumnen werden durch den Lesekopf ersetzt; die Prosa bleibt unverändert.

```sh
php werkzeug/kolumnen.php              # Bestand, Wortlaut, Chronologie und Navigation
```

## Diskographie

Die **Diskographie** unter `/de/diskografie` bzw. `/en/discography` führt durch 88 Einträge von 1973 bis 2024: John St. Field, Doll by Doll, Concrete Bulletproof Invisible, Jackie Leven, Sir Vincent Lone und Jackie Balfour, außerdem Haunted Valley, Kooperationen und spätere Ausgaben. Der Jahreszeitstrahl folgt der Leseposition; die Auswahl nach Projekt und Veröffentlichungsart aktualisiert auch die Jahresnavigation. Links zu einzelnen Einträgen verwenden stabile Anker, Sprachwechsel erhalten die Auswahl. Ohne JavaScript bleibt der gesamte Katalog lesbar.

`app/data/diskografie.json` enthält die Ausgaben, zweisprachige Anmerkungen, Quellen und Coveradressen. Grundlage ist `research/05-diskografie.md`, ergänzt um Labelnachweise und Jackies Ankündigungen. Insbesondere: *Live from a Cornish Pub in Germany* ist durch seinen Septembertext 2008 belegt; *Troubadour Heart* war 2008 zunächst direkt erhältlich und kam 2009 regulär heraus; die Rockpalast-Ausgabe von 2024 enthält CD und DVD. Unveröffentlichte bzw. nicht gesichert erschienene Projekte sind ausdrücklich gekennzeichnet. Cover werden aus den verlinkten Label- und Musikkatalogen eingebunden; digitale Cover belegen keine historischen Erscheinungsdaten.

```sh
php werkzeug/diskografie.php          # Katalog, Identitäten, Quellen und Sprachfassungen
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

## Rechte — bitte vor einer Veröffentlichung lesen

**Dieses Repository ist privat, und das hat Gründe.**

- **`research/columns/`** enthält die wiederhergestellten Originaltexte. Die Rechte daran liegen nicht bei uns. Die Rubrik „The Deep Pool“ macht den festgelegten Bestand als Lesefassung mit Quellen- und Rechtehinweis zugänglich; die Recherchedateien selbst bleiben gesperrt.
- **`assets/bilder/` und `sketches/assets/`** sind echte Pressefotos. Der Fotograf ist nicht ermittelt.
- **`research/09-alan-moffatt-genealogie.md`** enthält Registerdaten, Testamentsangaben und Familienspuren zu einer realen Person und ihren Angehörigen.
- **`autobiografie/`** darf nach dem eigenen Rahmen nirgends als Levens Wort erscheinen. Auf der Website steht es gekennzeichnet und mit `noindex`; vor einer Veröffentlichung ist zu entscheiden, ob das reicht.

Die Zeitreise verwendet kurze, wortgetreue Zitate mit Archivlinks. Die Rubrik „The Deep Pool“ gibt dagegen die Originalbeiträge einschließlich der darin enthaltenen Zitate und Liedpassagen wieder.
