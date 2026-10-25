#!/usr/bin/env python3
"""Generate data/quellen.json from research/quellen without exposing internal notes.

Default is an offline catalogue build. --check compares in memory and writes
nothing. --lizenzen explicitly refreshes National Library access metadata online.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from content import ROOT, PROJECTS, identity, read_json, source_path, write_json

SELECTED = {'erinnerungen/2019-04-10_norman-lamont_drinking-with-jackie-leven.md',
 'erinnerungen/2021-07-20_the-guardian_ian-rankin-jackie-leven-should-be-revered.md',
 'interviews/1978-11-18_record-mirror_chris-westwood-doll-by-doll.md',
 'interviews/1979-03_zigzag_night-of-the-psychotic-woodsmen.md',
 'interviews/1995-11-03_rolling-stone-de_auf-den-spuren-von-iron-john.md',
 'interviews/1998-10-26_bergensavisen_spirituell-bergensvenn.md',
 'interviews/2001-06-28_the-independent_always-look-on-the-dark-side-of-life.md',
 'interviews/2001-07-19_gaesteliste_das-leben-ist-ein-langer-dunkler-whisky.md',
 'interviews/2001-07-26_the-guardian_i-am-an-abject-failure.md',
 'interviews/2003-03-01_bergensavisen_leven-gar-i-fengsel.md',
 'interviews/2004-04_the-word_ian-rankin-and-jackie-leven-interview.md',
 'interviews/2008-07-23_whiskyfun_music-and-whisky-interview-jackie-leven.md',
 'interviews/2011-08-28_pennyblackmusic_jackie-leven-interview.md',
 'konzertberichte/1997-06_q_bawdy-jackie-leven-shocks-scandinavia.md',
 'nachrufe/2011-11-15_the-guardian_jackie-leven-obituary.md',
 'nachrufe/2011-11-16_herald-scotland_jackie-leven-obituary.md',
 'nachrufe/2011-11-16_louder-than-war_jackie-leven-obituary-by-kevin-hewick.md',
 'nachrufe/2012-03_the-word_the-jackie-leven-obituary.md',
 'portraets/1996-04-26_the-independent_man-trouble.md',
 'portraets/1998-03-06_nordlys_live-med-leven.md',
 'portraets/2000-02-03_the-daily-telegraph_the-lost-star-of-british-pop.md',
 'portraets/2010-02-24_telegraph-blogs_the-rock-star-and-the-prime-minister.md',
 'portraets/2010-04-22_chicago-reader_a-cult-artists-cult-artist.md',
 'portraets/2015-06-16_the-guardian_cult-heroes-jackie-leven.md',
 'portraets/2023-01-17_the-sunday-post_he-just-soaked-up-life-he-ate-up-life-th.md',
 'radio-tv/2010-12-01_bbc-radio-scotland_stark-talk-jackie-leven.md',
 'radio-tv/undatiert_stv_artery-jackie-leven-dokumentation.md'}
DETAILED = {'interviews', 'portraets', 'nachrufe', 'erinnerungen', 'konzertberichte', 'rezensionen', 'radio-tv', 'foren'}
SENTENCE_END = re.compile(r'(?<=[.!?…])(?<!\bSt\.)(?<!\bNr\.)(?<!\bDr\.)(?<!\bMr\.)(?<!\bca\.)(?<!\bvs\.)(?<!\bvgl\.)(?<!\b[A-Za-z]\.)(?<!\d\.)\s+(?=[A-ZÄÖÜ0-9„"*(])')


def level(q, override):
    if override is not None:
        return override
    if q['datei'] in SELECTED:
        return 'auswahl'
    if q['sicherheit'] == 'indirekt':
        return 'intern'
    if 'sammeldatei' not in q['art'].lower() and q['kategorie'] in DETAILED and (q['sicherheit'] == 'belegt' or q['umfang'] == 'ausfuehrlich'):
        return 'verzeichnis'
    return 'weitere'


def source_sections(path):
    match = re.fullmatch(r'---\n(.*?)\n---\n(.*)', Path(path).read_text(encoding='utf-8'), re.S)
    if not match:
        raise ValueError(f'Missing source header: {path}')
    explicit = re.search(r'^stufe:\s*"?(auswahl|verzeichnis|weitere|intern)"?\s*$', match[1], re.M)
    sections = {}
    for block in re.split(r'^## ', match[2], flags=re.M):
        if block.strip():
            title, _, rest = block.partition('\n')
            sections[title.strip()] = rest.strip()
    return explicit[1] if explicit else None, sections


def paragraphs(text):
    result = []
    for paragraph in re.split(r'\n\s*\n', text):
        paragraph = re.sub(r'\s*\([^()]*(?:research/|\.md\b)[^()]*\)', '', paragraph)
        paragraph = ' '.join(s for s in SENTENCE_END.split(paragraph.strip()) if not re.search(r'research/|\.md\b|README', s))
        if paragraph.strip():
            result.append(paragraph.strip())
    return result


def quotes(text):
    result = []
    for block in re.split(r'\n(?=>)', text):
        if not block.lstrip().startswith('>'):
            continue
        line = re.sub(r'^>\s?', '', block, flags=re.M).strip()
        match = re.fullmatch(r'[„"“«»](.+?)[“"”«»]\s*[–—]\s*(.+)', line, re.S) or re.fullmatch(r'[„"“«»](.+?)[“"”«»]\s*(?:-\s*(.+))?', line, re.S)
        if match:
            result.append({'text': match[1].strip(), 'kontext': (match[2] or '').strip()})
        elif line:
            result.append({'text': line, 'kontext': ''})
    return result


def evidence(text):
    result = []
    for block in re.split(r'\n\s*\n', text.strip()):
        original = re.search(r'^>\s?(.+)$', block, re.M)
        if original:
            item = {'original': original[1].strip()}
            for lang in ('de', 'en'):
                match = re.search(r'^' + lang + r':\s*(.+)$', block, re.M)
                item[lang] = match[1].strip() if match else ''
            result.append(item)
    return result


def correction(text):
    values = {lang: re.search(r'^' + lang + r':\s*(.+)$', text, re.M) for lang in ('de', 'en')}
    return {lang: match[1].strip() for lang, match in values.items()} if all(values.values()) else None


def short_text(paragraph):
    sentences = SENTENCE_END.split(paragraph)
    result = sentences[0]
    if len(result) < 90 and len(sentences) > 1:
        result += ' ' + sentences[1]
    return result[:300] + '…' if len(result) > 320 else result


def editions(topics, day, title, releases):
    year = int(day[:4]) if day[:4].isdigit() else 9999
    projects = {identity(name) for name in PROJECTS.values()}
    found = {}
    for topic in topics:
        key = identity(topic)
        if key in projects and not 1980 <= year <= 1982:
            continue
        candidates = [p for p in releases if identity(p['title']) == key and p['year'] <= year + 1]
        if candidates:
            candidates.sort(key=lambda p: (-p['year'], p['kind'] in ('single', 'ep')))
            found[candidates[0]['id']] = key in identity(title)
    return [key for key, in_title in found.items() if in_title] or list(found)


def nb_urn(url):
    match = re.search(r'URN:NBN:no-nb_[A-Za-z0-9_]+', url)
    return match[0] if match else None


def refresh_licenses(index, cached, fetch=None):
    """Explicit online operation; injectable transport keeps regression tests offline."""
    if fetch is None:
        def fetch(url):
            with urlopen(url, timeout=20) as response:
                return json.load(response)
    result = dict(cached)
    for q in index:
        urn = nb_urn(q['url'])
        if not urn:
            continue
        try:
            info = fetch('https://api.nb.no/catalog/v1/items?' + urlencode({'q': urn, 'searchType': 'FULL_TEXT_SEARCH'}))['_embedded']['items'][0]['accessInfo']
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            print(f'ohne Antwort: {urn}')
            continue
        result[urn] = {'license': info.get('license', ''), 'access': info.get('accessAllowedFrom', ''), 'checked': date.today().isoformat()}
        time.sleep(.15)
    return dict(sorted(result.items()))


def build(root=ROOT, licenses=None):
    root = Path(root)
    index = read_json(root / 'research/quellen/index.json')
    if licenses is None:
        path = root / 'data/quellen-lizenzen.json'
        licenses = read_json(path) if path.exists() else {}
    path = root / 'data/quellen-en.json'
    english = read_json(path) if path.exists() else {}
    recurring = english.get('_angaben', {})
    releases = read_json(root / 'data/diskografie.json')['releases']
    result, stale = [], 0
    for q in index:
        explicit, sections = source_sections(source_path(root / 'research/quellen', q['datei']))
        selected = level(q, explicit)
        if selected == 'intern':
            continue
        body = paragraphs(sections.get('Inhalt', ''))
        info = licenses.get(nb_urn(q['url']), {})
        license = {'name': info['license'], 'checked': info['checked']} if info.get('license') in ('ccbyncnd', 'ccbync') and info.get('access') == 'EVERYWHERE' else None
        access = 'frei' if license else {'live': 'online', 'archiv': 'archiv', 'paywall': 'abo'}.get(q['erreichbarkeit'], 'verloren')
        source_id = Path(q['datei']).stem.replace('_', '-')
        short = re.sub(r'\s+', ' ', sections['Kurz']).strip() if sections.get('Kurz', '').strip() else short_text(body[0]) if body else ''
        excerpts = quotes(sections.get('Zitate', ''))
        en = english.get(source_id)
        if en is not None and en['quelle'] != hashlib.sha1(('\n'.join(body) + short).encode()).hexdigest():
            en, stale = None, stale + 1
        if en is not None:
            for number, quote in enumerate(excerpts):
                translated = en.get('zitate_kontext', [])
                quote['kontext_en'] = translated[number] if number < len(translated) else ''
        en = en or {}
        translated = {key: en.get(key, recurring.get(q[key]) if key != 'titel' else None) for key in ('titel', 'medium', 'autor')}
        translated = {key: value for key, value in translated.items() if value}
        item = {key: q[key] for key in ('titel', 'autor', 'medium', 'datum', 'kategorie', 'art', 'sprache', 'url', 'archiv')}
        item.update(id=source_id, stufe=selected, zugang=access, lizenz=license, kurz={'de': short}, inhalt={'de': body},
            zitate=excerpts, beleg=evidence(sections.get('Beleg', '')), korrektur=correction(sections.get('Korrektur', '')),
            en=translated or [], ausgaben=editions(q['thema'], q['datum'], q['titel'], releases) if q['kategorie'] == 'rezensionen' else [])
        for field in ('kurz', 'inhalt'):
            if field in en:
                item[field]['en'] = en[field]
        result.append(item)
    ranks = {'auswahl': 0, 'verzeichnis': 1, 'weitere': 2}
    result.sort(key=lambda q: (q['datum'] == '', q['datum'], ranks[q['stufe']], q['id']))
    return result, {'stale_translations': stale, 'internal': len(index) - len(result), 'levels': dict(Counter(q['stufe'] for q in result))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', action='store_true', help='Compare against the existing output; do not write files')
    parser.add_argument('--lizenzen', action='store_true', help='Explicitly refresh licensing/access metadata online')
    args = parser.parse_args()
    if args.check and args.lizenzen:
        parser.error('--check is offline; use --lizenzen separately')
    licenses = None
    if args.lizenzen:
        path = args.root / 'data/quellen-lizenzen.json'
        licenses = refresh_licenses(read_json(args.root / 'research/quellen/index.json'), read_json(path) if path.exists() else {})
        write_json(path, licenses)
    catalogue, stats = build(args.root, licenses)
    output = args.output or args.root / 'data/quellen.json'
    if args.check:
        if read_json(output) != catalogue:
            raise SystemExit('Catalogue differs: review the research/translation changes before regenerating.')
    else:
        write_json(output, catalogue)
    print(json.dumps({'sources': len(catalogue), **stats, 'check': args.check}, ensure_ascii=False))


if __name__ == '__main__':
    main()
