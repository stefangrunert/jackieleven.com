# Go auf diesem MacBook

Seit dem 26. Oktober 2026 führt `https://jackieleven.localhost/de/` zur Go-Anwendung
im Hauptverzeichnis `/Users/stefan/www/jackieleven`.

Der Weg ist Browser → MAMP Apache mit dem vorhandenen lokalen Zertifikat →
`127.0.0.1:8080` → Go. MAMP muss für die HTTPS-Adresse laufen. Der Go-Prozess ist
unabhängig von einem Terminal und startet als LaunchAgent bei Stefans Anmeldung.
Er wird nach einem Prozessende automatisch neu gestartet. Nach Abmelden ist dieser
Benutzerdienst nicht verfügbar; im Ruhezustand des MacBooks wird nichts bedient.

## Im Alltag

```sh
cd /Users/stefan/www/jackieleven

# Go-Code geändert: bauen und Dienst neu starten
ops/go-local.sh restart

# Nur Templates, Kataloge oder Kolumnen geändert: ohne Build neu laden
ops/go-local.sh reload

# Diagnose
ops/go-local.sh status
ops/go-local.sh logs
curl -I https://jackieleven.localhost/de/

# Für diese Anmeldung stoppen; danach wieder starten
ops/go-local.sh stop
ops/go-local.sh start
```

`restart` baut zuerst eine neue Binärdatei und ersetzt sie erst nach erfolgreichem
Build. Ein Compilerfehler lässt den bisherigen Dienst weiterlaufen. `build` baut
nur und verändert den laufenden Prozess nicht. Es gibt keinen automatischen
Dateiwächter. Für Experimente kann zusätzlich `go run` auf Port 8081 laufen; 8080
gehört dem Anmeldedienst. Siehe auch `.dev/go-tutorial.html`.

`stop` entlädt den Dienst für die aktuelle Anmeldung. Beim nächsten Anmelden lädt
macOS die weiterhin installierte plist wieder. Für dauerhaftes Abschalten:

```sh
ops/go-local.sh stop
launchctl disable "gui/$(id -u)/com.stefan.jackieleven.go"
```

`ops/go-local.sh start` aktiviert und lädt ihn wieder.

## Einrichtung und Dateien

`ops/go-local.sh install` baut das Programm, schreibt die LaunchAgent-plist mit
den tatsächlichen lokalen Pfaden und lädt sie. Der Befehl ist für macOS gedacht
und erfordert Go sowie Python 3. Ein fremder Prozess auf Port 8080 muss vorher
gezielt beendet oder umkonfiguriert werden.

- Dienst: `com.stefan.jackieleven.go`
- plist: `~/Library/LaunchAgents/com.stefan.jackieleven.go.plist`
- Binärdatei: `.dev/bin/jackieleven-local`
- Logs: `.dev/logs/go-local.err.log` und `.dev/logs/go-local.out.log`
- Formularzustand: `.dev/runtime/local-contact`
- MAMP-Include: `ops/apache-go-local.conf`

Die LaunchAgent-Konfiguration setzt alle drei Versand-/Turnstile-Anbieterwerte
explizit leer. Die lokale Kontaktseite ist prüfbar, echter Mailversand ist nicht
aktiviert. HTTPS-Cookies erhalten durch kontrollierte Proxyheader dennoch die
korrekten Secure-, HttpOnly- und SameSite-Attribute. Der Backendport bindet nur an
Loopback; Apache begrenzt diesen Host zusätzlich auf lokale Zugriffe.

In MAMP PRO, Host **jackieleven**, Register **Apache**, Feld
**Additional parameters for <VirtualHost> directive**, ist gespeichert:

```apache
Include "/Users/stefan/www/jackieleven/ops/apache-go-local.conf"
```

Diese Einstellung überlebt MAMP-Konfigurationsgenerierung. Die erzeugte
`httpd-ssl.conf` wird nicht von Hand gepflegt. Änderungen an der Include-Datei
verlangen einen Apache-Neustart (Seitenleiste Apache → Kontextmenü → Restart
server). Der Betrieb anderer Hosts und deren Konfiguration bleiben erhalten.
Die normalen MAMP-HTTP-Ports wurden nicht verändert; der portlose Zugang ist die
oben genannte HTTPS-Adresse, nicht ein neu eingerichteter HTTP-Port 80.

## Prüfung und Rücknahme

Geprüft wurden DE/EN, Diskografie, CSS, Kontakt-GET und Secure-Cookie sowie 404 für
`.env`, `.dev`, alte private PHP-Konfiguration und JSON-Daten. Das Zertifikat wurde
normal validiert, ohne `curl -k`. Der automatische Wiederanlauf nach SIGTERM und
der Build-/Neustartbefehl wurden ausgeführt. Die gespeicherte MAMP-Einstellung
wurde nach der Konfigurationsgenerierung geprüft; ein vollständiger macOS-Neustart
war dafür nicht nötig und wurde nicht durchgeführt.

Die vorherigen MAMP-Einstellungen und SSL-Konfigurationen liegen lokal unter
`.dev/local-service-backup-2026-10-26/` mit Prüfsummen. Zur gezielten Rücknahme nur
obige Include-Zeile im Jackie-Leven-Host entfernen, speichern und Apache neu
starten; danach den Go-Dienst stoppen/deaktivieren. Das stellt die frühere
DocumentRoot-Zuordnung wieder her, aber keine entfernten PHP-Quelldateien.
Die PHP-Quellen bleiben im Git-Tag `php-before-go-migration`, der produktive
PHP-Rückfall bleibt auf Hetzner. Diese lokale Einrichtung ändert keinen Server.

Hintergrund: [Apple: LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html),
[Apache: Reverse Proxy](https://httpd.apache.org/docs/2.4/mod/mod_proxy.html),
[MAMP: Konfigurationen werden neu erzeugt](https://documentation.mamp.info/en/MAMP-PRO-Mac/FAQ/General/Changes-to-the-configuration-files-are-gone-when-I-restart-the-servers/).
