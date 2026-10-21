#!/usr/bin/env python3
"""Prüft die Übersetzungen der Pastiche gegen das Original.

    python3 werkzeug/uebersetzung.py            # alle vorhandenen Übersetzungen
    python3 werkzeug/uebersetzung.py 07 12      # einzelne Kapitel

Deutsch (autobiografie/de/): Absatzzahl, Satzgrenzen je Absatz, Wortverhältnis,
kleines „ich" am Satzanfang (Kapitel 1–13) bzw. großes (14–15), Gedankenstrich,
Anrede, Füllwörter und Satzfiguren, die das Deutsche neu mitbringt.

Englisch (autobiografie/en/): Jede Stelle in Anführungszeichen muss wortgetreu im
Korpus stehen (research/columns/, research/*.md) — sonst ist sie womöglich eine
Rückübersetzung, also ein erfundenes Zitat.

Das Werkzeug entscheidet nichts. Eine Abweichung in den Satzgrenzen kann richtig
sein, ein „vielmehr" kann richtig sein. Jeder Treffer wird im Zusammenhang gelesen.
Grundsätze: autobiografie/00-uebersetzung.md
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUCH = ROOT / 'autobiografie'

FUELLWOERTER = [
    'genau das', 'das Entscheidende', 'mit anderen Worten', 'kurz gesagt', 'letztlich',
    'schlussendlich', 'gewissermaßen', 'sozusagen', 'vielmehr', 'nicht zuletzt',
    'am Ende des Tages', 'macht Sinn', 'einmal mehr', 'Fakt ist', 'tatsächlich',
    'regelrecht', 'förmlich', 'durchaus',
]


def kapiteltext_original(pfad: Path) -> str:
    t = pfad.read_text()
    t = t.split('\n# ', 1)[1].split('\n', 1)[1]           # ab nach der Überschrift
    t = re.split(r'\n-{3,}\s*\n\s*## ', t)[0]
    return t.strip()


def kapiteltext_uebersetzung(pfad: Path) -> str:
    t = pfad.read_text()
    t = t.split('\n# ', 1)[1].split('\n', 1)[1]
    return re.split(r'\n## ', t)[0].strip()


def absaetze(text: str) -> list[str]:
    return [a.strip() for a in re.split(r'\n\s*\n', text) if a.strip()]


def satzgrenzen(a: str) -> int:
    return len(re.findall(r'[.!?;:]+[’”"‘“]?(?=\s|$)', a))


def satzanfaenge(a: str) -> list[str]:
    """Erstes Wort jedes Satzes (nach . ! ? und am Absatzanfang)."""
    teile = re.split(r'(?<=[.!?])\s+', a)
    return [re.match(r'[„"‚\'(]*(\w+)', s).group(1) for s in teile if re.match(r'[„"‚\'(]*\w', s)]


def pruefe_deutsch(nr: str, de: Path, en: Path) -> list[str]:
    meldungen = []
    a_en, a_de = absaetze(kapiteltext_original(en)), absaetze(kapiteltext_uebersetzung(de))
    if len(a_en) != len(a_de):
        meldungen.append(f'Absätze: Original {len(a_en)}, Deutsch {len(a_de)}')
    for i, (x, y) in enumerate(zip(a_en, a_de), 1):
        se, sd = satzgrenzen(x), satzgrenzen(y)
        if se != sd:
            meldungen.append(f'Absatz {i}: Satzgrenzen {se} → {sd}  „{y[:70]}…"')
        we, wd = len(x.split()), len(y.split())
        if we >= 12 and not 0.72 <= wd / we <= 1.3:
            meldungen.append(f'Absatz {i}: Wörter {we} → {wd} ({wd / we:.0%})  „{y[:70]}…"')

    klein = int(nr) <= 13
    for i, y in enumerate(a_de, 1):
        for w in satzanfaenge(y):
            if klein and w == 'Ich':
                meldungen.append(f'Absatz {i}: „Ich" groß am Satzanfang (Kap. 1–13: klein)')
            if not klein and w == 'ich':
                meldungen.append(f'Absatz {i}: „ich" klein am Satzanfang (Kap. 14–15: groß)')

    text = kapiteltext_uebersetzung(de)
    for m in re.finditer(r'\s[—–]\s|—', text):
        meldungen.append(f'Gedankenstrich „{m.group().strip()}" statt „ - ": …{text[max(0, m.start()-30):m.end()+30]}…')
    # „Sie" nur mitten im Satz melden: am Satzanfang ist es meist „sie" (Plural)
    for m in re.finditer(r'\bIhnen\b|\bSie\b', text):
        davor = text[:m.start()].rstrip()
        if m.group() == 'Sie' and (not davor or davor[-1] in '.!?:„"\n'):
            continue
        meldungen.append(f'Anrede „Sie"? …{text[max(0, m.start()-30):m.end()+30]}…')
    for w in FUELLWOERTER:
        for m in re.finditer(r'\b' + re.escape(w) + r'\b', text, re.I):
            meldungen.append(f'„{w}": …{text[max(0, m.start()-40):m.end()+40]}…')
    for m in re.finditer(r'\bnicht\b[^.;:!?]{2,60},\s*sondern\b', text):
        meldungen.append(f'„nicht …, sondern": …{text[max(0, m.start()-10):m.end()+30]}…')
    if kapiteltext_original(en).rstrip().endswith('….') and not text.rstrip().endswith('….'):
        meldungen.append('Kapitelende ohne „…." (das Original hat es)')
    return meldungen


# --------------------------------------------------------------------------

def norm(s: str) -> str:
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"').replace('„', '"')
    s = s.replace('–', '-').replace('—', '-').replace('…', '...')
    return re.sub(r'\s+', ' ', s).strip().lower()


def korpus() -> str:
    teile = [p.read_text() for p in sorted((ROOT / 'research' / 'columns').glob('*.md'))]
    teile += [p.read_text() for p in sorted((ROOT / 'research').glob('*.md'))]
    return norm('\n'.join(teile))


def zitate(text: str) -> list[str]:
    funde = re.findall(r'“([^”]+)”', text) + re.findall(r'(?<![\w])"([^"\n]+)"(?![\w])', text)
    return [z for z in funde if len(z) >= 12 or len(z.split()) >= 3]


def pruefe_englisch(en_neu: Path, original: Path, k: str) -> list[str]:
    """Documented-Teile gegen den Korpus; Invented-Teile gegen den Kapiteltext der Pastiche.
    Zitate, die der Nachweis selbst als „not secured" ausweist, gelten als deklariert."""
    meldungen = []
    text = en_neu.read_text()
    text = text[text.find('## '):] if '## ' in text else ''
    if not text:
        return ['kein Abschnitt „## Documented / invented"']
    deutsch = norm(original.read_text().split('\n## ', 1)[-1])
    pastiche = norm(kapiteltext_original(original))
    deklariert = {norm(z) for satz in re.split(r'(?<=\.)\s+', text) if 'not secured' in satz for z in zitate(satz)}
    for teil in re.split(r'(?=\*\*[A-Z][^*]+:\*\*)', text):
        erfunden = teil.startswith('**Invented:**')
        for z in zitate(teil):
            if norm(z) in deklariert:
                continue
            stuecke = [s.strip(' .,;:!?\'"') for s in re.split(r'\.\.\.|…|\[\.\.\.\]', z)]
            stuecke = [s for s in stuecke if len(s) >= 6]
            quelle = (pastiche,) if erfunden else (k, deutsch)
            if any(all(norm(s) not in q for q in quelle) for s in stuecke):
                wo = 'nicht im Kapiteltext' if erfunden else 'nicht im Korpus'
                meldungen.append(f'{wo}: “{z[:90]}{"…" if len(z) > 90 else ""}”')
    if re.search(r'[„“][^”"]*[äöüß][^”"]*["”]', text):
        meldungen.append('deutsche Wörter in Anführungszeichen — übersehene Wiedergabe?')
    return meldungen


def main():
    wahl = sys.argv[1:]
    originale = sorted(p for p in BUCH.glob('[01][0-9]-*.md') if not p.name.startswith('00'))
    if wahl:
        originale = [p for p in originale if any(p.name.startswith(w) for w in wahl)]
    k = None
    gesamt = 0
    for en in originale:
        nr = en.name[:2]
        de, en_neu = BUCH / 'de' / en.name, BUCH / 'en' / en.name
        if de.exists():
            m = pruefe_deutsch(nr, de, en)
            gesamt += len(m)
            print(f'{"✓" if not m else "·"} de/{en.name}' + ('' if not m else f'  {len(m)} Meldungen'))
            for x in m:
                print('    ' + x)
        if en_neu.exists() and '## ' in en_neu.read_text():
            k = k or korpus()
            m = pruefe_englisch(en_neu, en, k)
            gesamt += len(m)
            print(f'{"✓" if not m else "·"} en/{en.name}' + ('' if not m else f'  {len(m)} Meldungen'))
            for x in m:
                print('    ' + x)
    print(f'\n{gesamt} Meldungen. Jede im Zusammenhang lesen.')


if __name__ == '__main__':
    main()
