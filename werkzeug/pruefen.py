#!/usr/bin/env python3
"""Meldet Satzformen, die bei Leven selten oder gar nicht vorkommen.

    python3 werkzeug/pruefen.py                 # alle Kapitel
    python3 werkzeug/pruefen.py 07 08           # einzelne

Das Werkzeug entscheidet nichts. Jeder Treffer ist ein Kandidat, der im
Zusammenhang gelesen werden muss: „They danced." ist ein Satz über tanzende
Männer, „Only one of them is a room." ist eine Pointe. Der Zähler sieht den
Unterschied nicht.

Die Schwellen stammen aus der Messung gegen research/columns/ (90.000 Wörter
von Leven, 979 Absätze) vom 17. September 2026.
"""
import re, sys, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIGUREN = [
    ('Existenz-Eröffnung',      r'^(?:And )?There (?:was|is|were|are)\b',
     'Leven 0,8 % der Absätze — er stellt Dinge nicht vor, sie kommen in Bewegung herein'),
    ('Kopula-Definition',       r'^[A-Z][\w\']+(?: [A-Z][\w\']+)? (?:was|is) (?:my|a|an|the) ',
     'Registerauszug statt Handlung'),
    ('Datum zuerst',            r'^(?:In|On|By) (?:1[89]\d\d|20\d\d)\b',
     'Leven 0 von 979 Absätzen'),
    ('Rückverweis-Cleft',       r'^It was (?:there|then|at|in) (?:that )?',
     'Textverwaltung, kein Erzählen'),
    ('bewertender Anschluss',   r'\b(?:and|which) (?:is|was) (?:one of|the (?:whole|only|single|most)|not)\b',
     'die angehängte Bewertung des eben Gesagten'),
    ('Antithese mit sondern',   r'\b(?:was|is|were) not\b[^.]{3,60}\b(?:but|it was|it is)\b',
     'nicht X, sondern Y'),
    ('Selbstcharakterisierung', r'\b(?:men|people|the sort of (?:man|people)) (?:of my type|like me|who)\b.{0,40}\bdo\b',
     'er beschreibt, was er tat, nicht zu welchem Typus es gehört'),
    ('Ankündigung',             r'^(?:Now the|Here (?:are|is)|What follows|Let me (?:tell|say)|i want to (?:talk|say|tell))\b',
     'ein Satz über den eigenen Text'),
    ('nummerierte Weisheit',    r'^\*{0,2}(?:One|Two|Three|Four|Five)\.\*{0,2}\s',
     'kommt in 90.000 Wörtern Leven kein einziges Mal vor'),
    ('Merksatz-Verdacht',       r'^(?:That|This|It) (?:is|was) (?:the|not|all|what|why|how)\b',
     'zusammenfassender Satz — im Zusammenhang prüfen'),
]

def body(p: Path) -> str:
    t = p.read_text(encoding='utf-8', errors='ignore')
    if t.startswith('---'):
        t = t.split('---', 2)[2]
    t = t.split('## Belegt / erfunden')[0]
    t = re.sub(r'(?m)^>.*$', '', t)
    t = re.sub(r'(?m)^#.*$', '', t)
    return re.sub(r'\*\*', '', t)

def saetze(t):
    for para in re.split(r'\n\s*\n', t):
        para = para.strip()
        if not para:
            continue
        teile = [s.strip() for s in re.split(r'(?<=[.!?])\s+', para) if s.strip()]
        for i, s in enumerate(teile):
            yield s, (i == len(teile) - 1), len(teile)

def pruefe(pfad: Path):
    t = body(pfad)
    treffer = []
    for satz, ist_schluss, n in saetze(t):
        for name, pat, grund in FIGUREN:
            if re.search(pat, satz):
                treffer.append((name, satz))
                break
        else:
            # kurzer Absatzschluss ohne konkretes Substantiv: Pointenverdacht
            if ist_schluss and n > 2 and len(satz.split()) <= 9:
                treffer.append(('kurzer Absatzschluss', satz))
    laengen = [len(s.split()) for s, _, _ in saetze(t) if len(s.split()) >= 2]
    return treffer, statistics.mean(laengen), statistics.pstdev(laengen)

def main():
    wahl = sys.argv[1:]
    dateien = sorted((ROOT/'autobiografie').glob('[01][0-9]-*.md'))
    dateien = [d for d in dateien if not d.name.startswith('00')]
    if wahl:
        dateien = [d for d in dateien if any(d.name.startswith(w) for w in wahl)]
    gesamt = 0
    for d in dateien:
        treffer, mittel, streuung = pruefe(d)
        gesamt += len(treffer)
        print(f"\n{'='*78}\n{d.name}   Ø {mittel:.1f} Wörter, Streuung {streuung:.1f}   {len(treffer)} Kandidaten")
        for name, satz in treffer:
            kurz = satz if len(satz) <= 150 else satz[:147] + '…'
            print(f"  [{name:22}] {kurz}")
    print(f"\n{gesamt} Kandidaten insgesamt. Jeder einzelne ist im Zusammenhang zu lesen.")

if __name__ == '__main__':
    main()
