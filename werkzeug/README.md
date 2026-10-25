# Wartungswerkzeuge

Die Website läuft ausschließlich als Go-Prozess. Die Werkzeuge hier bearbeiten
neutrale JSON-Kataloge in `data/` und die erhaltenen Quellen in `research/` bzw.
`autobiografie/`. Kein Werkzeug startet einen alten Anwendungsprozess oder liest
eine lokale Konfigurationsdatei mit Zugangsdaten.

## Inhalte erzeugen und prüfen

```sh
python3 werkzeug/quellen.py --check       # offline: vollständigen Katalog im Speicher reproduzieren
python3 werkzeug/inhalte.py              # Integrität, Übersetzungen, Verweise und lokale Medien
python3 werkzeug/zitate.py               # Stationszitate wortgetreu gegen archivierte Texte
python3 werkzeug/quellen.py              # geprüften Quellenkatalog atomar neu schreiben
```

`quellen.py` übernimmt die bisherigen Publikationsregeln: explizite redaktionelle
Stufen, ausgewählte Quellen, private/interne Ausschlüsse, Entfernung von
Arbeitsdateiverweisen, Kurztexte, wörtliche Belege, Korrekturen und Zuordnung zu
Diskografieausgaben. Englische Fassungen werden nur bei passender Prüfsumme
veröffentlicht. `--check` schreibt nichts und darf nicht mit einem Netzwerk-Update
kombiniert werden. Die unveränderte Ausgabe umfasst derzeit 741 öffentliche und
25 ausgeschlossene Quellen, ohne veraltete Übersetzungen.

`inhalte.py` prüft Veröffentlichungsgrenzen, eindeutige IDs, Quellen und
Ausgabenbezüge, DE/EN-Felder, Albumangebote und Medienanbieter, Lied-/Videobezüge,
Einbett-Prüfdaten, lokale Vorschauen, Startseitenauszüge und die Hör-Auswahl.
Darstellung, Routing, Filter, Sessions, SEO und Releaseverhalten prüfen die
Go-Tests, HTTP-Vertragsprüfungen und Browserabläufe.

## Bewusste Netzwerk- und Bildaktualisierungen

```sh
python3 werkzeug/quellen.py --lizenzen    # Nationalbibliothek: Lizenz-/Zugangsmetadaten aktualisieren
python3 werkzeug/quellen-scans.py        # NB-IIIF-Manifeste und belegte Seitenreferenzen
python3 werkzeug/quellen-auszuege.py      # lokale Bildausschnitte + öffentlicher Katalog
python3 werkzeug/livevideos.py           # YouTube-Freigaben + fehlende lokale Vorschauen
python3 werkzeug/livevideos.py --vorschau # alle lokalen Videovorschauen erneuern
```

Die Quellen-/Katalogprüfungen benötigen nur die Python-Standardbibliothek.
`quellen-scans.py` verwendet zusätzlich `curl`. Die beiden Bildgeneratoren
benötigen Pillow; `livevideos.py` lädt Pillow erst, wenn tatsächlich ein Bild
geschrieben werden muss.

Der Video-Updater verwendet ausschließlich `JACKIE_YOUTUBE_API_KEY` aus seiner
Prozessumgebung. Mit Schlüssel prüft er über die Data API Einbettfreigabe,
Öffentlichkeit, Altersbeschränkung und Verfügbarkeit in Deutschland. Ohne
Schlüssel verwendet er oEmbed; Länder- und Altersbeschränkungen sind damit nicht
erfasst. Die Vorschauen bleiben lokale 480×270-WebP-Bilder. Diese Abfragen gehören
zum bewusst gestarteten Wartungslauf und finden nie während eines Seitenaufrufs
statt. Tests ersetzen alle Netzwerktransporte durch lokale Antworten.

## Regressionen

```sh
python3 -B -m unittest discover -s werkzeug -p 'test_*.py'
python3 werkzeug/cleanup.py
node werkzeug/browserablaeufe.cjs
go test -race ./...
go vet ./...
```

Die neuen Werkzeugtests vergleichen den gesamten erzeugten Quellenkatalog mit
dem vorhandenen `data/quellen.json`, prüfen Publikationsfilter und veraltete
Übersetzungen sowie die Video-Freigabekriterien, API-Bündelung, oEmbed-Fehler,
Vorschauauswahl und Bildmaße ohne Netz. Der Cleanup-Test verwendet temporäre
Go-Sessions und Zähler, einschließlich aktiver Locks, Symlinks und fremder Dateien.

Die alten interpreterspezifischen Runtime-, Router- und Paketprüfungen wurden
entfernt. Aktuell maßgeblich sind die Go-Tests, `ops/prepare-go-release.py` und die
HTTP-/Browserprüfungen. Die literarischen Analysewerkzeuge `messen.py`, `pruefen.py`
und `uebersetzung.py` bleiben unverändert verfügbar.

Der eingefrorene Migrationsvergleich und seine dokumentierten Normalisierungen
stehen in [parity.md](parity.md). Er kann die gespeicherten Antwortverträge ohne
laufende Referenz verwenden. Der zusätzliche historische Kontaktvergleich
benötigt nur eine ausdrücklich isolierte externe HTTP-Referenz; deren alten
Prozess installiert oder startet dieses Repository nicht.
