"""Zentrale Nachprüfung: HTTP-Status der Original-URLs und Wayback-Snapshots für Einträge ohne Archivlink.

Aufruf: python3 -I research/quellen/_werkzeug/pruefung.py research/quellen <cache.json außerhalb des Repos> [--live] [--wayback] [--schreiben]
Ergebnisse werden im Cache gehalten, ein erneuter Lauf setzt dort fort.
--schreiben trägt gefundene Snapshots in leere archiv-Felder ein; erreichbarkeit wird nie automatisch geändert.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quellen_lib import alle, lies, setze_feld  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"


def holen(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,de;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.read(400000)
    except urllib.error.HTTPError as e:
        return e.code, url, b""
    except Exception as e:  # noqa: BLE001
        return f"fehler: {type(e).__name__}", url, b""


def speichern(cache, pfad):
    tmp = pfad + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)
    os.replace(tmp, pfad)


def main():
    wurzel, cachepfad = sys.argv[1], sys.argv[2]
    flags = set(sys.argv[3:])
    cache = json.load(open(cachepfad, encoding="utf-8")) if os.path.exists(cachepfad) else {"live": {}, "wayback": {}}
    eintraege = []
    for pfad in alle(wurzel):
        meta, _, _ = lies(pfad)
        if meta and meta.get("url"):
            eintraege.append((pfad, meta))

    if "--live" in flags:
        letzter = {}
        for pfad, meta in eintraege:
            url = meta["url"]
            if url in cache["live"] or not url.startswith("http"):
                continue
            host = urllib.parse.urlparse(url).netloc
            warte = 1.5 - (time.time() - letzter.get(host, 0))
            if warte > 0:
                time.sleep(warte)
            status, ziel, _ = holen(url)
            letzter[host] = time.time()
            cache["live"][url] = {"status": status, "ziel": ziel}
            speichern(cache, cachepfad)

    if "--wayback" in flags:
        fehlversuche = 0
        for pfad, meta in eintraege:
            url = meta["url"]
            if meta.get("archiv") or url in cache["wayback"] or not url.startswith("http"):
                continue
            if urllib.parse.urlparse(url).netloc.endswith("nb.no"):
                continue
            api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
            status, _, body = holen(api, timeout=40)
            if status != 200:
                fehlversuche += 1
                print("wayback", status, url, file=sys.stderr)
                time.sleep(900 if fehlversuche >= 3 else 120)
                if fehlversuche >= 3:
                    fehlversuche = 0
                continue
            fehlversuche = 0
            try:
                snap = json.loads(body).get("archived_snapshots", {}).get("closest") or {}
            except ValueError:
                snap = {}
            cache["wayback"][url] = snap.get("url", "") if snap.get("available") and str(snap.get("status")) == "200" else ""
            speichern(cache, cachepfad)
            time.sleep(5)

    if "--schreiben" in flags:
        geschrieben = 0
        for pfad, meta in eintraege:
            snap = cache["wayback"].get(meta["url"])
            if snap and not meta.get("archiv"):
                snap = snap.replace("http://web.archive.org", "https://web.archive.org")
                _, text, _ = lies(pfad)
                with open(pfad, "w", encoding="utf-8") as f:
                    f.write(setze_feld(text, "archiv", snap))
                geschrieben += 1
        print("archiv-Felder ergänzt:", geschrieben)

    # Auffälligkeiten melden
    for pfad, meta in eintraege:
        info = cache["live"].get(meta["url"])
        if not info:
            continue
        ok = isinstance(info["status"], int) and info["status"] < 400
        e = meta.get("erreichbarkeit")
        if e == "live" and not ok:
            print("LIVE?", info["status"], os.path.relpath(pfad, wurzel), meta["url"])
        if e in ("archiv", "verloren") and ok:
            print("TOT?", info["status"], os.path.relpath(pfad, wurzel), meta["url"], "->", info["ziel"])


if __name__ == "__main__":
    main()
