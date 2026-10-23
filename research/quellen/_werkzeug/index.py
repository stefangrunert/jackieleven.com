"""Erzeugt research/quellen/index.json und den Abschnitt „Übersicht“ in research/quellen/README.md;
meldet Formfehler und URL-Dubletten.

Aufruf: python3 research/quellen/_werkzeug/index.py research/quellen
Alles in README.md ab der Zeile „## Übersicht“ wird ersetzt, der Text davor bleibt.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quellen_lib import KATEGORIEN, alle, lies, normalisiere_url, pruefe  # noqa: E402

MARKE = "## Übersicht"
ERREICHBAR = {"live": "live", "archiv": "nur Archiv", "paywall": "Paywall", "verloren": "verloren"}


def zelle(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def main(wurzel):
    eintraege, fehler = [], []
    for pfad in alle(wurzel):
        meta, _, probleme = lies(pfad)
        rel = os.path.relpath(pfad, wurzel)
        if meta is None:
            fehler.append((rel, probleme))
            continue
        probleme += pruefe(pfad, meta)
        if probleme:
            fehler.append((rel, probleme))
        meta["datei"] = rel
        eintraege.append(meta)

    nach_url = collections.defaultdict(list)
    for e in eintraege:
        if e.get("url"):
            nach_url[normalisiere_url(e["url"])].append(e["datei"])
    dubletten = {u: d for u, d in nach_url.items() if len(d) > 1}

    with open(os.path.join(wurzel, "index.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(eintraege, key=lambda e: e["datei"]), f, ensure_ascii=False, indent=1)

    zeilen = []
    zaehl = collections.Counter((e.get("kategorie"), e.get("erreichbarkeit")) for e in eintraege)
    zeilen.append("| Kategorie | Quellen | live | nur Archiv | Paywall | verloren |")
    zeilen.append("|---|---:|---:|---:|---:|---:|")
    summe = collections.Counter()
    for kat, titel in KATEGORIEN:
        werte = [zaehl[(kat, k)] for k in ERREICHBAR]
        gesamt = sum(werte)
        summe.update({k: zaehl[(kat, k)] for k in ERREICHBAR})
        zeilen.append(f"| [{titel}](#{kat}) | {gesamt} | " + " | ".join(map(str, werte)) + " |")
    zeilen.append(f"| **Gesamt** | **{len(eintraege)}** | " + " | ".join(str(summe[k]) for k in ERREICHBAR) + " |")
    zeilen.append("")
    sprachen = collections.Counter(e.get("sprache") or "?" for e in eintraege)
    zeilen.append("Sprachen: " + ", ".join(f"{s} {n}" for s, n in sprachen.most_common()) + ".")
    zeilen.append("")

    for kat, titel in KATEGORIEN:
        liste = sorted((e for e in eintraege if e.get("kategorie") == kat),
                       key=lambda e: (str(e.get("datum") or "9999"), e["datei"]))
        zeilen.append(f'<a id="{kat}"></a>')
        zeilen.append(f"### {titel} ({len(liste)})")
        zeilen.append("")
        if not liste:
            zeilen.append("Keine Einträge.")
            zeilen.append("")
            continue
        zeilen.append("| Datum | Titel | Autor · Medium | Art | Spr. | Erreichbarkeit | Datei |")
        zeilen.append("|---|---|---|---|---|---|---|")
        for e in liste:
            autor = " · ".join(x for x in (zelle(e.get("autor")), zelle(e.get("medium"))) if x)
            erreichbar = ERREICHBAR.get(e.get("erreichbarkeit"), zelle(e.get("erreichbarkeit")))
            if e.get("sicherheit") in ("unsicher", "indirekt"):
                erreichbar += f" ({e['sicherheit']})"
            name = os.path.basename(e["datei"])
            zeilen.append(f"| {zelle(e.get('datum')) or '–'} | {zelle(e.get('titel'))} | {autor} | "
                          f"{zelle(e.get('art'))} | {zelle(e.get('sprache'))} | {erreichbar} | "
                          f"[{zelle(name[:-3])}]({e['datei']}) |")
        zeilen.append("")

    readme = os.path.join(wurzel, "README.md")
    kopf = open(readme, encoding="utf-8").read().split(MARKE)[0] if os.path.exists(readme) else ""
    with open(readme, "w", encoding="utf-8") as f:
        f.write(kopf + MARKE + "\n\n" + "\n".join(zeilen) + "\n")

    print(f"{len(eintraege)} Einträge, {len(fehler)} Dateien mit Formfehlern, {len(dubletten)} URL-Dubletten")
    for rel, probleme in fehler:
        print("FEHLER", rel, "; ".join(probleme))
    for u, dateien in dubletten.items():
        print("DUBLETTE", u, "->", ", ".join(dateien))


if __name__ == "__main__":
    main(sys.argv[1])
