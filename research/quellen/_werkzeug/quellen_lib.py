"""Gemeinsame Hilfen: YAML-Köpfe der Quelldateien lesen, prüfen und Felder ersetzen."""
import json
import os
import re

KATEGORIEN = [
    ("nachrufe", "Nachrufe und Gedenkartikel"),
    ("interviews", "Interviews"),
    ("portraets", "Porträts, Features, Retrospektiven"),
    ("rezensionen", "Rezensionen"),
    ("konzertberichte", "Konzertberichte"),
    ("erinnerungen", "Erinnerungen und Würdigungen"),
    ("foren", "Foren, Gästebücher, Mailinglisten"),
    ("radio-tv", "Radio, TV, Film, Podcasts"),
    ("nachschlagewerke", "Nachschlagewerke und Datenbanken"),
    ("buecher", "Bücher und wissenschaftliche Arbeiten"),
    ("meldungen", "Meldungen und Pressetexte"),
]
FELDER = ["titel", "autor", "medium", "datum", "kategorie", "art", "sprache", "thema", "url",
          "archiv", "erreichbarkeit", "sicherheit", "umfang", "abgerufen", "bezug", "gefunden_ueber"]
WERTE = {
    "erreichbarkeit": {"live", "archiv", "paywall", "verloren"},
    "sicherheit": {"belegt", "unsicher", "indirekt"},
    "umfang": {"ausfuehrlich", "kurz"},
}
KOPF = re.compile(r"\A---\n(.*?)\n---\n", re.S)
ZEILE = re.compile(r"^([a-z_]+):\s*(.*)$")


def _wert(roh):
    roh = roh.strip()
    if roh.startswith("["):
        try:
            return json.loads(roh)
        except ValueError:
            innen = roh.strip("[]")
            return [x.strip().strip('"') for x in innen.split(",") if x.strip()]
    if roh.startswith('"'):
        try:
            return json.loads(roh)
        except ValueError:
            m = re.match(r'^"((?:[^"\\]|\\.)*)"', roh)
            return m.group(1).replace('\\"', '"') if m else roh.strip('"')
    return roh.split(" #")[0].strip()


def lies(pfad):
    with open(pfad, encoding="utf-8") as f:
        text = f.read()
    m = KOPF.match(text)
    if not m:
        return None, text, ["kein YAML-Kopf"]
    meta, probleme = {}, []
    for zeile in m.group(1).split("\n"):
        if not zeile.strip() or zeile.lstrip().startswith("#"):
            continue
        z = ZEILE.match(zeile)
        if not z:
            probleme.append("unlesbare Kopfzeile: " + zeile[:70])
            continue
        meta[z.group(1)] = _wert(z.group(2))
    return meta, text, probleme


def pruefe(pfad, meta):
    probleme = []
    ordner = os.path.basename(os.path.dirname(pfad))
    for feld in FELDER:
        if feld not in meta:
            probleme.append("Feld fehlt: " + feld)
    for feld, erlaubt in WERTE.items():
        if feld in meta and meta[feld] not in erlaubt:
            probleme.append(f"{feld} ungültig: {meta[feld]!r}")
    if meta.get("kategorie") != ordner:
        probleme.append(f"kategorie {meta.get('kategorie')!r} passt nicht zum Ordner {ordner}")
    datum = meta.get("datum", "")
    if datum and not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(datum)):
        probleme.append(f"datum unüblich: {datum!r}")
    if meta.get("erreichbarkeit") == "archiv" and not meta.get("archiv"):
        probleme.append("erreichbarkeit archiv, aber kein archiv-Link")
    for feld in ("thema", "bezug"):
        if feld in meta and not isinstance(meta[feld], list):
            probleme.append(f"{feld} ist keine Liste")
    return probleme


def normalisiere_url(url):
    u = (url or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = re.sub(r"#.*$", "", u)
    return u.rstrip("/")


def setze_feld(text, feld, wert):
    """Ersetzt einen skalaren Kopfwert und gibt den neuen Text zurück."""
    m = KOPF.match(text)
    kopf = m.group(1)
    neu = re.sub(rf"^{feld}:.*$", f"{feld}: {json.dumps(wert, ensure_ascii=False)}", kopf, count=1, flags=re.M)
    return text[: m.start(1)] + neu + text[m.end(1):]


def alle(wurzel):
    for kat, _ in KATEGORIEN:
        ordner = os.path.join(wurzel, kat)
        if not os.path.isdir(ordner):
            continue
        for name in sorted(os.listdir(ordner)):
            if name.endswith(".md"):
                yield os.path.join(ordner, name)
