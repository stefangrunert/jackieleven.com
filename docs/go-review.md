# Unabhängiger Review der Go-Migration

Stand: 25. Oktober 2026. PHP-Referenz: Commit `869442365d26a697f4f630b03ac073d4899055d6`, Sicherungstag `php-before-go-migration`. Geprüft wurde der lokale Go-Worktree nach den unten beschriebenen Korrekturen. Der unabhängige Reviewer hat keine Runtime- oder Betriebsdateien implementiert. Nach Abschluss des ersten Reviews wurden lediglich eigene Regressionstests und dieser Bericht ergänzt.

## Ergebnis und Umfang

Die unabhängig reproduzierten Sicherheits- und Korrektheitsbefunde sind behoben und erneut geprüft. In den untersuchten Bereichen bleiben keine bekannten offenen P1-/P2-Befunde. Das ist eine Aussage über diesen Reviewumfang, kein formaler Beweis universeller Parität aller denkbaren HTTP-Eingaben.

Der Review umfasst die HTTP-Routen und Pfadgrenzen, sprachabhängiges Rendering und Escaping, Markdown-/Kolumnenleser, Kontaktformular, persistente Zustände und Nebenläufigkeit, Proxyvertrauen, SEO-Ursprung sowie Releasepaketierung und Betriebsvorlagen. Der vollständige Seitenvergleich und die Browserprüfung sind gesonderte Nachweise des Migrationsablaufs.

## Gefundene und behobene Fehler

| Befund | Auswirkung | Korrektur und Nachweis |
|---|---|---|
| P1: `main` wartete nicht auf den Abschluss von `Shutdown`. | SIGTERM konnte laufende Anfragen abbrechen, obwohl ein Zeitfenster zum Beenden vorgesehen war. | `shutdownDone` wird abgewartet. Unabhängig mit einem echten lokalen Prozess geprüft: unvollständiger Kontakt-POST, SIGTERM, Prozess bleibt aktiv, Restbody gesendet, vollständige 400-Antwort, anschließend Exit 0. |
| P2: `net/mail` entsprach nicht PHP `FILTER_VALIDATE_EMAIL`. | Manche vorher gültigen Adressen wurden abgewiesen, andere vorher ungültige akzeptiert. | Explizite Regeln für ASCII, lokale Adressteile, DNS-Namen und IP-Literale. Der unabhängig aus PHP gewonnene Korpus umfasst 612 Kombinationen und stimmt vollständig überein. Er bleibt als `internal/site/testdata/email-validation.json` erhalten. |
| P2: Nichtleere Honeypot-Arrays wurden verworfen. | `website[]=bot` wurde weiterverarbeitet, statt wie in PHP frühzeitig 429 zurückzugeben. | Eigene Prüfung erhält PHP-Leerheits- und Überschreibungsregeln. Ursprünglicher Fehler und korrigierte 429-Antwort unabhängig reproduziert. |
| Querywerte wurden zunächst mit `url.Values.Get` gelesen. | Bei doppelten Parametern wurde der erste statt des letzten Werts verwendet; Arrayüberschreibungen unterschieden sich. | Zentrale skalare PHP-Queryauswertung; Regressionen für letzte skalare Werte und Arrayüberschreibungen. |
| Weitere Kontaktabweichungen bei Trim, Bodygrenze, JSON-Antworten und Formencoding. | Unterschiedliche Eingabebehandlung beziehungsweise Annahme einer nur teilweise gültigen Upstreamantwort. | PHP-Trim-Zeichenmenge, 128 KiB-Grenze, vollständig validierte begrenzte JSON-Antwort, medientypabhängige Formularauswertung einschließlich Multipart und PHP-kompatible Behandlung von Name `"0"`. |

## Unabhängige Nachweise

- Zwei gleichzeitige Kontakt-POSTs mit derselben Sitzung und demselben Token führen genau zu einem Versandaufruf. Ein anschließender Wiederholungsversuch nach unsicherem Versand verwendet auch mit neuem Kontaktobjekt denselben persistenten Idempotenzschlüssel.
- 20 parallele Zugriffe auf denselben IP-Limiter lassen genau fünf Versuche zu. Weitergeleitete Client-IP und HTTPS-Angaben werden nur mit aktivierter Proxyoption und einem lokalen TCP-Peer berücksichtigt.
- 24 gleichzeitige deutsche und englische Seitenantworten blieben sprachlich getrennt. Die überprüften Ausführungspfade liefen unter dem Go-Race-Detector ohne Befund.
- Vertrauliche beziehungsweise interne Pfade aus `.git`, `.dev`, `app`, `data`, `templates`, `research` und `autobiografie` werden nicht direkt ausgeliefert. Asset-Traversal und Asset-Verzeichnislisting sind gesperrt.
- Angreiferähnliche Eingaben in Name und Nachricht bleiben auf der Kontaktfehlerseite erhalten, werden aber als Text escaped. Die Regression prüft ausdrücklich die Anwesenheit der escaped Werte; bloß fehlende Formularfelder würden den Test nicht bestehen.
- Persistenter Kontaktzustand enthält weder Name, E-Mail-Adresse, Nachricht, Turnstile-Token, unverschlüsselte Client-IP noch Zugangsschlüssel. Zustandsdateien haben 0600, vom Kontaktmodul angelegte Sitzungsverzeichnisse 0700. Die Rechte des vom Betreiber vorgegebenen Stammverzeichnisses sind Betreiberkonfiguration; die systemd-Vorlage setzt es auf 0700.
- Der direkte PHP-Differentialtest der Leseregeln bestand: 73 Kolumnenmodelle und deren HTML, Kapitelteile in beiden Sprachen sowie 202 Markdown-/Inlinefälle. Die bewusst begrenzten Leseregeln wurden beibehalten.
- Die Releaseauswahl enthält exakt dieselben 186 Asset-/Markdown-Dateien wie das erzeugte PHP-Referenzrelease. Paketgrenzentests für Traversal, Symlinks und existierende Zielverzeichnisse bestanden.
- Die Betriebsvorlagen überschreiben die relevanten Forwarding-Header, binden den Backendport an Loopback, erhalten Origin-Gate und Limits und verwenden den einmalig aufgelösten Releasepfad. Der Rückfall auf das erhaltene PHP-Release ist dokumentiert.

Die eigenständigen, nicht bereits durch andere Tests abgedeckten Szenarien bleiben in `internal/site/independent_review_test.go`: zusätzliche private Ressourcen, reflektierte Kontakt-XSS-Eingaben und Datenschutz-/Dateirechteprüfung des persistenten Kontaktzustands. Bestehende Parallelitäts-, Idempotenz-, Proxy- und Sprachtests wurden nicht dupliziert.

Reproduzierbare Standardprüfungen:

```sh
go test -race ./...
go vet ./...
PYTHONDONTWRITEBYTECODE=1 python3 ops/test_go_release.py
```

Der zusätzliche direkte PHP-Leservergleich verwendet den erzeugten Fixturepfad über `JACKIE_PHP_READERS_FIXTURE` und den Inhaltsbaum über `JACKIE_CONTENT_ROOT`; der oben genannte Emailkorpus gehört dauerhaft zur normalen Testsuite.

## Grenzen vor Produktionsfreigabe

Turnstile und Resend wurden mit kontrollierten Transporten beziehungsweise injizierten Antworten geprüft. Es wurde keine echte Nachricht versandt und kein Livekontakt getestet. Die reale Dienstkonfiguration und erfolgreiche Zustellung sind dadurch nicht nachgewiesen.

Die lokale Prüfung ersetzt kein `nginx -t`, `systemd-analyze verify` und keine Start-/Rückfallprobe auf dem tatsächlichen Linuxserver. Rechte, reale Proxykette, Netzwerkerreichbarkeit und Restartverhalten müssen dort vor Freigabe bestätigt werden. Der Go-Betrieb ist vorbereitet, aber dieser Review hat keinen Live-Deploy vorgenommen.

Eine abschließende Freigabe muss den vollständigen HTTP-/Inhaltsvergleich, die Browserprüfung und das tatsächlich gebaute Releasepaket berücksichtigen. Von diesem unabhängigen Review wird keine ungeprüfte pauschale 100%-Parität behauptet.
