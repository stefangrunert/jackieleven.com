#!/usr/bin/env python3
"""Check exported readable text against a separately running local website."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import urlopen


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.skip += 1
        if tag in ('br', 'p', 'div', 'section', 'h1', 'h2', 'li'): self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.skip -= 1
        if tag in ('p', 'div', 'section', 'h1', 'h2', 'li'): self.parts.append(' ')
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:18089')
    args = parser.parse_args()
    base = urlparse(args.base_url)
    if base.scheme != 'http' or base.hostname not in ('127.0.0.1', 'localhost', '::1') or base.username or base.password:
        parser.error('Only a credential-free loopback HTTP server is supported')
    corpus = json.loads(args.export.read_text())
    checks = []
    archive_records = 0
    for passage in corpus['passages']:
        if passage['metadata'].get('representation') == 'archive_record':
            archive_records += 1
            continue
        lang = 'en' if passage['language'] == 'en' else 'de'
        path = passage['url_' + lang]
        selector = passage['metadata'].get('source_selector', '')
        if isinstance(selector, str) and '/kurz/' in selector:
            path = '/' + lang + ('/voices' if lang == 'en' else '/stimmen') + '?auswahl=0'
        checks.append((path, passage))
    def fetch(path):
        reader = Reader()
        with urlopen(args.base_url.rstrip('/') + path, timeout=10) as response:
            reader.feed(response.read().decode())
        return path, norm(''.join(reader.parts))
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = dict(pool.map(fetch, sorted(set(path for path, _ in checks))))
    errors = []
    for path, passage in checks:
        fragments = passage['metadata'].get('display_fragments', [passage['text']])
        if any(norm(fragment) not in pages[path] for fragment in fragments):
            errors.append({'id': passage['id'], 'selector': passage['metadata'].get('source_selector')})
    print(json.dumps({'pages': len(pages), 'passages': len(checks), 'archive_records_separately_validated': archive_records, 'mismatch_count': len(errors), 'first_mismatches': errors[:20]}))
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()
