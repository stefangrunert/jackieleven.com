"""Pinned Git snapshots to a deterministic private search corpus, no network reads."""
from collections import defaultdict, Counter
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
from urllib.parse import urldefrag
import yaml
from common import canonical, sha
from sections import music, timeline, biography, site_pages, archive_records, live_media, SECTIONS, record

ADAPTER = 'website-public-v2-chunks2400'
MAX_CHARS = 2400


class Snapshot:
    def __init__(self, root, revision):
        self.root = Path(root)
        self.revision = subprocess.check_output(['git', 'rev-parse', revision + '^{commit}'], cwd=self.root).decode().strip()
        self.files = {}

    def read(self, path):
        if Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('invalid_source_path')
        raw = subprocess.check_output(['git', 'show', self.revision + ':' + path], cwd=self.root)
        self.files[path] = sha(raw)
        return raw

    def json(self, path):
        return json.loads(self.read(path))

    def graph(self):
        raw = subprocess.check_output(['git', 'archive', '--format=tar', self.revision, 'data'], cwd=self.root)
        entities = []
        with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.startswith('data/') and member.name.endswith('.yaml'):
                    data = tar.extractfile(member).read()
                    self.files[member.name] = sha(data)
                    entity = yaml.safe_load(data)
                    if not isinstance(entity, dict) or not entity.get('id'):
                        raise ValueError('archive_entity_invalid')
                    entities.append({'id': entity['id'], 'data': entity})
        if not entities or len({e['id'] for e in entities}) != len(entities):
            raise ValueError('archive_graph_incomplete')
        return sorted(entities, key=lambda e: e['id'])


def inline(text):
    # Match the deliberately small site's MarkdownInline reader; never interpret raw HTML.
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.S)
    text = re.sub(r'(?<![A-Za-z0-9_*])\*(\S(?:.*?\S)?)\*(?![A-Za-z0-9_*])', r'\1', text, flags=re.S)
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'\1', text)


def chunks(text):
    """Contiguous readable chunks; never synthesize or drop an overlong remainder."""
    text = text.strip()
    while text:
        if len(text) <= MAX_CHARS:
            yield text
            break
        cut = max(text.rfind('. ', 0, MAX_CHARS), text.rfind('! ', 0, MAX_CHARS), text.rfind('? ', 0, MAX_CHARS))
        if cut >= MAX_CHARS // 2:
            cut += 1
        else:
            cut = text.rfind(' ', 0, MAX_CHARS)
            if cut < MAX_CHARS // 2:
                cut = MAX_CHARS
        yield text[:cut].strip()
        text = text[cut:].strip()


def year(value):
    match = re.match(r'^(\d{4})(?:-|$)', str(value or ''))
    return int(match[1]) if match else None


def column_text(raw, filename):
    match = re.match(r'\A---\n(.*?)\n---\n(.*)\Z', raw.replace('\r\n', '\n'), re.S)
    if not match:
        raise ValueError('column_frontmatter_invalid')
    # The Go loader accepts these quoted scalar fields, not arbitrary YAML coercions.
    meta = dict(re.findall(r'^([a-z_]+):\s*"([^"\n]*)"\s*$', match[1], re.M))
    text = re.sub(r'\A\s*# [^\n]*\n', '', match[2]).strip()
    art = filename.split('_')[1]
    title = meta.get('titel', '')
    if art not in ('deep-pool', 'ankuendigung') and title != '.' and not title.endswith('…') and not re.sub(r'\s+', ' ', text).startswith(title):
        text = title + '\n\n' + text
    if filename == '2007-09_deep-pool_september-2007.md':
        prefix = 'A\nugust 2006\n\nMarch 2003a\n\n'
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = re.sub(r'^!\[[^\]]*\]\(bilder/[^)]+\)\s*$', '', text, flags=re.M).strip()
    if art == 'deep-pool':
        pattern = r'\A(?:Monthly column - [A-Za-z]+ \d{4}|THE DEEP POOL(?: - [A-Z]+ \d{4}(?: - no\.\d+)?)?)\n\s*\n'
        while re.match(pattern, text):
            text = re.sub(pattern, '', text, count=1)
    return meta, art, text


def export(website, archive, state):
    entities = archive.graph()
    docs = {e['id']: e['data'] for e in entities if e['data'].get('type') == 'Document'}
    by_url = defaultdict(list)
    for did, doc in docs.items():
        if doc.get('url'):
            by_url[urldefrag(doc['url'])[0]].append(did)
    catalog = website.json('data/quellen.json')
    source_excerpts = website.json('data/quellen-auszuege.json')
    source_scans = website.json('data/quellen-scans.json')
    langs = {l: website.json('data/lang/' + l + '.json') for l in ('de', 'en')}
    candidates = []
    documents = set()
    def append(base, text, language, kind, voice, family, locator, original=False):
        if not isinstance(text, str):
            raise ValueError('unexpected_text_type')
        readable = text if original else inline(text)
        for index, part in enumerate(chunks(readable)):
            documents.add(base['document_id'])
            candidates.append({**base, 'text': part, 'language': language, 'text_kind': kind,
                               'text_voice': voice, 'content_hash': sha(part), '_family': family,
                               'metadata': {**base['metadata'], 'source_selector': locator,
                                            'chunk': index, 'version_group': base['document_id'] + '#' + family.rsplit(':', 1)[0]}})
    for qi, q in enumerate(catalog):
        if q.get('fiction') or q.get('kategorie') == 'pastiche':
            continue
        matches = by_url.get(urldefrag(q.get('url', ''))[0], [])
        did = 'document/' + q['id']
        if did not in docs:
            did = matches[0] if len(matches) == 1 else 'private/document/source/' + q['id']
        if docs.get(did, {}).get('fiction'):
            continue
        voice = 'leven' if q.get('autor') == 'Jackie Leven' else 'third_party'
        base = {'document_id': did, 'title': q['titel'], 'source_voice': voice, 'year': year(q.get('datum')),
                'url_de': '/de/' + langs['de']['pfad.stimmen'] + '/' + q['id'],
                'url_en': '/en/' + langs['en']['pfad.stimmen'] + '/' + q['id'],
                'metadata': {'section': 'press', 'fiction': False, 'record_kind': 'source', 'display_date': q.get('datum'), 'website_source_id': q['id'], 'identity_scope': 'archive' if did in docs else 'private_search',
                             'source_url': q.get('url'), 'source_access': q.get('zugang'), 'rights': q.get('lizenz'),
                             'publication_date': q.get('datum'), 'author': q.get('autor'), 'adapter': ADAPTER,
                             'input_file': 'data/quellen.json', 'source_revision': website.revision}}
        if q.get('stufe') == 'weitere':
            base['url_de'] = '/de/' + langs['de']['pfad.stimmen'] + '?auswahl=0#' + q['id']
            base['url_en'] = '/en/' + langs['en']['pfad.stimmen'] + '?auswahl=0#' + q['id']
            base['metadata']['record_kind'] = 'catalog_source'
        for lang in ('de', 'en'):
            translated = q.get('en') if lang == 'en' and isinstance(q.get('en'), dict) else {}
            title = translated.get('titel', q['titel'])
            if lang == 'en' and q['titel'].startswith('[') and not translated.get('titel'):
                title = langs[lang]['stimmen.kategorie.' + q['kategorie']] + ' · ' + translated.get('medium', q['medium'])
            title = title.replace('[', '').replace(']', '')
            record(append, base, [title, translated.get('medium', q['medium'])], lang, 'source-header:' + lang, f'/{qi}/titel')
        scan = source_scans.get(q['id'], {})
        for lang in ('de', 'en'):
            if scan.get('pages'):
                record(append, {**base, 'metadata': {**base['metadata'], 'input_file': 'data/quellen-scans.json'}},
                       [langs[lang]['stimmen.seite'], scan['pages']], lang, 'scan-pages:' + lang, '/' + q['id'] + '/pages')
            if q.get('stufe') != 'weitere':
                for i, excerpt in enumerate(source_excerpts.get(q['id'], [])):
                    for field in ('caption', 'source'):
                        if excerpt.get(field, {}).get(lang):
                            append({**base, 'metadata': {**base['metadata'], 'input_file': 'data/quellen-auszuege.json'}},
                                   excerpt[field][lang], lang, 'summary', 'editorial', 'facsimile-' + field + ':' + lang,
                                   f'/{q["id"]}/{i}/{field}/{lang}', original=True)
        if q.get('stufe') == 'weitere':
            continue  # Its stored summaries/quotes are not rendered publicly.
        for field in ('kurz', 'inhalt', 'korrektur'):
            values = q.get(field) or {}
            if not isinstance(values, dict):
                if values: raise ValueError('unexpected_source_shape')
                continue
            for lang in ('de', 'en'):
                value = values.get(lang)
                if not value: continue
                for i, text in enumerate(value if isinstance(value, list) else [value]):
                    loc = f'/{qi}/{field}/{lang}' + (f'/{i}' if isinstance(value, list) else '')
                    append(base, text, lang, 'summary', 'editorial', field + ':' + lang, loc)
        for bi, b in enumerate(q.get('beleg') or []):
            for field in ('original', 'de', 'en'):
                if not b.get(field): continue
                append(base, b[field], q['sprache'] if field == 'original' else field,
                       'original' if field == 'original' else 'translation', voice,
                       f'beleg-{bi}:' + field, f'/{qi}/beleg/{bi}/{field}', original=True)
        for zi, z in enumerate(q.get('zitate') or []):
            if any(z['text'].strip(' .') == b['original'].strip(' .') for b in q.get('beleg') or []):
                continue
            append(base, z['text'], q['sprache'], 'original', voice, 'zitate:original', f'/{qi}/zitate/{zi}/text', original=True)
            for lang, field in [('de', 'kontext'), ('en', 'kontext_en')]:
                if z.get(field): append(base, z[field], lang, 'summary', 'editorial', 'quote-caption:' + lang, f'/{qi}/zitate/{zi}/{field}')
    column_files = website.json('data/kolumnen.json')['dateien']
    for filename in column_files:
        if Path(filename).name != filename or not filename.endswith('.md'):
            raise ValueError('invalid_column_path')
        path = 'research/columns/' + filename
        meta, art, text = column_text(website.read(path).decode(), filename)
        slug = filename[:-3].replace('_', '-')
        did = 'private/document/column/' + slug
        voice = 'leven' if meta.get('autor') == 'Jackie Leven' else 'editorial'
        issue = art == 'deep-pool' or bool(re.search(r'-(june|aug)-08\.php$', meta.get('quelle', '')))
        publication = '2008' if re.search(r'-(june|aug)-08\.php$', meta.get('quelle', '')) else meta.get('datum')
        base = {'document_id': did, 'title': meta.get('titel', slug), 'source_voice': voice,
                'year': year(publication) if issue else None,
                'url_de': '/de/' + langs['de']['pfad.pool'] + '/' + slug,
                'url_en': '/en/' + langs['en']['pfad.pool'] + '/' + slug,
                'metadata': {'section': 'writing', 'fiction': False, 'record_kind': 'column', 'display_date': meta.get('datum'), 'identity_scope': 'private_search', 'input_file': path, 'source_revision': website.revision,
                             'source_url': meta.get('quelle'), 'archive_url': meta.get('archiv'), 'author': meta.get('autor'),
                             'date_kind': 'issue' if issue else 'capture', 'date_label': meta.get('datum'),
                             'capture_date': meta.get('capture'), 'adapter': ADAPTER}}
        text = re.sub(r'^(-{3,})[ \t]*$', r'\n\1\n', text, flags=re.M)
        for i, block in enumerate(re.split(r'\n\s*\n', text.strip())):
            block = block.strip()
            if not block or re.fullmatch(r'-{3,}', block): continue
            lines = block.splitlines()
            verse = len(lines) > 2 and max(len(line.encode()) for line in lines) < 68
            readable = block if verse else re.sub(r'\s*\n\s*', ' ', block)
            append(base, readable, 'en', 'original', voice, 'column:en', {'block': i}, original=True)
    if not candidates or not column_files:
        raise ValueError('empty_source_snapshot')
    coverage = {'sources': len(catalog), 'source_detail_pages': sum(q.get('stufe') != 'weitere' for q in catalog),
                'catalog_only_sources': sum(q.get('stufe') == 'weitere' for q in catalog), 'columns': len(column_files)}
    for adapter in (music, timeline, biography, site_pages, live_media):
        coverage.update(adapter(website, langs, append))
    document_targets = {p['document_id']: {'url_de': p['url_de'], 'url_en': p['url_en']} for p in candidates if p['metadata'].get('identity_scope') == 'archive'}
    coverage.update(archive_records(entities, archive, document_targets, append))
    passages = state.assign(candidates)
    # Bind the rendering adapter dependencies in addition to content inputs.
    for path in ('internal/site/markdown.go', 'internal/site/templates.go', 'templates/quelle.gohtml', 'templates/kolumne.gohtml'):
        website.read(path)
    for path in ('templates/platte.gohtml', 'templates/diskografie.gohtml', 'templates/buehne.gohtml', 'templates/kapitel.gohtml',
                 'templates/hoeren.gohtml', 'templates/livevideos.gohtml', 'templates/start.gohtml', 'templates/mitmachen.gohtml', 'templates/stimmen.gohtml'):
        website.read(path)
    if any(p['metadata'].get('section') not in SECTIONS for p in passages):
        raise ValueError('invalid_section')
    coverage['sections'] = {section: {'passages': sum(p['metadata']['section'] == section for p in passages),
                                     'documents': len({p['document_id'] for p in passages if p['metadata']['section'] == section})}
                            for section in sorted(SECTIONS)}
    coverage['fiction_passages'] = sum(p['metadata'].get('fiction') is True for p in passages)
    coverage['source_policy'] = 'Explicit published adapters only; no private research notes, binary OCR, unrendered source details or disabled fan videos.'
    inputs = {'website': {'commit': website.revision, 'files': dict(sorted(website.files.items()))},
              'archive': {'commit': archive.revision, 'files': dict(sorted(archive.files.items()))}}
    result = {'format_version': 'search-export-v1', 'adapter': ADAPTER, 'inputs': inputs,
              'entities': entities, 'passages': passages, 'document_count': len(documents), 'coverage': coverage}
    result['data_version'] = sha(canonical(result))
    return result
