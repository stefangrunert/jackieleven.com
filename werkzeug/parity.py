#!/usr/bin/env python3
"""Independent HTTP contract comparison; stdlib only. See parity.md."""
from __future__ import annotations
import argparse
import concurrent.futures
import difflib
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
HEADERS = ('content-type', 'content-language', 'location', 'link', 'x-robots-tag', 'vary', 'retry-after')
HTML_SPACE = re.compile(r'[ \t\r\n\f]+')
BLOCK = set('address article aside blockquote body dd details dialog div dl dt fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup html li main menu nav ol p pre search section table tbody td tfoot th thead tr ul'.split())
FLOW_BREAK = {'br', 'hr'}
JSON_DATA_ATTRIBUTES = {'data-alternativen', 'data-seo'}
SAFE_STATUS_PATHS = {'/de%2Fueber'}
LEAK_MARKERS = ('/users/stefan', 'jackie_resend_', 'turnstile_secret', 'traceback', 'panic:', 'runtime error:')

def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def asset_url(value):
    if value.startswith('/assets/'):
        url = urllib.parse.urlsplit(value)
        args = [(k, v) for k, v in urllib.parse.parse_qsl(url.query, keep_blank_values=True) if k != 'v']
        return urllib.parse.urlunsplit(('', '', url.path, urllib.parse.urlencode(args), url.fragment))
    return value

class HTMLContract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events, self.links, self.assets, self.inline_text = [], set(), set(), []
        self.raw = None
        self.raw_text = []
        self.flow = []
    def flow_break(self):
        if not self.flow: return
        current = self.flow[-1]
        if current['text']:
            current['segments'].append(current['text'])
        current['text'], current['space'] = '', False
    def flow_open(self, tag):
        self.flow_break()
        self.flow.append({'tag':tag, 'segments':[], 'text':'', 'space':False})
    def flow_close(self, tag):
        if not self.flow or self.flow[-1]['tag'] != tag: return
        self.flow_break()
        current = self.flow.pop()
        if current['segments']:
            self.inline_text.append([tag, current['segments']])
        self.flow_break()
    def flow_text(self, data):
        if not self.flow: return
        collapsed = HTML_SPACE.sub(' ', data)
        core = collapsed.strip(' ')
        current = self.flow[-1]
        if not core:
            if current['text'] and ' ' in collapsed: current['space'] = True
            return
        if current['text'] and (current['space'] or collapsed.startswith(' ')):
            current['text'] += ' '
        current['text'] += core
        current['space'] = collapsed.endswith(' ')
    def handle_decl(self, decl):
        self.events.append(['declaration', decl.lower()])
    def handle_starttag(self, tag, attrs):
        if tag in BLOCK:
            self.flow_open(tag)
        elif tag in FLOW_BREAK:
            self.flow_break()
        values = dict(attrs)
        for key, value in attrs:
            if key in ('href', 'src') and value:
                if value.startswith('/assets/'):
                    self.assets.add(asset_url(value))
                if key == 'href': self.links.add(value)
        normalized = []
        for key, value in attrs:
            if key == 'value' and tag == 'input' and values.get('name') == 'token':
                value = '<CONTACT-CSRF>'
            if value is not None and key in ('src', 'href'): value = asset_url(value)
            normalized.append([key, value])
        self.events.append(['open', tag, sorted(normalized, key=lambda a: a[0])])
        if tag in ('script', 'style', 'pre', 'textarea'):
            self.raw = (tag, values.get('type', ''))
            self.raw_text = []
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if self.raw and self.raw[0] == tag:
            text = ''.join(self.raw_text)
            if tag == 'script' and self.raw[1] == 'application/ld+json':
                try: self.events.append(['jsonld', json.loads(text)])
                except ValueError: self.events.append(['invalid-jsonld', text])
            else:
                self.events.append(['raw', text])
            self.raw = None
        if tag not in VOID: self.events.append(['close', tag])
        if tag in BLOCK: self.flow_close(tag)
    def handle_data(self, data):
        if self.raw:
            self.raw_text.append(data)
        else:
            self.flow_text(data)
            # HTML collapses only ASCII space characters. NBSP and other
            # typographic spacing are rendered content and must stay distinct.
            text = HTML_SPACE.sub(' ', data).strip(' ')
            if text: self.events.append(['text', text])
    def handle_comment(self, data):
        pass  # comments are not rendered behavior

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

class Client:
    def __init__(self, base, insecure=False):
        self.base = base.rstrip('/')
        context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), urllib.request.HTTPSHandler(context=context))
    def fetch(self, case):
        headers = {'User-Agent': 'JackieLeven-Parity/1.0', **case.get('headers', {})}
        req = urllib.request.Request(self.base + case['path'], headers=headers, method=case.get('method', 'GET'))
        try:
            response = self.opener.open(req, timeout=45)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            headers = {k.lower(): v for k, v in response.headers.items()}
            result = {'status': response.status, 'headers': {k: headers[k] for k in HEADERS if k in headers}}
        content_type = headers.get('content-type', '').lower()
        if 'content-type' in result['headers']:
            result['headers']['content-type'] = re.sub(r';\s*', '; ', content_type)
        if case.get('method') == 'HEAD':
            result['body'] = ['empty', len(body)]
        elif 'text/html' in content_type:
            parser = HTMLContract()
            parser.feed(body.decode('utf-8'))
            result['body'] = parser.events
            result['inline_text'] = parser.inline_text
            result['assets'] = sorted(parser.assets)
            result['links'] = sorted(parser.links)
        elif 'xml' in content_type:
            def tree(node):
                return [node.tag, [list(pair) for pair in sorted(node.attrib.items())], (node.text or '').strip(), [tree(c) for c in node]]
            result['body'] = tree(ET.fromstring(body))
        elif content_type.startswith('text/'):
            result['body'] = body.decode('utf-8').replace('\r\n', '\n')
        else:
            result['body'] = ['sha256', hashlib.sha256(body).hexdigest(), len(body)]
        return result

def case_id(case):
    return hashlib.sha256(compact(case).encode()).hexdigest()

def saved_path(folder, case): return folder / (case_id(case) + '.json.gz')

def save_result(folder, case, result):
    folder.mkdir(parents=True, exist_ok=True)
    with gzip.open(saved_path(folder, case), 'wt', encoding='utf-8') as f:
        json.dump({'case': case, 'result': result}, f, ensure_ascii=False)

def load_result(folder, case):
    with gzip.open(saved_path(folder, case), 'rt', encoding='utf-8') as f: return json.load(f)['result']

def corpus(client):
    cases = []
    def add(path, **extra):
        c = {'path': path, **extra}
        if c not in cases: cases.append(c)
    sitemap = client.fetch({'path': '/sitemap.xml'})
    def locate(node):
        if node[0].endswith('}loc'): yield urllib.parse.urlsplit(node[2]).path
        for child in node[3]: yield from locate(child)
    paths = list(locate(sitemap['body']))
    for path in paths: add(path)
    add('/sitemap.xml'); add('/robots.txt')
    for lang, biography in [('de', 'biografie'), ('en', 'biography')]:
        bio = client.fetch({'path': f'/{lang}/{biography}'})
        for path in bio['links']:
            if path.startswith(f'/{lang}/{biography}/'): add(path)
    for path in paths:
        if '/zeitreise/' in path or '/timeline/' in path: add(path + '?fragment=1')
    station_paths = [p for p in paths if '/zeitreise/' in p or '/timeline/' in p]
    for path in station_paths[:2]:
        for query in ['fragment=0', 'fragment=01', 'fragment=', 'fragment=1&fragment=0', 'fragment[]=1']:
            add(path + '?' + query)
    for language in ['', 'en', 'en-GB,en;q=0.9,de;q=0.8', 'fr-CA,fr;q=0.9,en;q=0.5', 'de;q=0,en;q=0', 'en;q=0,de;q=0.5', '*', 'EN-us;q=0.9, de;q=0.9']:
        add('/', headers={'Accept-Language': language})
        add('/missing-page', headers={'Accept-Language': language})
    for path in ['/de', '/en', '/fr/', '/index.php', '/zeitreise', '/biografie', '/ueber', '/station/1983-der-ueberfall', '/station/missing', '/de/zeitreise/1983-der-ueberfall', '/en/timeline/1983-der-ueberfall', '/de/deep-pool', '/en/deep-pool', '/de/deep-pool/archive', '/en/deep-pool/archiv', '/de/diskografie/1973-control', '/en/discography/1973-control?projekt=john-st-field&format=alben&von=1975-control', '/de/stimmen/missing', '/de/biografie/missing', '/de/zeitreise/missing?fragment=1', '/de/ueber/extra', '/de//ueber', '/de/ueber/', '/de/%75eber', '/de/ueber?unrelated=1']:
        add(path)
    for path in ['/de/timeline/1983-caledonian-road', '/en/zeitreise/1983-caledonian-road', '/de/biography/prinlaws-boy', '/en/biografie/prinlaws-boy', '//de///ueber//', '/de%2Fueber']:
        add(path)
    for method in ['OPTIONS', 'PUT', 'PATCH', 'DELETE']:
        add('/de/ueber', method=method)
        add('/missing-page', method=method)
    pairs = [('zeitreise','timeline'), ('biografie','biography'), ('ueber','about'), ('diskografie','discography'), ('stimmen','voices'), ('hoeren','listen'), ('mitmachen','contribute'), ('impressum','legal-notice')]
    for de, en in pairs:
        add('/de/'+en); add('/en/'+de)
        add('/de/'+de, method='HEAD')
    filters = ['auswahl=0', 'auswahl=1', 'auswahl=2', 'auswahl=3', 'auswahl[]=1', 'sprache=en', 'sprache=no', 'sprache=de', 'sprache=andere', 'art=interviews', 'art=portraets', 'art=rezensionen', 'art=konzertberichte', 'art=nachrufe', 'art=erinnerungen', 'art=radio-tv', 'art=foren', 'art=buecher', 'art=nachschlagewerke', 'art=meldungen', 'zugang=frei', 'zugang=online', 'zugang=archiv', 'zugang=abo', 'zugang=verloren', 'auswahl=0&sprache=no&art=interviews&zugang=archiv', 'auswahl=2&sprache=en&art=rezensionen&zugang=online', 'art[]=interviews&sprache[]=en&zugang[]=frei', 'art=%3Cscript%3E&sprache=invalid&zugang=invalid', 'auswahl=1&auswahl=0']
    for lang, stem in [('de','stimmen'),('en','voices')]:
        for query in filters: add(f'/{lang}/{stem}?{query}')
    discs = [p for p in paths if '/diskografie/' in p or '/discography/' in p]
    for path in discs[:6]:
        for query in ['projekt=john-st-field&format=alben&von=1975-control', 'projekt=doll-by-doll&format=kleine', 'format=reissue', 'projekt[]=jackie-leven&format[]=alben&von[]=1975-control', 'projekt=invalid&format=invalid&von=missing', 'von=1975-control&format=alben&projekt=jackie-leven']:
            add(path+'?'+query)
    # POST is intentionally excluded: isolated contact harness/package mocks own that contract.
    return cases

def semantic_html_body(value):
    if not isinstance(value, list): return value
    result = []
    for event in value:
        if not (isinstance(event, list) and len(event) == 3 and event[0] == 'open'):
            result.append(event)
            continue
        attrs = []
        for key, attr_value in event[2]:
            if key in JSON_DATA_ATTRIBUTES and isinstance(attr_value, str):
                try: attr_value = ['<JSON>', json.loads(attr_value)]
                except ValueError: pass
            attrs.append([key, attr_value])
        result.append([event[0], event[1], attrs])
    return result

def infrastructure_check(expected, actual, case):
    if not case or case.get('path') not in SAFE_STATUS_PATHS: return None
    rendered = compact(actual).lower()
    found = [marker for marker in LEAK_MARKERS if marker in rendered]
    return {
        'case': case,
        'contract': 'safe-status-no-leak',
        'reference_status': expected.get('status'),
        'candidate_status': actual.get('status'),
        'no_leak': not found,
        'body_parity_compared': False,
        'note': 'Reference body is generated by Apache before the PHP application; app-body parity is intentionally not claimed.',
    }

def diff_result(expected, actual, case=None):
    result = []
    if case and case.get('path') in SAFE_STATUS_PATHS:
        if expected.get('status') != actual.get('status'):
            result.append({'field':'status','reference':expected.get('status'),'candidate':actual.get('status')})
        rendered = compact(actual).lower()
        found = [marker for marker in LEAK_MARKERS if marker in rendered]
        if found: result.append({'field':'body-leak','markers':found})
        return result
    # Baseline v1 did not retain boundary whitespace. It stays readable for
    # diagnostics, while final parity must use a v2 baseline with inline_text.
    keys = ['status','headers','body']
    if 'inline_text' in expected: keys.append('inline_text')
    for key in keys:
        if expected.get(key) != actual.get(key):
            left, right = expected.get(key), actual.get(key)
            if key in ('body', 'inline_text'):
                if key == 'body':
                    left, right = semantic_html_body(left), semantic_html_body(right)
                if left == right: continue
                left = [compact(x) for x in left] if isinstance(left,list) else str(left).splitlines()
                right = [compact(x) for x in right] if isinstance(right,list) else str(right).splitlines()
                result.append({'field':key, 'diff':list(difflib.unified_diff(left,right,fromfile='PHP',tofile='Go',n=2))[:100]})
            else: result.append({'field':key,'reference':left,'candidate':right})
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference', default='https://jackieleven.localhost')
    ap.add_argument('--candidate')
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--report', type=Path, default=Path('/tmp/jackie-parity-report.json'))
    ap.add_argument('--insecure', action='store_true', help='Accept local development TLS certificates')
    ap.add_argument('--refresh', action='store_true', help='Rebuild baseline; use only for an intentional new PHP revision')
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--match', default='', help='Only paths containing this string (baseline discovery remains complete)')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--assets', action='store_true', help='Also compare referenced CSS and JavaScript byte hashes')
    args = ap.parse_args()
    reference = Client(args.reference,args.insecure)
    manifest = args.baseline/'manifest.json'
    if manifest.exists() and not args.refresh:
        cases = json.loads(manifest.read_text())['cases']
    else:
        cases = corpus(reference)
        args.baseline.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps({'contract_version':2,'reference':args.reference,'created':time.time(),'cases':cases},ensure_ascii=False,indent=2)+'\n')
    cases = [c for c in cases if args.match in c['path']]
    if args.limit: cases=cases[:args.limit]
    candidate = Client(args.candidate,args.insecure) if args.candidate else None
    def check(case):
        try:
            if args.refresh or not saved_path(args.baseline,case).exists(): save_result(args.baseline,case,reference.fetch(case))
            expected = load_result(args.baseline,case)
            if candidate:
                actual = candidate.fetch(case)
                diffs = diff_result(expected,actual,case)
                return case, diffs, expected.get('assets',[]), infrastructure_check(expected,actual,case)
            return case, [], expected.get('assets',[]), None
        except Exception as exc: return case, [{'field':'error','error':str(exc)}], [], None
    failures, assets, infrastructure_checks = [], set(), []
    start=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for count,(case,diffs,refs,infrastructure) in enumerate(pool.map(check,cases),1):
            assets.update(refs)
            if infrastructure: infrastructure_checks.append(infrastructure)
            if diffs: failures.append({'case':case,'differences':diffs})
            if count%100==0 or count==len(cases): print(f'{count}/{len(cases)} pages; {len(failures)} mismatches/errors; {time.monotonic()-start:.1f}s',flush=True)
    asset_cases=[]
    if args.assets:
        asset_cases=[{'path':a} for a in sorted(assets) if urllib.parse.urlsplit(a).path.endswith(('.css','.js'))]
        for case in asset_cases:
            c,diffs,_,_=check(case)
            if diffs: failures.append({'case':c,'differences':diffs})
    report={'reference':args.reference,'candidate':args.candidate,'baseline':str(args.baseline),'cases':len(cases),'assets':len(asset_cases),'failures':failures,'infrastructure_checks':infrastructure_checks,'duration_seconds':round(time.monotonic()-start,2)}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'Report: {args.report}; {len(failures)} failures',flush=True)
    return 1 if failures else 0

if __name__=='__main__': sys.exit(main())
