"""Explicit adapters for public pages and labelled public archive records.

No recursive import of research notes, template variables or private filesystem content.
"""
from collections import Counter
from html.parser import HTMLParser
import re
from urllib.parse import quote, urlparse

SECTIONS = {'music', 'live', 'timeline', 'writing', 'press', 'biography', 'site'}


def page_urls(langs, route, slug=None):
    return {f'url_{lang}': '/' + lang + '/' + langs[lang]['pfad.' + route] + ('/' + slug if slug else '') for lang in ('de', 'en')}


def base(document, title, section, urls, input_file, revision, **metadata):
    return {'document_id': document, 'title': title, 'source_voice': 'editorial', 'year': None, **urls,
            'metadata': {'section': section, 'fiction': False, 'identity_scope': 'private_search',
                         'record_kind': 'site', 'input_file': input_file, 'source_revision': revision, **metadata}}


def image_url(value):
    if isinstance(value, str) and (value.startswith('/assets/') or urlparse(value).scheme == 'https'):
        return value
    return None


def fragments(value):
    return [str(v) for v in value if v is not None and str(v).strip()]


def record(append, b, values, lang, family, selector):
    """Readable record from explicitly displayed fields, not invented source prose."""
    parts = fragments(values)
    if parts:
        append({**b, 'metadata': {**b['metadata'], 'representation': 'displayed_record', 'display_fragments': parts}},
               '\n'.join(parts), lang, 'summary', 'editorial', family, selector, original=True)


def music(website, langs, append):
    releases = website.json('data/diskografie.json')
    details = website.json('data/diskografie-details.json')
    listening = website.json('data/diskografie-hoerlinks.json')
    tracks = 0
    for i, release in enumerate(releases['releases']):
        rid = release['id']
        b = base('private/document/release/' + rid, release['title'], 'music', page_urls(langs, 'diskografie', rid),
                 'data/diskografie.json', website.revision, record_kind='release', display_date=str(release['year']),
                 image=image_url(release.get('cover')), release_id=rid)
        b['year'] = int(release['year'])
        for lang in ('de', 'en'):
            record(append, b, [release['artist'], release['title'], release['year'], langs[lang].get('disk.type.' + release['kind']),
                              release['format'], release['label'], release['catalog']], lang, 'release-header:' + lang, f'/releases/{i}')
            catalog = {**b, **{key: value + '#' + rid for key, value in page_urls(langs, 'diskografie').items()}}
            if release.get('notes', {}).get(lang):
                append(catalog, release['notes'][lang], lang, 'summary', 'editorial', 'release-notes:' + lang, f'/releases/{i}/notes/{lang}', original=True)
            if release.get('tracks'):
                record(append, catalog, [langs[lang]['disk.weitere_titel'], ' / '.join(release['tracks'])], lang, 'catalog-tracks:' + lang, f'/releases/{i}/tracks')
            d = details.get(rid, {})
            db = {**b, 'metadata': {**b['metadata'], 'input_file': 'data/diskografie-details.json'}}
            for fi, fact in enumerate(d.get('facts', [])):
                record(append, db, [fact.get('label', {}).get(lang), fact.get('value', {}).get(lang)], lang, 'facts:' + lang, f'/{rid}/facts/{fi}')
            for ci, credit in enumerate(d.get('credits', [])):
                record(append, db, [credit.get('role', {}).get(lang), credit['name']], lang, 'credits:' + lang, f'/{rid}/credits/{ci}')
            for li, tracklist in enumerate(d.get('tracklists', [])):
                for ti, track in enumerate(tracklist['tracks']):
                    if lang == 'de': tracks += 1
                    tb = {**db, 'metadata': {**db['metadata'], 'record_kind': 'track', 'track_title': track['title'], 'track_number': track.get('number')}}
                    record(append, tb, [tracklist.get('label', {}).get(lang), track.get('number'), track['title'], track.get('artist'), track.get('duration')], lang,
                           f'tracks-{li}:' + lang, f'/{rid}/tracklists/{li}/tracks/{ti}')
            for si, source in enumerate(d.get('sources', [])):
                record(append, db, [source['label']], lang, 'release-sources:' + lang, f'/{rid}/sources/{si}/label')
            note = listening.get(rid, {}).get('note', {}).get(lang) if isinstance(listening.get(rid), dict) else None
            if note:
                append({**b, 'metadata': {**b['metadata'], 'input_file': 'data/diskografie-hoerlinks.json'}}, note, lang, 'summary', 'editorial', 'listening-note:' + lang, f'/{rid}/note/{lang}', original=True)
    return {'releases': len(releases['releases']), 'track_rows': tracks}


def timeline(website, langs, append):
    stations = website.json('data/stationen.json')
    texts = {lang: website.json('data/texte/' + lang + '.json') for lang in ('de', 'en')}
    for i, station in enumerate(stations):
        slug = station['slug']
        b = base('private/document/station/' + slug, texts['de'][slug]['titel'], 'timeline', page_urls(langs, 'station', slug),
                 'data/stationen.json', website.revision, record_kind='timeline', display_date=station['jahr'],
                 image='/assets/bilder/' + station['bild'])
        for lang in ('de', 'en'):
            for field in ('titel', 'label', 'text', 'bildtext'):
                actual_lang = lang if field in texts.get(lang, {}).get(slug, {}) else 'de'
                value = texts[actual_lang][slug].get(field)
                if value:
                    bb = {**b, 'title': texts[actual_lang][slug]['titel'], 'metadata': {**b['metadata'], 'input_file': 'data/texte/' + actual_lang + '.json'}}
                    append(bb, value, actual_lang, 'summary', 'editorial', field + ':' + actual_lang, f'/{slug}/{field}', original=True)
            # One original quotation, shared by both UI languages.
        if station.get('zitat'):
            append({**b, 'source_voice': 'leven', 'metadata': {**b['metadata'], 'quote_source': station.get('quelle')}},
                   station['zitat'], 'en', 'original', 'leven', 'quote:en', f'/{i}/zitat', original=True)
    return {'stations': len(stations)}


def chapter_parts(text):
    text = re.sub(r'\A---\n.*?\n---\n', '', text.replace('\r\n', '\n'), flags=re.S)
    parts = {'anmerkung': '', 'text': '', 'apparat': ''}
    match = re.search(r'^## ', text, re.M)
    if match:
        parts['apparat'], text = text[match.start():].strip(), text[:match.start()]
    quote_match = re.match(r'\A\s*((?:>.*(?:\n|$))+)', text)
    if quote_match:
        note = re.sub(r'^> ?', '', quote_match[1], flags=re.M)
        notes = [p for p in re.split(r'\n\s*\n', note.strip()) if not re.match(r'^\*\*(Hinweis|Note):\*\*', p.strip())]
        parts['anmerkung'] = '\n\n'.join(notes).strip()
        text = text[quote_match.end():]
    text = re.sub(r'^#\s+.*$', '', text, count=1, flags=re.M)
    parts['text'] = re.sub(r'\n-{3,}\s*\Z', '', text.rstrip()).strip()
    return parts


def markdown_blocks(text):
    for block in re.split(r'\n\s*\n', text.strip()):
        block = block.strip()
        if not block or re.fullmatch(r'-{3,}', block): continue
        block = re.sub(r'^> ?', '', block, flags=re.M)
        block = re.sub(r'\A#{2,6}\s+', '', block)
        yield re.sub(r'\s*\n\s*', ' ', block)


def biography(website, langs, append):
    chapters = website.json('data/pastiche.json')
    for chapter in chapters:
        slug = chapter['slug']
        if not re.fullmatch('[a-z0-9-]+', slug): raise ValueError('invalid_chapter_slug')
        source = chapter_parts(website.read('autobiografie/' + slug + '.md').decode())
        b = base('private/document/pastiche/' + slug, chapter['titel'], 'biography', page_urls(langs, 'biografie', slug),
                 'autobiografie/' + slug + '.md', website.revision, record_kind='pastiche', fiction=True,
                 display_date=chapter['zeit'], authorship='Editorial pastiche; not written by Jackie Leven')
        b['source_voice'] = 'pastiche'
        emitted = set()
        for lang in ('de', 'en'):
            path = 'autobiografie/' + lang + '/' + slug + '.md'
            translation = chapter_parts(website.read(path).decode())
            for field, origin in [('text', 'en'), ('anmerkung', 'de'), ('apparat', 'de')]:
                selected = translation[field] or source[field]
                actual_lang = lang if translation[field] else origin
                source_path = path if translation[field] else 'autobiografie/' + slug + '.md'
                identity = (field, actual_lang, selected)
                if identity in emitted: continue
                emitted.add(identity)
                for i, paragraph in enumerate(markdown_blocks(selected)):
                    bb = {**b, 'metadata': {**b['metadata'], 'input_file': source_path, 'chapter_part': field}}
                    kind = ('original' if actual_lang == 'en' else 'translation') if field == 'text' else 'summary'
                    append(bb, paragraph, actual_lang, kind, 'pastiche', field + ':' + actual_lang, {'part': field, 'block': i})
    return {'pastiche_chapters': len(chapters)}


class StaticBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag = None
        self.parts = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'h1', 'h2', 'h3', 'address'):
            self.tag, self.parts = tag, []
        elif tag == 'br' and self.tag:
            self.parts.append('\n')
    def handle_data(self, data):
        if self.tag: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == self.tag:
            value = re.sub(r'\s+', ' ', ''.join(self.parts)).strip()
            if value: self.blocks.append(value)
            self.tag = None


def site_pages(website, langs, append):
    for lang in ('de', 'en'):
        for name, route, section in [('ueber', 'ueber', 'site'), ('impressum', 'impressum', 'site'), ('biografie-intro', 'biografie', 'biography')]:
            path = f'templates/{lang}/{name}.gohtml'
            template = website.read(path).decode()
            # These localized static pages use only URL substitutions; fail closed on new dynamic content.
            for token in re.findall(r'{{(.*?)}}', template, re.S):
                if not token.strip().startswith('(url '): raise ValueError('static_template_requires_explicit_adapter')
            reader = StaticBlocks()
            reader.feed(re.sub(r'{{.*?}}', '', template, flags=re.S))
            b = base('private/document/page/' + name, langs[lang].get('nav.' + route, name), section, page_urls(langs, route), path, website.revision)
            for i, text in enumerate(reader.blocks):
                append(b, text, lang, 'summary', 'editorial', 'static:' + lang, {'block': i}, original=True)
        # Content strings actually shown on public pages; omit form values/errors/configuration labels.
        selections = {'mitmachen': ['mit.intro', 'mit.mitarbeit', 'mit.absprache', 'mit.mail', 'mit.fotos', 'mit.datenschutz'],
                      'hoeren': ['hoeren.intro_anfang', 'hoeren.intro_ende'],
                      'diskografie': ['disk.intro'], 'stimmen': ['stimmen.intro'], 'pool': ['pool.intro']}
        for route, fields in selections.items():
            section = {'diskografie': 'music', 'hoeren': 'music', 'stimmen': 'press', 'pool': 'writing'}.get(route, 'site')
            b = base('private/document/page/' + route, langs[lang].get('nav.' + route, 'The Deep Pool'), section, page_urls(langs, route), 'data/lang/' + lang + '.json', website.revision)
            for key in fields:
                if langs[lang].get(key): append(b, langs[lang][key], lang, 'summary', 'editorial', 'intro:' + lang, '/' + key, original=True)
    start = website.json('data/startseite.json')
    b = base('private/document/page/home', 'Jackie Leven', 'site', {'url_de': '/de/', 'url_en': '/en/'}, 'data/startseite.json', website.revision)
    for lang in ('de', 'en'):
        for field in ('pool', 'leben'):
            if start.get(field, {}).get('zitat', {}).get(lang):
                append({**b, 'source_voice': 'leven'}, start[field]['zitat'][lang], lang, 'original' if lang == 'en' else 'translation', 'leven', field + ':' + lang, f'/{field}/zitat/{lang}', original=True)
        for i, video in enumerate(start.get('hoeren', [])):
            record(append, b, [video.get('titel'), video.get('kuenstler'), video.get('kontext')], lang, 'home-video:' + lang, f'/hoeren/{i}')
        append(b, langs[lang]['mit.home'], lang, 'summary', 'editorial', 'home-invitation:' + lang, '/mit.home', original=True)
    for field, text in [('vers', start.get('vers')), ('platte/zeile', start.get('platte', {}).get('zeile'))]:
        if text: append({**b, 'source_voice': 'leven'}, text, 'en', 'original', 'leven', 'home-lines:en', '/' + field, original=True)
    groups = website.json('data/hoeren.json')
    releases = {r['id']: r for r in website.json('data/diskografie.json')['releases']}
    for gi, group in enumerate(groups):
        for si, song in enumerate(group['stuecke']):
            release = releases[song['release']]
            b = base('private/document/listening/' + song['release'] + '/' + str(si), song['song'], 'music', page_urls(langs, 'hoeren'), 'data/hoeren.json', website.revision,
                     record_kind='listening_selection', image=image_url(release.get('cover')), display_date=str(release['year']))
            b['year'] = int(release['year'])
            for lang in ('de', 'en'):
                record(append, b, [group['titel'][lang], song['song'], release['title'], release['artist']], lang, 'listening:' + lang, f'/{gi}/stuecke/{si}')
    return {'listening_groups': len(groups), 'listening_songs': sum(len(g['stuecke']) for g in groups), 'static_localized_templates': 6}


PREDICATES = {'time': 'Zeitangabe', 'took_place_at': 'Spielstätte', 'performance_status': 'Durchführungsstatus',
              'participants': 'Beteiligung', 'names': 'Namensform', 'identifiers': 'Externe Kennung',
              'published': 'Veröffentlichung', 'published_in': 'Publikation', 'located_in': 'Lage',
              'part_of': 'Teil von', 'members': 'Mitgliedschaft', 'performs_as': 'Künstleridentität'}


def archive_records(entities, archive, document_targets, append):
    lookup = {e['id']: e['data'] for e in entities}
    def label(value):
        return lookup.get(value, {}).get('label', value) if isinstance(value, str) else str(value)
    count = 0
    for entity in entities:
        e, eid = entity['data'], entity['id']
        section = 'live' if e['type'] == 'Event' else ('press' if e['type'] in ('Document', 'Publication') else 'site')
        urls = document_targets.get(eid) or {'url_de': '/de/suche/objekt?id=' + quote(eid, safe=''), 'url_en': '/en/search/entity?id=' + quote(eid, safe='')}
        times = [str(s.get('edtf_value')) for s in e.get('time', []) if s.get('edtf_value')]
        statuses = sorted(set(str(s['status_value']) for s in e.get('performance_status', []) if s.get('status_value')))
        places = list(dict.fromkeys(label(s['entity_value']) for s in e.get('took_place_at', []) if s.get('entity_value')))
        b = base(eid, e['label'], section, urls, 'data/' + eid + '.yaml', archive.revision,
                 identity_scope='archive', record_kind='archive_entity', entity_id=eid,
                 display_date=' | '.join(times), place=' | '.join(places), event_status=statuses[0] if len(statuses) == 1 else ('mixed' if statuses else 'unknown'),
                 event_status_values=statuses, fiction=bool(e.get('fiction')), representation='archive_record',
                 record_notice='Archivdatensatz; Aussagen und Belegstatus bleiben getrennt. Kein Originalquellentext.')
        if e.get('fiction'): b['source_voice'] = 'pastiche'
        text = ['Archivdatensatz: ' + e['label'], 'Entität: ' + eid, 'Typ: ' + e['type']]
        for key in ('document_type', 'event_type', 'place_type', 'organization_type', 'language', 'access', 'note', 'replaced_by', 'birth', 'death', 'latitude', 'longitude'):
            if e.get(key) is not None: text.append(key + ': ' + label(e[key]))
        for key in ('about', 'reviews', 'derived_from'):
            if e.get(key): text.append(key + ': ' + ' | '.join(label(x) for x in e[key]))
        append(b, '\n'.join(text), 'de', 'summary', 'pastiche' if e.get('fiction') else 'editorial', 'archive-overview:de', '/', original=True)
        for predicate, statements in e.items():
            if not isinstance(statements, list): continue
            for i, statement in enumerate(statements):
                if not isinstance(statement, dict) or not statement.get('statement_id'): continue
                count += 1
                text = ['Archiv-Aussage über ' + e['label'], PREDICATES.get(predicate, predicate) + ':']
                for key, value in statement.items():
                    if key.endswith('_value') or key in ('agent_ref', 'roles', 'instrument', 'credited_as', 'name_type', 'language', 'valid_time', 'scheme', 'match_status'):
                        values = value if isinstance(value, list) else [value]
                        text.append(key + ': ' + ' | '.join(label(v) for v in values))
                text.extend(['Rang: ' + statement.get('rank', 'normal'), 'Gewissheit: ' + statement.get('certainty', 'nicht angegeben')])
                if statement.get('note'): text.append('Anmerkung: ' + statement['note'])
                refs = statement.get('references', [])
                if not refs: text.append('Belegstatus: Kein Belegverweis an dieser Aussage.')
                for reference in refs:
                    text.append('Beleg (' + reference.get('evidence_type', 'Typ nicht angegeben') + '): ' + label(reference.get('document', 'Quelle fehlt')))
                    for key in ('locator', 'quote', 'asserted_by', 'scope'):
                        if reference.get(key): text.append(key + ': ' + label(reference[key]))
                sb = {**b, 'metadata': {**b['metadata'], 'record_kind': 'archive_statement', 'statement_id': statement['statement_id'],
                                      'predicate': predicate, 'rank': statement.get('rank', 'normal'), 'certainty': statement.get('certainty'),
                                      'evidence_types': sorted(set(r.get('evidence_type', 'unspecified') for r in refs)), 'references': refs}}
                append(sb, '\n'.join(text), 'de', 'summary', 'pastiche' if e.get('fiction') else 'editorial', 'statement-' + statement['statement_id'] + ':de', f'/{predicate}/{i}', original=True)
    return {'archive_entities': len(entities), 'archive_statements': count, 'archive_types': dict(Counter(e['data']['type'] for e in entities))}


def live_media(website, langs, append):
    """Only official, checked, embeddable videos shown by the default website."""
    videos = website.json('data/live-videos.json')
    releases = website.json('data/diskografie.json')['releases']
    details = website.json('data/diskografie-details.json')
    # Reuse the explicit published spelling map from the pinned Go adapter.
    code = website.read('internal/site/content.go').decode()
    match = re.search(r'var songAliases = map\[string\]string\{([^\n]+)\}', code)
    aliases = dict(re.findall(r'"([^"]+)": "([^"]+)"', match[1])) if match else {}
    def songkey(text):
        text = re.sub(r'(?i)^\s*(?:\d+[.)]?\s*[-–—]?\s*)', '', text)
        text = re.sub(r'(?i)\s*[\[(](?:live|edit|radio|remaster|bonus track|full version|beautiful version|from live show|etc\.)[^\])]*[\])]', '', text)
        text = re.sub(r'(?i)\s*[-–—]\s*(?:live|radio edit|edit|remaster).*$', '', text).lower()
        for a, b in [('é','e'),('è','e'),('á','a'),('à','a'),('ö','o'),('ü','u'),('ä','a'),('ø','o'),('ñ','n'),('ß','ss')]: text = text.replace(a,b)
        text = re.sub('[^a-z0-9]', '', text)
        return aliases.get(text, text)
    release_songs = {r['id']: {songkey(t['title']) for group in details.get(r['id'], {}).get('tracklists', []) for t in group['tracks']} for r in releases}
    included, excluded, songs = 0, 0, 0
    for key, concert in videos.items():
        if concert.get('source') != 'official':
            excluded += 1
            continue
        emitted = False
        for vi, video in enumerate(concert.get('videos', [])):
            if not video.get('embeddable') or not video.get('checked'): continue
            for si, song in enumerate(video.get('songs', [])):
                target = next((r['id'] for r in releases if r['id'] in concert.get('releases', []) or songkey(song['title']) in release_songs[r['id']]), None)
                if not target: continue
                songs += 1
                emitted = True
                b = base('private/document/live-video/' + key, concert['title'], 'live', page_urls(langs, 'diskografie', target), 'data/live-videos.json', website.revision,
                         record_kind='live_media', display_date=concert.get('date'), place=concert['title'], event_status='took_place', video_source='official',
                         image='/assets/bilder/live/' + video['id'] + '.webp')
                record(append, b, [concert['title'], song['title']], 'en', 'live-songs:en', f'/{key}/videos/{vi}/songs/{si}')
        included += int(emitted)
    return {'public_official_concerts': included, 'public_live_song_rows': songs, 'fan_video_groups_excluded_by_default': excluded}
