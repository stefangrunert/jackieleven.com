#!/usr/bin/env python3
"""Misst die Pastiche-Kapitel gegen Jackie Levens eigene Prosa.

    python3 werkzeug/messen.py

Der Maßstab liegt im Haus: 76 Texte von Leven selbst in research/columns/.
Gemessen wird, was den Maschinentakt verrät — gleichförmige Satzlänge, die
gebaute Pointe am Absatzende, die Antithese, der Merksatz.
"""
import re, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def body(p: Path) -> str:
    t = p.read_text(encoding='utf-8', errors='ignore')
    if t.startswith('---'):
        t = t.split('---', 2)[2]
    t = t.split('## Belegt / erfunden')[0]
    t = re.sub(r'(?m)^>.*$', ' ', t)          # Hinweisblöcke
    t = re.sub(r'(?m)^#.*$', ' ', t)          # Überschriften
    t = re.sub(r'\*+', '', t)
    return t

def sentences(t: str):
    t = re.sub(r'\.{2,}', '… ', t)
    parts = re.split(r'(?<=[.!?])\s+', t)
    return [s.strip() for s in parts if len(s.split()) >= 2]

def paragraphs(t: str):
    return [p.strip() for p in re.split(r'\n\s*\n', t) if len(p.split()) >= 15]

FIGUREN = {
    'Antithese (not X, …)': r'(?i)\bis not\b[^.]{2,60}\bit is\b|\bnot\b[^.,]{2,40}, (?:but|it)\b',
    'Merksatz-Schluss (kurzer Aussagesatz am Absatzende)': None,   # gesondert
    'bewertender Schluss (that is / which is)': r'(?i)\b(?:and )?that (?:is|was) (?:the|one of|not)\b|\bwhich is (?:the|that|why|what)\b',
    'Ankündigung': r'(?i)^(?:now|here (?:are|is)|and now|what follows)\b|\bsince (?:somebody|nobody) \w+ (?:ought|does)\b',
    'Rückgriff/Ringschluss': r'(?i)\b(?:as i (?:said|wrote) (?:above|earlier)|that is the whole of it|all of this comes back)\b',
    'Stakkato (Satz < 5 Wörter)': None,
}

def messen(paths, label):
    txt = ' '.join(body(p) for p in paths)
    sents = sentences(txt)
    lens = [len(s.split()) for s in sents]
    words = sum(lens)
    # Absatz-Schlusssätze
    schluss = []
    for p in (q for path in paths for q in paragraphs(body(path))):
        ss = sentences(p)
        if ss: schluss.append(len(ss[-1].split()))
    kurz = sum(1 for l in lens if l < 5)
    print(f"\n=== {label}: {len(paths)} Dateien, {words} Wörter, {len(sents)} Sätze")
    print(f"  Satzlänge        Ø {statistics.mean(lens):5.1f}   Streuung {statistics.pstdev(lens):5.1f}   längster {max(lens)}")
    print(f"  Absatzschluss    Ø {statistics.mean(schluss):5.1f}   Anteil < 8 Wörter: {100*sum(1 for l in schluss if l<8)/len(schluss):4.1f} %")
    print(f"  Sätze < 5 Wörter {100*kurz/len(sents):4.1f} %")
    print(f"  Gedankenstrich   {1000*len(re.findall(r' [-–—] ', txt))/words:5.1f} je 1000 W")
    print(f"  Auslassung …     {1000*len(re.findall(r'…|\.\.\.', txt))/words:5.1f} je 1000 W")
    print(f"  Komma je Satz    {len(re.findall(r',', txt))/len(sents):5.2f}")
    for name, pat in FIGUREN.items():
        if pat:
            n = len(re.findall(pat, txt, re.M))
            print(f"  {name:52} {1000*n/words:5.2f} je 1000 W  ({n})")

leven = sorted((ROOT/'research'/'columns').glob('*.md'))
leven = [p for p in leven if p.name != 'README.md']
pastiche = sorted((ROOT/'autobiografie').glob('[01][0-9]-*.md'))
pastiche = [p for p in pastiche if not p.name.startswith('00-')]
messen(leven, 'LEVEN (Original)')
messen(pastiche, 'PASTICHE (unsere Kapitel)')
