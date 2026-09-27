# Jackie Leven

Eine private Hommage an den schottischen Songwriter **Jackie Leven** (18. Juni 1950, Kirkcaldy – 14. November 2011, Hampshire). Keine offizielle Seite, kein Nachlass, keine Plattenfirma.

Das Projekt besteht aus drei Teilen: einer Recherchegrundlage, einer erfundenen Autobiografie in seiner Stimme und einer PHP-Website, die beides zugänglich macht.

## Die Grundlage: seine eigenen Texte

Leven hat von Oktober 2002 bis Herbst 2011 auf seinen eigenen Websites geschrieben — erst die Monatskolumne *The Deep Pool* auf jackieleven.com, ab 2008 Blog und Rubriken auf jackieleven.co.uk. Beide Seiten sind offline; jackieleven.co.uk wurde 2024 vom Hoster gesperrt.

Über das Internet Archive ließen sich **76 dieser Texte wiederherstellen, rund 90.000 Wörter** — der einzige Ort, an dem er ausführlich mit eigener Stimme über sich spricht. Sie liegen wortgetreu in [`research/columns/`](research/columns/README.md), je eine Datei pro Beitrag, mit Rubrik, Datum, Quell-URL und Archivlink im YAML-Kopf.

Dieser Korpus ist zugleich die **Faktenbasis** und der **stilistische Maßstab** des Projekts.

## Verzeichnisse

| Pfad | Inhalt |
|---|---|
| [`research/`](research/README.md) | Biografisches Kompendium: zwölf Akten mit Fußnoten, Zeitleiste mit Datierungskonflikten, Konzertkalender (470 Auftritte), Website-Geschichte — dazu `columns/` als Primärquelle |
| [`autobiografie/`](autobiografie/00-rahmen.md) | Die Pastiche: 15 Kapitel in Levens Stimme, **nicht von ihm geschrieben**. Dazu Rahmen, Kapitelplan und das Sprachdokument |
| `werkzeug/` | `messen.py` misst die Kapitel gegen den Korpus, `pruefen.py` meldet KI-Satzformen, `zitate.php` prüft die Zitate der Website gegen ihre Quellen |
| `app/`, `index.php`, `assets/` | Die Website: Front Controller, Views, Stationsdaten, CSS/JS |
| `sketches/` | Design-Entwürfe A–E; die Seite folgt Entwurf E |
| `.dev/` | Werkstattbericht über die Entstehung |

## Die Autobiografie ist erfunden

**Der Text in `autobiografie/` stammt nicht von Jackie Leven.** Er ist eine Pastiche, geschrieben auf Grundlage dessen, was Leven selbst über sich erzählt hat. Jedes Kapitel trägt diesen Hinweis und endet mit einem Abschnitt „Belegt / erfunden", der beides einzeln auflistet.

Die Kennzeichnung ist keine Formalie. Leven war ein notorischer Ausschmücker — Bob Dylan als angeblicher Ko-Autor, eine Auftragsmörderin als Song-Inspiration, ein eigener Whisky, den sein Labelchef „a complete scam" nannte. Seine echten Erinnerungen klingen bereits wie Erfindungen. Ungekennzeichnete erfundene Ich-Prosa daneben würde seine Biografie endgültig unlesbar machen.

Siehe [`autobiografie/00-rahmen.md`](autobiografie/00-rahmen.md).

## Die Website lokal starten

DocumentRoot ist das Projektverzeichnis; die Seite läuft unter `https://jackieleven` (MAMP-vhost). Die `.htaccess` leitet alles auf `index.php` und sperrt `research/`, `autobiografie/`, `werkzeug/`, `app/` sowie alles, was mit einem Punkt beginnt — darunter `.git/` mit dem ganzen Repository und `.dev/`. Arbeitsmaterial ist nicht Teil der Website.

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

- **`research/columns/`** enthält Levens eigene Texte im Volltext. Die Rechte daran liegen nicht bei uns. Arbeitsgrundlage, keine Veröffentlichung.
- **`assets/bilder/` und `sketches/assets/`** sind echte Pressefotos. Der Fotograf ist nicht ermittelt.
- **`research/09-alan-moffatt-genealogie.md`** enthält Registerdaten, Testamentsangaben und Familienspuren zu einer realen Person und ihren Angehörigen.
- **`autobiografie/`** darf nach dem eigenen Rahmen nirgends als Levens Wort erscheinen.

Auf der Website selbst steht deshalb kein Songtext, und jedes Zitat ist kurz, wortgetreu und mit Archivlink belegt.
