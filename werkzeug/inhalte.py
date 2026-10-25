#!/usr/bin/env python3
"""Offline integrity checks for the Go site's neutral content and source references.

Presentation, routing, sessions and release packaging are tested by the Go tests,
HTTP parity suite, browser workflow suite and Go release builder respectively.
"""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from content import ROOT, PROJECTS, read_json, song_key, source_path
from zitate import verify as verify_quotes, norm

CATEGORIES = {'interviews', 'portraets', 'rezensionen', 'konzertberichte', 'nachrufe', 'erinnerungen', 'radio-tv', 'foren', 'buecher', 'nachschlagewerke', 'meldungen'}
ACCESS = {'frei', 'online', 'archiv', 'abo', 'verloren'}
SERVICES = {'spotify': 'open.spotify.com', 'apple': 'music.apple.com', 'qobuz': 'www.qobuz.com', 'amazon': 'music.amazon.ca', 'bandcamp': 'jackieleven.bandcamp.com'}
DAY = re.compile(r'\d{4}-\d{2}-\d{2}\Z')
DATE = re.compile(r'\d{4}(?:-\d{2}(?:-\d{2})?)?\Z')


def validate(root=ROOT):
    root = Path(root)
    load = lambda name: read_json(root / 'data' / (name + '.json'))
    problems = []
    def check(ok, message):
        if not ok:
            problems.append(message)
    def unique(values, what):
        check(len(values) == len(set(values)), 'Duplicate ' + what)
    def remote(url):
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    def bilingual(value):
        return isinstance(value, dict) and all(lang in value for lang in ('de', 'en'))
    def asset(path):
        if not path.startswith('/assets/'):
            return remote(path)
        return source_path(root / 'assets', path.removeprefix('/assets/')).is_file()

    catalogue, details, offers = load('diskografie'), load('diskografie-details'), load('diskografie-hoerlinks')
    releases = catalogue['releases']
    ids = {p['id'] for p in releases}
    unique([p['id'] for p in releases], 'release ID')
    check([p['year'] for p in releases] == sorted(p['year'] for p in releases), 'Release chronology changed')
    languages = {lang: load('lang/' + lang) for lang in ('de', 'en')}
    projects = set()
    known_songs = set()
    for release in releases:
        ident = release['id']
        check(bool(re.fullmatch(r'\d{4}-[a-z0-9-]+', ident)), 'Invalid release ID: ' + ident)
        check(bool(release['sources']), 'Missing release provenance: ' + ident)
        for key in release['sources']:
            source = catalogue['sources'].get(key, {})
            check(remote(source.get('url', '')), 'Unknown release source: ' + key)
        projects.update(release['tags'])
        check(set(release['tags']) <= set(PROJECTS), 'Unknown release project: ' + ident)
        check(bilingual(release['notes']), 'Missing release translation: ' + ident)
        check(all('disk.type.' + release['kind'] in languages[lang] for lang in languages), 'Unknown release kind: ' + ident)
        if release.get('cover'):
            check(asset(release['cover']), 'Invalid/missing cover: ' + ident)
    check(projects == set(PROJECTS), 'A catalogued project is absent')
    for ident, detail in details.items():
        check(ident in ids and bool(detail['sources']), 'Details without release or provenance: ' + ident)
        check(all(remote(q['url']) and q['label'] for q in detail['sources']), 'Invalid detail source: ' + ident)
        for tracks in detail.get('tracklists', []):
            check(bool(tracks['tracks']), 'Empty tracklist: ' + ident)
            check('label' not in tracks or bilingual(tracks['label']), 'Missing tracklist translation: ' + ident)
            for track in tracks['tracks']:
                check(isinstance(track['number'], str) and bool(track['number']) and bool(track['title']), 'Incomplete track: ' + ident)
                known_songs.add(song_key(track['title']))
        check(all(bilingual(c['role']) and c['name'] for c in detail.get('credits', [])), 'Incomplete credits: ' + ident)
        check(all(bilingual(f['label']) and bilingual(f['value']) for f in detail.get('facts', [])), 'Incomplete recording facts: ' + ident)
    for ident, offer in offers.items():
        check(ident in ids and bool(DAY.fullmatch(offer['checked'])) and bool(offer['digitalTitle']) and bool(offer['links']), 'Invalid listening offer: ' + ident)
        unique([link['service'] for link in offer['links']], 'listening service for ' + ident)
        for link in offer['links']:
            parsed = urlparse(link['url'])
            check(parsed.scheme == 'https' and parsed.netloc == SERVICES.get(link['service']) and ('/albums/' if link['service'] == 'amazon' else '/album/') in parsed.path, 'Invalid direct album URL: ' + ident)
        tracks = sum(len(part['tracks']) for part in details.get(ident, {}).get('tracklists', []))
        if tracks != offer['trackCount']:
            check(bilingual(offer.get('note')) and all(offer['note'].values()), 'Digital edition difference without bilingual note: ' + ident)
    youtube = load('youtube-titel')
    for key, videos in youtube.items():
        check(key in known_songs, 'Video without known song: ' + key)
        videos = videos if isinstance(videos, list) else [videos]
        unique([v['url'] for v in videos], 'video for ' + key)
        for i, video in enumerate(videos):
            check(bool(re.fullmatch(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}(?:&t=\d+s)?', video['url'])), 'Invalid video URL: ' + key)
            check(video['kind'] in ('audio', 'video', 'live') and video['title'] and video['channel'], 'Incomplete song video: ' + key)
            label = video.get('label')
            check(label is None or bool(label) and (isinstance(label, str) or bilingual(label)), 'Incomplete video place: ' + key)
            check(i == 0 or video['kind'] == 'live' and label is not None, 'Additional song version is not labelled live: ' + key)
    concerts = load('live-videos')
    for name, concert in concerts.items():
        check(bool(re.fullmatch('[a-z0-9-]+', name)) and concert['title'] and DATE.fullmatch(concert['date']), 'Invalid concert: ' + name)
        check(concert['source'] in ('official', 'fan') and set(concert.get('releases', [])) <= ids, 'Invalid concert attribution/release: ' + name)
        for video in concert['videos']:
            check(bool(re.fullmatch('[A-Za-z0-9_-]{11}', video['id'])) and video['title'] and video['channel'], 'Invalid concert video: ' + name)
            check(isinstance(video['embeddable'], bool) and DAY.fullmatch(video['checked']), 'Unverified concert video: ' + video['id'])
            for song in video['songs']:
                check(song_key(song['title']) in known_songs and type(song['start']) is int and song['start'] >= 0, 'Unknown concert song/start: ' + song['title'])
            if video['embeddable']:
                path = root / 'assets/bilder/live' / (video['id'] + '.webp')
                check(path.is_file() and path.stat().st_size <= 24 * 1024, 'Missing/oversized local preview: ' + video['id'])

    sources = load('quellen')
    source_ids = {q['id'] for q in sources}
    unique([q['id'] for q in sources], 'source ID')
    for q in sources:
        ident = q['id']
        check(bool(re.fullmatch('[a-z0-9-]+', ident)) and q['titel'] and q['medium'], 'Incomplete source: ' + ident)
        check(q['stufe'] in ('auswahl', 'verzeichnis', 'weitere') and q['kategorie'] in CATEGORIES and q['zugang'] in ACCESS, 'Private/unknown source classification: ' + ident)
        check(q['datum'] == '' or DATE.fullmatch(q['datum']), 'Invalid source date: ' + ident)
        check(q['url'] or q['archiv'] or q['zugang'] == 'verloren', 'Source without link: ' + ident)
        check(q['lizenz'] is None or 'nb.no' in q['url'] and q['zugang'] == 'frei', 'License without public archive: ' + ident)
        check(bool(q['kurz']['de']) and bool(q['inhalt']['de']), 'Source without summary: ' + ident)
        check(not re.search(r'research/|\.md\b|gefunden_ueber|\bsicherheit:', json.dumps([q['kurz'], q['inhalt'], q['zitate']], ensure_ascii=False)), 'Internal working reference in public source: ' + ident)
        check(set(q['ausgaben']) <= ids, 'Source links unknown release: ' + ident)
        check(all(b['original'] and b['de'] and b['en'] for b in q.get('beleg', [])), 'Untranslated correction evidence: ' + ident)
        check(q.get('korrektur') is None or bilingual(q['korrektur']) and all(q['korrektur'].values()), 'Untranslated correction: ' + ident)
        if q['stufe'] != 'weitere':
            check(q['kurz'].get('en') and len(q['inhalt'].get('en', [])) == len(q['inhalt']['de']), 'Stale/missing English summary: ' + ident)
            check(all(not z['kontext'] or z.get('kontext_en') for z in q['zitate']), 'Untranslated quotation context: ' + ident)
    for ident, excerpts in load('quellen-auszuege').items():
        check(ident in source_ids, 'Excerpt without source: ' + ident)
        for item in excerpts:
            check(asset(item['image']) and bilingual(item['caption']) and bilingual(item['source']), 'Incomplete facsimile excerpt: ' + ident)
            check(item['width'] > 0 and item['height'] > 0 and max(item['width'], item['height']) <= 1800, 'Oversized facsimile excerpt: ' + ident)

    columns = load('kolumnen')['dateien']
    unique(columns, 'column source')
    expected = {p.name for p in (root / 'research/columns').glob('*.md') if p.name != 'README.md' and p.name[:7] <= '2011-11'}
    check(set(columns) == expected, 'Column publication boundary differs from the November 2011 collection')
    for file in columns:
        check(source_path(root / 'research/columns', file).is_file(), 'Missing column: ' + file)
    stations = load('stationen')
    unique([s['slug'] for s in stations], 'station slug')
    for station in stations:
        check(asset('/assets/bilder/' + station['bild']), 'Missing station picture: ' + station['slug'])
        check(not station.get('platte') or station['platte'] in ids, 'Station links unknown release: ' + station['slug'])
        check(not station['quelle'] or station['quelle']['datei'] in columns, 'Station links unpublished column: ' + station['slug'])
    _, quote_errors = verify_quotes(stations, root)
    problems.extend(quote_errors)
    chapters = load('pastiche')
    unique([c['slug'] for c in chapters], 'chapter slug')
    for chapter in chapters:
        check(source_path(root / 'autobiografie', chapter['slug'] + '.md').is_file(), 'Missing chapter: ' + chapter['slug'])
    home = load('startseite')
    column_slugs = {Path(file).stem.replace('_', '-'): file for file in columns}
    for section in ('pool', 'leben'):
        excerpt = home[section]
        check(excerpt['slug'] in column_slugs, 'Home excerpt links unknown column: ' + section)
        if excerpt['slug'] in column_slugs:
            text = norm(source_path(root / 'research/columns', column_slugs[excerpt['slug']]).read_text())
            if section == 'leben':
                text = text.replace('he death of my brother', 'The death of my brother')
            check(all(part.strip(' .\t\n\r') in text for part in excerpt['zitat']['en'].split('…') if part.strip(' .\t\n\r')), 'Home excerpt differs from original: ' + section)
    check(home['platte']['id'] in ids, 'Home album missing')
    check(len(home['hoeren']) == 3 and all(asset(v['preview']) for v in home['hoeren'] if v['video']), 'Home playlist preview missing')
    listening = [song for group in load('hoeren') for song in group['stuecke']]
    check(len(listening) == len({s['song'] for s in listening}) == 10, 'Listening selection must contain ten distinct songs')
    check(all(s['release'] in ids and song_key(s['song']) in youtube for s in listening), 'Listening selection lacks release/video')
    return problems, {'releases': len(releases), 'sources': len(sources), 'songs': len(youtube), 'concerts': len(concerts), 'columns': len(columns), 'chapters': len(chapters)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    problems, counts = validate(args.root)
    print(json.dumps(counts, ensure_ascii=False))
    for problem in problems:
        print('ERROR:', problem)
    raise SystemExit(bool(problems))


if __name__ == '__main__':
    main()
