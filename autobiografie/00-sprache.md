# Sprache: gemessen an Leven, nicht geschätzt

Am 17. September 2026 hat Stefan an fünf Stellen KI-Sprache in den Kapiteln erkannt:

> „Both facts are true. Only one of them is a room."
> „Now the money, because nobody does the money."
> „When he died i did the thing that men of my type do, which is that i went out and worked. Not a little."
> „Kevin Coyne i never got to work with, and that is one of my real regrets."
> „I never got the big audience. I got the right one."

Sein Urteil: „das zieht die ansonsten inhaltlich guten texte in richtung ki slop."

Er hat recht, und die Messung sagt, wie weit. Der Maßstab liegt im Haus: 76 Texte von Leven selbst, rund 90.000 Wörter, in [research/columns/](../research/columns/README.md).

```sh
python3 werkzeug/messen.py
```

## Was die erste Messung ergab

| | Leven | erste Fassung |
|---|---|---|
| Satzlänge, Mittel | 35,1 Wörter | 21,5 |
| Streuung der Satzlänge | 30,0 | 17,9 |
| längster Satz | 362 Wörter | 99 |
| Sätze unter 5 Wörtern | 2,1 % | 12,6 % |
| Gedankenstriche | 20,1 je 1000 Wörter | 8,5 |
| Auslassungspunkte | 3,6 je 1000 Wörter | 0,0 |
| Kommas je Satz | 1,74 | 1,27 |
| bewertender Schluss („that is", „which is") | 0,16 je 1000 Wörter | 1,67 |
| Antithese | 0,22 je 1000 Wörter | 0,67 |
| Ankündigung | 0,16 je 1000 Wörter | 0,47 |

Nicht Passiv oder Nominalstil sind das Problem, sondern der Takt. Levens Sätze mäandern durch Kommas und Gedankenstriche und kommen oft nirgends an; die erste Fassung zerlegte dasselbe Material in gebaute Einheiten mit Landung.

## Die Figuren, an denen es hängt

Sie stammen aus dem Christ-Projekt und sind hier auf eine englische, mündliche Stimme übertragen. **Nicht alle gelten:** Der Gedankenstrich als Einschub ist bei Leven kein Fehler, sondern sein Hauptgelenk, und das Stakkato existiert bei ihm als Ausnahme. Was zählt, ist dies:

1. **Der Merksatz am Absatzende.** Ein kurzer Aussagesatz, der das Gesagte zusammenfasst und zitierfähig klingt. Levens Absätze enden an einem Bild, an einem Witz, der die Sache entwertet, oder mitten in der Bewegung.
2. **Die Antithese mit Parallelbau.** „I never got the big audience. I got the right one." Zwei Sätze gleicher Form, deren zweiter den ersten aufhebt.
3. **Die Ankündigung.** „Now the money, because nobody does the money." Ein Satz über den eigenen Text statt über die Sache.
4. **Der bewertende Schluss.** „and that is one of my real regrets", „which is the whole of it". Leven bewertet schief, beiläufig oder gar nicht.
5. **Die Selbstcharakterisierung.** „i did the thing that men of my type do". Er beschreibt, was er tat, nicht, zu welchem Typus es gehört.
6. **Die nummerierte Weisheit.** Listen mit „One. Two. Three." — in seinen 90.000 Wörtern kommt das kein einziges Mal vor.
7. **Der Ringschluss.** Das Kapitel kehrt am Ende zum ersten Satz zurück.

## Der Fehlversuch: die Messung als Dogma

Die erste Überarbeitung von Kapitel 2 hob den Mittelwert auf über 50 Wörter und machte den Text unlesbar. Stefan am 17. September 2026: „das darf nicht zum manierismus werden … jackies texte sind nicht immer leicht zu lesen. darauf müssen wir rücksicht nehmen. vorallem weil es eine lange autobiografie ist, die auch gelesen werden soll."

**Der Mittelwert war die falsche Zielgröße.** Levens Kennzahl ist die **Streuung**: 30 bei einem Mittel von 35. Das heißt, er schreibt Sätze von zwölf Wörtern und Sätze von hundertzwanzig, unmittelbar nacheinander. Die 362-Wörter-Sätze sind Ausreißer aus Kolumnen, keine Schreibweise. Sein eigener Blogeintrag über die Markthallenuhr läuft bei 24, 30 und 15 Wörtern und liest sich mühelos.

Dazu kommt, dass eine Autobiografie von fünfzehn Kapiteln anders gelesen wird als eine Monatskolumne von zweitausend Wörtern. Was dort als Eigenart trägt, ermüdet über hundert Seiten.

## Woran die zweite Fassung sich hält

- **Streuung statt Länge.** Zielmarke: Mittel zwischen 24 und 32 Wörtern, Streuung über 20. Pro Kapitel ein, höchstens zwei Sätze über achtzig Wörter — dort, wo der Gedanke wirklich nicht abreißen darf.
- **Kurze Sätze sind erlaubt**, solange sie nichts zusammenfassen. „She ironed to Lightnin' Hopkins." ist ein Satz über die Mutter. „Only one of them is a room." ist eine Pointe. Der Unterschied liegt nicht in der Länge.
- **Der Gedankenstrich als Gelenk**, nicht als Pointenvorbereitung: er reiht an, statt gegenüberzustellen.
- **Auslassungspunkte**, wo ein Gedanke ausläuft statt endet.
- **Abschweifung ohne Rückkehr.** Ein Absatz darf bei einem Detail beginnen, über zwei Assoziationen abwandern und nicht zurückfinden.
- **Konkretes statt Deutung.** Der Name des Pubs, die Marke des Biers, der Preis in Pfund und Pence.
- **Selbstironie statt Bilanz.** Wo ein Merksatz stünde, steht bei Leven ein Witz auf eigene Kosten — oder er bricht ab.

## Was bleibt

Der Inhalt. Kein Fakt, kein Name, kein Datum ändert sich beim Umschreiben; die Abschnitte „Belegt / erfunden" bleiben gültig. Geändert wird nur der Takt.

---

## Der Durchgang Satz für Satz (17. September 2026)

Stefan: „nicht auf diese spezifischen stellen begrenzen, die waren beispiele. du musst das generell berücksichtigen, also satz für satz sinn und unsinn analysieren. und dann auch auf noch nicht umgeschriebene kapitel anwenden. aber wiederum: nicht in dogmatismus verfallen."

Dafür entstand `werkzeug/pruefen.py`. Es meldet Satzformen, die bei Leven selten oder gar nicht vorkommen, und **entscheidet nichts**. Jeder Treffer wurde einzeln im Zusammenhang gelesen. Alle fünfzehn Kapitel sind durch.

### Was entfernt wurde

| Figur | Beispiel aus der ersten Fassung | Ersatz |
|---|---|---|
| Existenz-Eröffnung | „There is a ferry to Kerrera." | „You go down to the slip for the Kerrera ferry und there is a board propped up there…" — die Sache kommt in Bewegung herein |
| Registerauszug | „Mikki Rain is the chieftain. John Ralph is the tribal seer." | „Mikki Rain has been its chieftain since Dorset … John Ralph carries the relics about und does the seeing" |
| nummerierte Weisheit | „**One.** … **Two.** … **Three.**" (Kap. 15) | dieselben vier Gedanken als Absätze, ohne Zählung |
| Ankündigung | „Now the money, because nobody does the money." | „Nobody ever does the money, so." + sofort die Zahl |
| Satz über den eigenen Text | „That is a shameful sentence and it is accurate." | „…und i have never yet found a way of putting that down which does not shame me while i am putting it down." |
| Antithese | „It was not a crisis, it was a solution." | „…so plainly then - it worked. It took the trouble away every time, for about four hours." |
| Stakkato-Schluss | „Alone. Sitting. Watching somebody else's departure." | „On my own, on the sand, watching other people leave, and pleased about it in a way i could not have defended to a committee." |

### Was ausdrücklich stehen blieb

„Shame." · „Not everyone can do this." · „DOLL BY DOLL HAVE MOVED." · „Let the snake be a snake." · „i was in the room." · „He stayed five weeks." · „i would stand in a room and hum." · „Smartie is a retired racehorse." · „He was my little brother." · „i simply have an excellent memory and a website."

Das sind Levens eigene Wörter, wörtliche Rede Dritter, nackte Tatsachen oder Witze in seinem Register. Der Zähler sieht den Unterschied nicht; deshalb entscheidet er nicht.

### Stand der Messung nach dem Durchgang

| | Leven | 1. Fassung | 2. Fassung |
|---|---|---|---|
| Ankündigung je 1000 W | 0,16 | 0,47 | **0,07** |
| Antithese je 1000 W | 0,22 | 0,67 | **0,14** |
| Absatzschluss < 8 Wörter | 6,3 % | 7,2 % | **4,4 %** |
| Sätze < 5 Wörter | 2,1 % | 9,4 % | **8,1 %** |
| Satzlänge Ø / Streuung | 35,1 / 30,0 | 22,5 / 17,1 | **23,7 / 17,3** |

Zwei Werte weichen weiter ab, und beide bleiben so:

**Die kurzen Sätze (8,1 % statt 2,1 %).** Nachgesehen: es sind Szenenüberschriften („Then Reading.", „And then Austria.", „Little Venice."), Zitate („Now listen, lads.") und Tatsachen („She could not drive."). Keine davon ist eine gebaute Pointe. Ein Buch aus fünfzehn Kapiteln braucht Schnitte, die eine Monatskolumne nicht braucht.

**Die Streuung (17 statt 30).** Levens Extremwert entsteht durch einzelne Kolumnensätze von über dreihundert Wörtern. Auf hundert Seiten wäre das der Manierismus, vor dem Stefan gewarnt hat. Die flachsten Kapitel — 11, 13, 14 — liegen bei 14 bis 15; dort wäre beim nächsten Durchgang je ein langer, anrollender Satz zu setzen, nicht mehr.
