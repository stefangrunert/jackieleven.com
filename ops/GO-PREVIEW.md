# Separate Go-Testinstanz auf Hetzner

Ziel: `https://unpubli.sh/jackieleven/`. Diese Instanz ersetzt weder die PHP-Seite noch den produktiven Jackie-Leven-VHost.

## Aufbau

- Go-Dienst: `jackieleven-go-preview.service`, eigener Systembenutzer `jackieleven-preview`.
- Backend: ausschließlich `127.0.0.1:18766`, URL-Mount `/jackieleven` bleibt beim Proxying erhalten.
- Releases: `/var/www/jackieleven-go-preview/releases/RELEASE`; die Unit verwendet jeweils den unveränderlichen absoluten Releasepfad.
- Privater Zustand: `/var/lib/jackieleven-go-preview/contact`.
- nginx: ein zusätzliches Include im vorhandenen HTTPS-VHost `unpublish`, eigenes Snippet und eigene Limitzonen.
- Alle Vorschauantworten sind `noindex`. Canonical, hreflang, JSON-LD und Sitemap behalten die produktive Identität unter `jackieleven.com`. Sichtbare Navigation, Assets und Formular-Weiterleitungen bleiben im Vorschaupfad.

Die drei Kontakt-Schlüssel sind in der Preview-Unit ausdrücklich leer. Damit lässt sich die Oberfläche prüfen, es werden aber keine echten Nachrichten versandt. Echte Turnstile-/Resend-Integration ist ein eigener Folgeschritt; produktive Geheimnisse werden nicht automatisch in eine Testinstanz kopiert.

## Prüfen und installieren

```sh
go test -race ./...
go vet ./...
node werkzeug/browserablaeufe.cjs
python3 -B ops/test_go_preview.py
python3 ops/prepare-go-release.py NEW_RELEASE_DIRECTORY --goos linux --goarch amd64
```

`install-go-preview.py` wird zusammen mit `jackieleven-preview.service`, `nginx-preview-location.conf` und `nginx-preview-limits.conf` auf den Server übertragen. Das Release muss vorher in ein neues Releaseverzeichnis hochgeladen werden. Der Installer wird als root mit `--release RELEASE --expected-vhost-sha SHA256` ausgeführt.

Vor einer Änderung prüft er alle Release-Prüfsummen und die erwartete Prüfsumme der bestehenden VHostdatei. Dadurch überschreibt er keine zwischenzeitliche Änderung. Er sichert vorhandene Konfigurationsdateien nach `/var/backups/jackieleven-go-preview/`, prüft die neue Unit mit `systemd-analyze verify` und nginx mit `nginx -t`, startet nur den Preview-Dienst und prüft zuerst den Backend- und anschließend den lokalen HTTPS-Pfad. Fehler stellen die gesicherten Dateien und den vorherigen Dienstzustand wieder her. Ein solcher Fehler wurde vor Einsatz simuliert und die Wiederherstellung geprüft.

Nach der Installation sind öffentliche HTTPS-Aufrufe, die Referenz-Startseiten, Serverstatus und die unveränderte PHP-VHost-Prüfsumme zu kontrollieren. Der Preview-Port darf nicht an eine öffentliche Schnittstelle gebunden sein.

## Parität beim Unterpfad

Der eingefrorene PHP-Seitenvertrag bleibt maßgeblich. Das Prefix-Prüfwerkzeug darf ausschließlich sichtbare interne Mountadressen normalisieren; produktive Canonical-/JSON-LD-Adressen bleiben unangetastet. Cookiepfad und noindex werden zusätzlich geprüft. Zwei bewusst veränderte Assets benötigen eigene Nachweise: `home.css` verwendet stylesheet-relative Fontadressen, und `zeitgraph.js` trennt bei einem Mount sichtbare Navigationsadressen von SEO-Adressen. Diese Dateien sind deshalb nicht mehr bytegleich mit der eingefrorenen PHP-Fassung. Die genauen Unterschiede werden ausgewiesen; der Defaultbetrieb wird weiterhin auf identisches Verhalten geprüft.

## Rücknahme

Vor einer Rücknahme die gesicherte VHostdatei mit dem aktuellen Stand vergleichen, damit spätere Änderungen anderer Anwendungen erhalten bleiben. Ausschließlich das Include `snippets/jackieleven-preview.conf` entfernen beziehungsweise die zugehörige Sicherung kontrolliert wiederherstellen, `nginx -t` ausführen und nginx neu laden. Danach nur `jackieleven-go-preview.service` stoppen und deaktivieren. PHP und die Hauptseite bleiben verfügbar. Release- und Backupverzeichnisse für einen erneuten Start erhalten.
