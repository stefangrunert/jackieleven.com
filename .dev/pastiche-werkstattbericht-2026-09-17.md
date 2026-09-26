# Wie Jackie Leven eine Autobiografie bekam, die er nie geschrieben hat

Werkstattbericht über die Zusammenarbeit von Stefan und Claude Code am Projekt jackieleven. Aufgezeichnet am 17. September 2026, am Abend desselben Tages, an dem die Arbeit begonnen hat. Der Bericht beschreibt die Rekonstruktion von Levens eigenen Websites aus dem Internet Archive, die Entstehung einer erfundenen Autobiografie in seiner Stimme und vor allem das, was danach kam: das Entfernen von KI-Sprache aus einem Text, der inhaltlich bereits stimmte.

## Ein Projekt, das am Herzen liegt

Stefan begann mit einem Satz, der den Maßstab für alles Weitere setzte:

> „wir haben hier en neues projekt, eines das mir besonders am herzen lieg."

Es sollte eine Hommage-Seite für den schottischen Songwriter Jackie Leven werden (1950–2011). Ein biografisches Kompendium lag bereits vor: acht Dateien, aus Leitmedien, Musikpresse, Nachrufen und Diskografien zusammengetragen, mit Fußnoten und dokumentierten Widersprüchen. Damit ließ sich eine Seite bauen. Aber es war Material *über* ihn.

## Die Detektivaufgabe

> „erst weiter recherchieren. du bekommst eine detektivaufgabe. ich erinnere mich gut, dass jackie eine eigene homepage hatte, die dann nach 2011 offline ging. dort hatte er einen blog, konzertkalender und anderes. jackieleven uk oder com oder so. finde das heraus im web archiv"

Eine Erinnerung, zwei mögliche Domains, kein Link. Die Suche über die CDX-Schnittstelle des Internet Archive ergab mehr, als die Erinnerung versprochen hatte: nicht eine Seite, sondern drei, hintereinander über dreißig Jahre.

**jackieleven.com** entstand 1996 als Fanseite, betrieben von einem Italiener, technisch untergebracht unter der wenig glamourösen Adresse `home.xnet.it/tout/HTML/`. Ab Oktober 2002 schrieb Leven dort eine Monatskolumne, „The Deep Pool". **jackieleven.co.uk** war ab 2008 die offizielle Seite mit Blog und mehreren Rubriken; sie lief bis 2025 weiter und wurde 2024 vom Hoster gesperrt. **jackie-leven.com** ist die Gedenkseite nach seinem Tod.

Damit war die eigentliche Entdeckung gemacht, und sie war größer als die Aufgabe: Leven hatte neun Jahre lang regelmäßig geschrieben. Nicht Interviews, nicht Pressetexte — eigene Prosa, monatlich, für ein Publikum von vielleicht ein paar hundert Menschen.

## Die Ernte

> „wichtig: alle inhalte aus jackies kolumnen in research/colums sammeln. ein file pro post"

> „auch die bilder, falls vorhanden"

Am Ende standen **76 Dateien mit rund 90.000 Wörtern** in `research/columns/`, dazu 19 Bilder. Der Text ist wortgetreu übernommen, samt Levens Eigenheiten: durchgehend kleines „i", Tippfehler, eigenwillige Zeichensetzung. Jede Datei trägt einen YAML-Kopf mit Rubrik, Datum, Quell-URL, Archivlink und Capture-Datum.

Der Weg dorthin bestand zu großen Teilen aus dem Beheben eigener Fehler, und die sind aufschlussreicher als das Ergebnis:

- **Führende Leerzeichen** hebelten die Regeln zum Entfernen von Navigation und Kopfzeilen aus. Jede Zeile musste vorher beschnitten werden.
- **Die Trennlinien in den Kolumnen** bestanden aus denselben Zeichen wie die Trennlinien zwischen Kolumnen. Ein Text wurde dadurch in vier Stücke zerlegt. Erst eine engere Regel (`(\+-){4,}`) trennte richtig.
- **Eine Ähnlichkeitsprüfung mit Schwelle 0,9** verschmolz den Nachruf vom November 2011 mit einer Seite vom August 2011, weil beide dieselbe Navigation trugen. Die unscharfe Zusammenführung flog raus; nur exakte Dubletten werden noch zusammengefasst.
- **Umlaute in Dateinamen** erzeugten Slugs wie `m-rz` für „März". Eine Transkriptionstabelle hat das geheilt.

Keiner dieser Fehler war spektakulär. Zusammen hätten sie den Korpus unbrauchbar gemacht, ohne dass es aufgefallen wäre — ein Textkonvolut sieht auch dann vollständig aus, wenn ein Viertel fehlt.

Eine Einschränkung technischer Art gehört hierher: **Unteragenten konnten in dieser Umgebung keine Dateien schreiben.** Die Analysen liefen parallel und korrekt, aber ihre Berichte landeten nirgends. Sie mussten aus den Transkripten der Agentenläufe extrahiert werden. Bei den folgenden Aufträgen bekamen die Agenten die Anweisung, den vollständigen Bericht direkt zurückzugeben.

## Erst die Fakten ordnen

> „erst mal die fakten ordnen, denn die sind voraussetzung für das buch."

Aus den Kolumnen und den rekonstruierten Seiten entstanden vier weitere Rechercheakten:

| Datei | Inhalt |
|---|---|
| `09-websites.md` | Geschichte der drei Domains, Betreiber, Technik, Inventar des Presse- und Interviewarchivs, die Lücken |
| `10-konzertkalender.md` | 470 Auftritte 1997–2011, zusammengeführt aus 26 Kalenderfassungen beider Seiten |
| `11-zeitleiste.md` | Durchgehende Chronologie mit einer eigenen Tabelle aller Datierungskonflikte |
| `12-biografie-aus-den-kolumnen.md` | Faktensammlung aus Levens eigenen Texten, thematisch, jeder Fakt mit Belegstelle |

Der Punkt an dieser Reihenfolge war, dass die Fakten *vor* der Prosa fertig sein mussten. Wer erst schreibt und dann belegt, belegt, was er geschrieben hat.

Die Zeitleiste enthält deshalb eine Tabelle, die eher ein Eingeständnis ist: Geburtsdatum (18. oder 19. Juni), Bandgründung (1975 nach Leven, 1977 nach allen anderen), der Überfall (1983 oder 1984), die Krebsart (drei Angaben, keine Primärquelle). Bei einem Mann, der seine eigene Biografie gern ausschmückte, ist die Widerspruchstabelle kein Mangel der Recherche, sondern ihr Ergebnis.

## Die haarsträubende Idee

> „mir kommt eine haarsträubende idee: wie wäre es jackie eine autobiographie schreiben zu lassen. wir wissen ja nun in welchem stil er schreibt, wie er sich ausdrückt, wo sein feiner humor, sarkasmus, ironie sitzten"

Drei Entscheidungen fielen sofort: freie Pastiche in seiner Stimme statt Montage aus Zitaten; Englisch mit späterer deutscher Fassung; das ganze Leben in zwölf bis fünfzehn Kapiteln.

## Der Rahmen, der vor dem ersten Satz stand

Die Idee ist heikel, und sie wurde als Erstes eingehegt. `autobiografie/00-rahmen.md` legt fest:

- Der Text ist **nicht von Jackie Leven**. Jedes Kapitel trägt diesen Hinweis.
- Er wird **nirgends als Levens Wort veröffentlicht**, weder auf der Hommage-Seite noch anderswo.
- **Jedes Kapitel endet mit einem Abschnitt „Belegt / erfunden"**, der beides einzeln aufführt.

Die Begründung steht im Rahmen selbst und ist der eigentliche Grund, weshalb das Projekt vertretbar ist: Leven war ein notorischer Ausschmücker — Bob Dylan als angeblicher Ko-Autor, eine Profikillerin als Song-Inspiration, ein eigener Whisky, den sein Labelchef später „a complete scam" nannte. **Seine echten Erinnerungen klingen bereits wie Erfindungen.** Wenn ungekennzeichnete erfundene Ich-Prosa danebensteht, kann später niemand mehr trennen, was von ihm stammt und was von uns. Bei einem anderen Autor wäre die Kennzeichnung Höflichkeit. Bei diesem ist sie die Bedingung.

In der Praxis hat sich der Belegt/erfunden-Abschnitt als das nützlichste Instrument des ganzen Projekts erwiesen, und zwar aus einem unerwarteten Grund: Er zwingt dazu, nach dem Schreiben jeden Satz einer Quelle zuzuordnen. Dabei fiel in Kapitel 5 ein Fehler auf, der sonst stehen geblieben wäre. Ich hatte Tony Stratton Smith zum Zeitpunkt des Solovertrags für tot gehalten; er starb 1987, also nach dem Überfall. Die Szene und die Belegnotiz wurden korrigiert.

## Die Stimme messen, bevor man sie nachmacht

Der Korpus zerfällt stilistisch in zwei Phasen, und der Unterschied ist so deutlich, dass er sich zählen lässt:

| | Kolumnen 2002–2007 (43.600 W.) | Blog 2008–2012 (46.900 W.) |
|---|---|---|
| Erste Person | 578× kleines „i", 257× „I" | 22× kleines „i", 829× „I" |
| Gedankenstrich ` - ` | 22,8 je 1000 Wörter | 1,2 |
| Auslassungspunkte | 4,8 | 2,3 |
| Halbe Anführungszeichen | 14,9 | 0,3 |
| Satzlänge (Median / längster) | 29 / 323 Wörter | 26 / 157 Wörter |

Gewählt wurde die frühe Kolumnenstimme. Die Kapitel 14 und 15 wechseln bewusst in die späte Blogstimme mit großem „I", weil sie in den Jahren spielen, in denen er so schrieb; das steht in ihrem Frontmatter.

Daraus entstanden zehn Stilregeln und vier Fallen. Die wichtigste Regel lautet: **Keine Pointe am Kapitelende, sondern ein ruhiges Bild.** Sie wurde in der ersten Fassung fünfzehnmal gebrochen.

## Fünfzehn Kapitel

Die erste Fassung entstand in einem Zug. Sie war inhaltlich dicht, sie hielt die Fakten sauber getrennt, und Stefan las sie mit Interesse:

> „ja, weiter mit kapitel 7 bis 15 - ich bin gespannt sie zu lesen"

## Der Einspruch

Dann kam der Satz, um den herum sich die zweite Hälfte des Projekts organisiert hat:

> „es gibt zahlreiche forumulierungen in den texten, die ganz klar ki sind - und nicht jackie. […] das zieht die ansonsten inhaltlichen guten texte in richtung ki slop. das muss unbeding verhindert werden. du musst abschitt für abschnitt dahingehend analysieren und den text flüssiger \"leven like\" machen. wir haben sprache ja schon - wenn auch für einen andern stil - gemeinsam im christ projekt getrimmt. du sollst das nicht 1:1 nachahmen, aber verstehen warum dort die sprache die geworden ist, die ich will"

Fünf Belegstellen lagen bei:

> „Both facts are true. Only one of them is a room."
> „Now the money, because nobody does the money."
> „When he died i did the thing that men of my type do, which is that i went out and worked. Not a little."
> „Kevin Coyne i never got to work with, and that is one of my real regrets."
> „I never got the big audience. I got the right one."

Der entscheidende Umstand war, dass der Maßstab bereits im Haus lag. Für die Frage „klingt das nach Leven?" gab es 90.000 Wörter von Leven. Daraus entstand `werkzeug/messen.py`, und die erste Messung war unbequem:

| | Leven | erste Fassung |
|---|---|---|
| Satzlänge, Mittel | 35,1 Wörter | 21,5 |
| Streuung der Satzlänge | 30,0 | 17,9 |
| längster Satz | 362 Wörter | 99 |
| Sätze unter 5 Wörtern | 2,1 % | 12,6 % |
| Gedankenstriche je 1000 W. | 20,1 | 8,5 |
| Auslassungspunkte je 1000 W. | 3,6 | 0,0 |
| bewertender Schluss | 0,16 | 1,67 |
| Antithese | 0,22 | 0,67 |
| Ankündigung | 0,16 | 0,47 |

Nicht Passiv oder Nominalstil waren das Problem — die gab es gar nicht. Das Problem war der **Takt**. Levens Sätze mäandern durch Kommas und Gedankenstriche und kommen oft nirgends an. Die erste Fassung zerlegte dasselbe Material in gebaute Einheiten mit Landung: zehnmal so viele bewertende Schlüsse wie er, sechsmal so viele Sätze unter fünf Wörtern, und kein einziges Auslassungszeichen, wo er im Schnitt alle dreihundert Wörter eines setzt.

Genau das ist, was „KI-Slop" auf Satzebene bedeutet. Es fehlt nichts, es ist nichts falsch. Jeder Absatz landet nur zu sauber.

## Der Fehlversuch: die Messung als Dogma

Die Korrektur ging sofort schief. Ich nahm den Mittelwert als Zielgröße und zog die Satzlänge hoch — auf über 50 Wörter. Stefan stoppte das im nächsten Zug:

> „stop - das darf nicht zum manierismus werden. jetz wird der text grausam unleserlich. du musst eine balance finden, kein dogma anwenden. jackies texte sind nicht immer leicht zu lesen. darauf müssen wir rücksicht nehmen. vorallem wei es eine lange autobiografie ist, die auch gelesen werden soll. finde den sweet spot"

Das ist der wichtigste Eingriff des ganzen Tages, und der Fehler dahinter ist lehrreich genug, um ihn ausdrücklich festzuhalten: **Der Mittelwert war die falsche Kennzahl.** Levens Zahl ist die Streuung — 30 bei einem Mittel von 35. Er schreibt Sätze von zwölf Wörtern und Sätze von hundertzwanzig, unmittelbar nacheinander. Die 362-Wörter-Sätze sind Ausreißer aus einzelnen Kolumnen, keine Schreibweise. Sein eigener Blogeintrag über die Markthallenuhr läuft bei 24, 30 und 15 Wörtern und liest sich mühelos.

Dazu kommt ein Gattungsunterschied, den keine Messung erfasst: Eine Autobiografie von fünfzehn Kapiteln wird anders gelesen als eine Monatskolumne von zweitausend Wörtern. Was dort als Eigenart trägt, ermüdet über hundert Seiten.

Die neue Zielmarke: **Mittel zwischen 24 und 32 Wörtern, Streuung über 20, pro Kapitel höchstens ein bis zwei Sätze über achtzig Wörter.** Der Fehlversuch steht mitsamt Stefans Zitat in `00-sprache.md`, damit er nicht wiederholt wird.

## Der zweite Einspruch: der platte Anfang

> „platter start, jackie hätte das niemals geschrieben: i was born in Kirkcaldy in the June of 1950, in the town that made linoleum for most of the world and produced one Prime Minister."

Statt zu raten, wie er stattdessen angefangen hätte, wurden seine eigenen dreißig Kolumnenanfänge ausgelesen. Das Ergebnis war eindeutig: **Leven beginnt mit Wetter, Ort, Jahreszeit oder Körper. Nie mit Biografie.** Von seinen 979 Absätzen beginnt kein einziger mit einer Datumsangabe der Form „In 1971…“, „On 14 November…“, „By 1983…“.

Das neue erste Kapitel beginnt jetzt so:

> „May, and the hawthorn out all along the path by the railway line between Leslie and Markinch - ne'er cast a clout till May is out…"

Linoleum und Premierminister stehen weiterhin drin, zwei Absätze später, beiläufig.

## Der dritte Einspruch: Sätze, die vorstellen statt erzählen

> „viel besser. sachen, die ich nicht erklären kann warum sie nicht echt klingen. kannst du?"

Sieben Belegstellen, alle ähnlich gebaut. Die Messung fand die Regel dahinter:

| | Leven | Pastiche |
|---|---|---|
| Absätze, die mit „There was/is…" beginnen | 0,8 % | 5,4 % |
| Absätze, die mit „X ist/war ein Y" beginnen | 1,3 % | 7,7 % |

Das ist der **Registerauszug**: Eine Sache wird dem Leser vorgestellt, bevor sie etwas tut. Leven führt Dinge nie ein. Sie kommen in Bewegung herein — über eine Assoziation, eine Erinnerung oder weil er gerade daran vorbeigeht. Aus „There is a ferry to Kerrera" wurde deshalb „You go down to the slip for the Kerrera ferry and there is a board propped up there…". Die Fähre existiert im zweiten Satz genauso; der Unterschied ist, dass jemand zu ihr hinuntergeht.

## Satz für Satz, durch alle fünfzehn Kapitel

> „nicht auf diese spezifischen stellen begrenzen, die waren beispiele. du musst das generell berücksichtigen, also satz für satz sinn und unsinn analysierern. und dann auch auf noch nicht umgeschriebene kapitel anwenden. aber wiederum: nicht in dogmatismus verfallen"

Dafür entstand das zweite Werkzeug, `werkzeug/pruefen.py`. Es meldet zehn Satzformen, die bei Leven selten oder gar nicht vorkommen — Existenz-Eröffnung, Kopula-Definition, Datum am Absatzanfang, Rückverweis-Cleft, bewertender Anschluss, Antithese, Selbstcharakterisierung, Ankündigung, nummerierte Weisheit, Merksatz-Verdacht — dazu kurze Absatzschlüsse als Pointenverdacht.

Der erste Lauf über alle fünfzehn Kapitel ergab über hundert Kandidaten. Was davon entfernt wurde:

| Figur | vorher | nachher |
|---|---|---|
| nummerierte Weisheit | „**One.** … **Two.** … **Three.** … **Four.**" (Kap. 15) | dieselben vier Gedanken als Absätze, ohne Zählung |
| Registerauszug | „Mikki Rain is the chieftain. John Ralph is the tribal seer." | „Mikki Rain has been its chieftain since Dorset … John Ralph carries the relics about and does the seeing" |
| Stakkato-Pointe | „Alone. Sitting. Watching somebody else's departure." | „On my own, on the sand, watching other people leave, and pleased about it in a way i could not have defended to a committee." |
| Satz über den eigenen Satz | „That is a shameful sentence and it is accurate." | „…and i have never yet found a way of putting that down which does not shame me while i am putting it down." |
| Ankündigung | „Now the money, because nobody does the money." | „Nobody ever does the money, so." — und sofort die Zahl |
| Antithese | „It was not a crisis, it was a solution." | „…so plainly then - it worked. It took the trouble away every time, for about four hours." |

Nebenbei fiel ein Perspektivfehler auf, den kein Stilwerkzeug meldet: In Kapitel 10 stand „the reason i stayed with him until the end of my life". Das kann ein Erzähler nicht schreiben, der noch lebt.

## Was das Werkzeug nicht kann

Hier liegt der methodische Kern des ganzen Tages, und er ist aus dem Christ-Projekt übernommen: **Die mechanische Prüfung meldet, sie entscheidet nicht.** Der Docstring von `pruefen.py` sagt das an sich selbst gerichtet:

> „Das Werkzeug entscheidet nichts. Jeder Treffer ist ein Kandidat, der im Zusammenhang gelesen werden muss: ‚They danced.' ist ein Satz über tanzende Männer, ‚Only one of them is a room.' ist eine Pointe. Der Zähler sieht den Unterschied nicht."

Von den 31 am Ende verbliebenen Treffern wurde jeder einzeln geprüft und keiner geändert, weil sie alle in eine von vier Gruppen fallen:

- **Levens eigene Wörter:** „Shame." · „Not everyone can do this." · „Smartie is a retired racehorse." · „DOLL BY DOLL HAVE MOVED."
- **Wörtliche Rede Dritter:** Blys „That is what the death of a father does to a man's soul. Look at it." · Hillmans „Let the snake be a snake."
- **Nackte Tatsachen:** „He stayed five weeks." · „He was my little brother." · „i was in the room."
- **Witze in seinem Register:** „i simply have an excellent memory and a website."

Eine Zeile im Skript hätte jede dieser Stellen glattgezogen. Das Ergebnis wäre ein Text ohne Auffälligkeiten und ohne Verfasser gewesen — also genau der Slop, gegen den die Übung gerichtet war. Die Messung verhindert KI-Sprache nur, solange ein Urteil dazwischensteht.

## Was aus dem Christ-Projekt kam

Stefan hat ausdrücklich auf `~/www/christ` verwiesen, mit der Einschränkung, das nicht nachzuahmen, sondern zu verstehen, weshalb die Sprache dort geworden ist, was sie ist. Übernommen wurden drei Dinge, keines davon eine Formulierung:

1. **Die Trennung von mechanischer Prüfung und Urteil.** Dort „report, don't decide", hier derselbe Satz im Docstring.
2. **Der Katalog der KI-Figuren.** Elf Figuren aus einem deutschen, schriftlichen Stil, übertragen auf eine englische, mündliche Stimme — mit ausdrücklicher Streichung derer, die hier nicht gelten. Der Gedankenstrich-Einschub ist bei Leven kein Fehler, sondern sein Hauptgelenk. Das Stakkato existiert bei ihm als seltene Ausnahme, nicht als Verbot.
3. **Der dokumentierte Fehlversuch.** Im Christ-Projekt stehen die missratenen Fassungen mit Begründung neben den gelungenen. Deshalb steht hier die 50-Wörter-Katastrophe mitsamt Stefans Stopp-Zitat im Sprachdokument und nicht nur in einem verlorenen Gesprächsverlauf.

Was *nicht* übernommen wurde, ist der Ton. Der Christ-Text ist deutsch, schriftlich, ruhig. Leven ist englisch, mündlich, schnell, grob und plötzlich zärtlich.

## Der Stand nach diesem Durchgang

Alle fünfzehn Kapitel sind geschrieben, geprüft und überarbeitet. Die Messung am Ende:

| | Leven | 1. Fassung | 2. Fassung |
|---|---|---|---|
| Ankündigung je 1000 W. | 0,16 | 0,47 | **0,07** |
| Antithese je 1000 W. | 0,22 | 0,67 | **0,14** |
| Absatzschluss unter 8 Wörtern | 6,3 % | 7,2 % | **4,4 %** |
| Sätze unter 5 Wörtern | 2,1 % | 9,4 % | **8,1 %** |
| Satzlänge Ø / Streuung | 35,1 / 30,0 | 22,5 / 17,1 | **23,7 / 17,3** |

Zwei Werte weichen weiterhin ab, und beide bleiben bewusst stehen. Die **kurzen Sätze** sind nachgesehen fast alle Szenenüberschriften („Then Reading.", „And then Austria.", „Little Venice."), Zitate oder Tatsachen; ein Buch braucht Schnitte, die eine Monatskolumne nicht braucht. Die **Streuung** bleibt bei 17 statt 30, weil Levens Extremwert aus einzelnen dreihundertwortigen Kolumnensätzen stammt — auf hundert Seiten wäre genau das der Manierismus, vor dem Stefan gewarnt hat.

Offen bleibt eine Schwäche, die benannt und nicht behoben ist: **Die Kapitel 11, 13 und 14 liegen mit einer Streuung von 14 bis 15 am flachsten.** Dort fehlt je ein langer, anrollender Satz. Das steht in `00-sprache.md` als nächster Schritt.

Und es ist festzuhalten, was dieser Tag *nicht* erbracht hat. Der Text ist von einem einzigen Leser beurteilt worden, und der ist am Projekt beteiligt. Ob die Kapitel jemanden erreichen, der Leven nicht kennt, ist unbekannt. Ob sie jemanden erreichen, der ihn kennt und liebt, ist die eigentliche Frage und ebenfalls unbeantwortet. Die deutsche Fassung existiert nicht. Ein Durchgang über das ganze Buch auf wiederkehrende Bilder — Kohlenschuppen, Fähre, Kohlenfeld — steht aus; einzelne Kapitel sind geprüft, das Buch als Ganzes nicht.

Die Messwerte belegen ausschließlich, dass bestimmte Satzformen seltener geworden sind. Sie belegen nicht, dass der Text gut ist.

---

## Redaktionelle Unterlagen für die Weiterarbeit

Dieser Abschnitt dient der eigenen Erinnerung und kann bei einer Weitergabe entfernt werden.

- **Erzählperspektive:** Der Bericht verwendet „wir" für die gemeinsamen Entscheidungen und „ich" dort, wo es um meine eigenen Fehler geht. Das ist beabsichtigt: Die Fehlentscheidungen (Mittelwert statt Streuung, die Extraktionsfehler, Stratton Smith) waren meine, nicht unsere.

- **Gesprächszitate:** Alle eingerückten Zitate sind Stefans Formulierungen im Wortlaut, Kleinschreibung und Tippfehler beibehalten. Die übrige Darstellung fasst den Verlauf zusammen.

- **Rollen:** Stefan gab das Ziel vor, stellte die Detektivaufgabe, bestand auf der Reihenfolge Fakten-vor-Prosa, hatte die Idee der Autobiografie, traf die drei Grundentscheidungen (freie Pastiche, Englisch mit deutscher Fassung, ganzes Leben) und erkannte in drei Durchgängen die KI-Sprache, die ich selbst nicht gesehen hatte. Sein Stopp gegen die Übersteuerung war der wichtigste einzelne Eingriff. Claude Code recherchierte, baute die Extraktion, legte den Korpus an, schrieb die fünfzehn Kapitel und die beiden Messwerkzeuge und führte die Überarbeitung durch. Unteragenten wurden für parallele Korpusanalysen eingesetzt; sie konnten in dieser Umgebung keine Dateien schreiben.

- **Was vor einer Veröffentlichung zu klären ist:** Die Rechte an Levens Texten liegen nicht bei uns. Der Korpus in `research/columns/` ist Arbeitsgrundlage, keine Veröffentlichung. Für die Hommage-Seite wären Zitatumfang und Rechteinhaber zu klären; der Songtext, mit dem Levens letzter Blogeintrag endet, steht aus genau diesem Grund nicht in Kapitel 15. Die Pastiche selbst darf nach dem Rahmen ohnehin nicht als sein Wort erscheinen.

- **Namenskollision:** In `research/` existieren zwei Dateien mit der Nummer 09 — `09-websites.md` aus diesem Verlauf und `09-alan-moffatt-genealogie.md` aus einer parallelen Sitzung. Beide sind inhaltlich in Ordnung; die Nummerierung ist noch zu bereinigen.

### Dateien des Projekts

- [research/README.md](../research/README.md) — das biografische Kompendium, zwölf Akten plus Korpus
- [research/columns/README.md](../research/columns/README.md) — die Primärquelle: 76 Texte, ~90.000 Wörter, mit Archivlinks je Beitrag
- [autobiografie/00-rahmen.md](../autobiografie/00-rahmen.md) — was das Buch ist und was nicht; die Kennzeichnungspflicht
- [autobiografie/00-kapitelplan.md](../autobiografie/00-kapitelplan.md) — fünfzehn Kapitel mit Quellen je Kapitel
- [autobiografie/00-sprache.md](../autobiografie/00-sprache.md) — das Sprachgesetz: Messungen, Figurenkatalog, der dokumentierte Fehlversuch, das Protokoll des Satz-für-Satz-Durchgangs
- [werkzeug/messen.py](../werkzeug/messen.py) — misst die Kapitel gegen den Korpus
- [werkzeug/pruefen.py](../werkzeug/pruefen.py) — meldet Kandidaten pro Kapitel, entscheidet nichts

### Aufrufe

```sh
python3 werkzeug/messen.py              # Gesamtvergleich Leven / Pastiche
python3 werkzeug/messen.py autobiografie/07-electric-fur.md
python3 werkzeug/pruefen.py             # alle Kapitel
python3 werkzeug/pruefen.py 07 08       # einzelne, mit führender Null
```

### Verwandte Arbeitsgrundlage

- `~/www/testhost/christ` — Herkunft der Methode: Trennung von mechanischer Prüfung und Urteil, Figurenkatalog der KI-Sprache, dokumentierte Fehlversuche
