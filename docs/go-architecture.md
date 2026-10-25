# Architektur der Go-Migration

Die erste Ausbaustufe ersetzt die serverseitige Laufzeit und bewahrt den bestehenden öffentlichen Vertrag: URLs, Weiterleitungen, Sprachen, Inhalte, HTML-Struktur, CSS-/JavaScript-Anknüpfungspunkte, Metadaten und Formularverhalten. Ontologie und Suche folgen als gesonderte Funktionen. Damit können Unterschiede der Migration von späteren Produktänderungen getrennt geprüft werden.

## Laufzeit und Inhalte

`cmd/jackieleven` startet einen `net/http`-Server. `internal/site` enthält Routing, Inhaltsaufbereitung, SEO, Templates und Kontakt. Die Anwendung benötigt keine Bibliothek außerhalb der Go-Standardbibliothek und keinen PHP-Prozess.

`data/` enthält die bisherigen strukturierten Kataloge und Übersetzungen als JSON. Go lädt sie beim Start. Die Kataloge behalten ihre Feldnamen in Inhaltsrecords; Routing-, Sitzungs- und Konfigurationszustand haben eigene Go-Typen. Die offen gehaltenen Katalogrecords erleichtern zunächst die überprüfbare Übertragung des bestehenden Datenbestands. Sie sind noch kein ontologisches Domänenmodell.

`templates/` enthält echte `html/template`-Vorlagen. Es gibt keine vorgerenderten Seitensnapshots als Laufzeitquelle. Pro Anfrage werden Sprache, Route und Templatefunktionen an einen eigenen Request gebunden. Gemeinsame Inhaltsdaten werden nach dem Laden nur gelesen. Dieser Unterschied zu PHP ist wesentlich: Ein Go-Prozess verarbeitet mehrere Anfragen gleichzeitig und darf Sprach- oder Routenzustand nicht in veränderlichen globalen Variablen halten.

Die ausgewählten Texte in `research/columns/` und `autobiografie/` bleiben Markdownquellen. Der bewusst kleine Renderer reproduziert die bestehenden Leseregeln einschließlich Verszeilen, wiederholter alter Überschriften und Übersetzungsfallbacks. Die Go-Fassung wurde gegen alle 73 veröffentlichten Kolumnenmodelle und HTML-Lesefassungen, beide Kapitelsprachen und 202 Markdownbeispiele verglichen.

## HTML und Adressen

`html/template` übernimmt kontextbezogenes Escaping. Freigegebenes HTML entsteht nur an begrenzten Stellen: aus bereits gerenderten eigenen Templates, dem vorab escapenden Markdownleser und ausdrücklich erlaubten Attributfragmenten. Die komplette öffentliche Identität bleibt `https://jackieleven.com`; fremde Hostheader erzeugen keine beliebigen Canonical-Adressen. Lokale und andere nichtproduktive Hosts bleiben noindex.

Nur `/assets/` liefert Dateien aus. Daten, Templates, Forschung und Punktdateien erhalten keine allgemeine Dateiauslieferung. Releasepakete erlauben zusätzlich nur eine explizite Auswahl der tatsächlich benötigten Dateien. Ein Produktionsprozess liest seine Inhalte aus einem einmal aufgelösten Releaseverzeichnis, einschließlich Assets.

## Kontakt und Parallelität

Kontaktkonfiguration kommt ausschließlich aus Prozessvariablen. Tests können Turnstile- und Versandfunktionen ersetzen, ohne echte Anbieter zu kontaktieren. Sitzungen, Formulartokens, Wiederholungskennungen und IP-Limits liegen in privaten Zustandsdateien. Dateisperren serialisieren konkurrierende Verarbeitung derselben Sitzung und schützen die IP-Zähler. Dadurch bleiben CSRF-Lebensdauer, Formularalter, mehrere offene Tabs, Abkühlzeit und Wiederholungsschutz auch bei Parallelität und Neustart erhalten.

Ein Versandversuch mit unverändertem Formularinhalt behält nach einem ungewissen Ergebnis seine Idempotenzkennung. Der erfolgreiche Versand wird unter derselben Sitzungssperre vermerkt. Externe Antworten müssen vollständig und valide sein; Anfrage- und Antwortgrößen sind begrenzt. Sensible Formularinhalte und Schlüssel werden nicht protokolliert.

Proxyheader gelten nur bei aktiviertem `-trust-proxy` und einem direkten Loopback-Peer. nginx überschreibt sie mit den eigenen, aus vertrauenswürdigen Quellen gewonnenen Werten. Der Backendport bleibt lokal. Bei SIGTERM wartet der Hauptprozess auf den geordneten Abschluss laufender Anfragen, höchstens bis zur dokumentierten Shutdownfrist.

## Nachweise und Grenzen

Der HTTP-Abgleich prüft sämtliche Sitemapziele plus Alias-, Sprach-, Filter-, Fragment- und Fehlerfälle. Normalisierungen sind in `werkzeug/parity.md` aufgeführt. Insbesondere bleiben echte Inline-Leerzeichen und geschützte Leerzeichen erhalten; als JSON konsumierte Attribute werden nach Datenwerten verglichen.

Der eingefrorene PHP-Snapshot ist eine Testreferenz, kein Bestandteil des Go-Servers. Ein Apache-generierter Fehler für einen kodierten Pfadtrenner wird ausdrücklich nur auf 404 und fehlende Datenpreisgabe geprüft; sein Fehlerseiten-HTML ist keine behauptete Gleichheit.

Zusätzlich wurden neun Seitentypen bei 1440×1000 und 390×844 im Browser verglichen: gleiche DOM-Geometrie und pixelgleiche Screenshots nach abgeschlossenem Laden der Bilder. Interaktionsprüfungen decken dynamische Zeitreise, Sprachwechsel, Verlauf und Filterkontext ab. Diese Nachweise betreffen die geprüften Zustände und ersetzen keine Behauptung über jede denkbare Browser- oder Netzwerksituation.

Die separate Linux-Testinstanz ist auf Hetzner installiert und unter `https://unpubli.sh/jackieleven/` geprüft; Details stehen in `ops/GO-PREVIEW.md`. Echte Anbieterintegration und ein Produktionswechsel bilden weiterhin eine eigene Abnahme. Die bisherige Seite bleibt bis dahin verfügbar.
