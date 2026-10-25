"""Read-only checks against the published site. Does not submit messages."""
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import json
import xml.etree.ElementTree as ET

ORIGIN = 'https://jackieleven.com'
USER_AGENT = 'JackieLevenDeploymentCheck/1.0'


def fetch(path):
    request = Request(ORIGIN + path, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.headers, response.read()
    except HTTPError as error:
        return error.code, error.headers, error.read()


class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.alternates = []
        self.assets = set()
        self.in_schema = False
        self.schema = ''

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'link' and values.get('rel') == 'canonical':
            self.canonical.append(values['href'])
        if tag == 'link' and values.get('rel') == 'alternate':
            self.alternates.append(values['href'])
        if tag == 'script' and values.get('type') == 'application/ld+json':
            self.in_schema = True
        for key in ('src', 'href'):
            value = values.get(key, '')
            if value.startswith('/assets/'):
                self.assets.add(value)

    def handle_data(self, data):
        if self.in_schema:
            self.schema += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_schema = False


assets = set()
paths = [
    '/de/', '/en/', '/de/hoeren', '/en/listen', '/de/zeitreise', '/en/timeline',
    '/en/timeline/1977-doll-by-doll', '/de/diskografie', '/en/discography/1975-control',
    '/de/biografie', '/en/biography', '/en/voices', '/de/stimmen?auswahl=2',
    '/en/voices/1978-06-zigzag-doll-by-doll-acne-club-aylesbury',
    '/en/deep-pool/2002-10-deep-pool-oktober-2002', '/de/deep-pool/2002-10-deep-pool-oktober-2002',
    '/de/ueber', '/en/about', '/de/impressum', '/en/legal-notice',
]
for path in paths:
    status, headers, body = fetch(path)
    assert status == 200, (path, status)
    assert 'noindex' not in headers.get('X-Robots-Tag', ''), path
    assert b'content="noindex' not in body and b'Fatal error' not in body and b'Warning:' not in body, path
    parser = Head()
    parser.feed(body.decode())
    assert parser.canonical == [ORIGIN + path.split('?')[0]], path
    assert len(parser.alternates) == 3 and all(url.startswith(ORIGIN) for url in parser.alternates), path
    assert json.loads(parser.schema)['@graph'][2]['url'] == parser.canonical[0], path
    assets.update(parser.assets)
    print('OK: ' + path, flush=True)

for path in ['/de/mitmachen', '/en/contribute']:
    status, headers, body = fetch(path)
    assert status == 200 and b'name="token"' in body and b'type="submit" disabled' not in body, path
    assert 'no-store' in headers.get('Cache-Control', ''), path
    cookie = headers.get('Set-Cookie', '').lower()
    assert 'secure' in cookie and 'httponly' in cookie and 'samesite=lax' in cookie, path
    print('OK: contact form ready, secure session (no message sent)', flush=True)

status, headers, body = fetch('/robots.txt')
assert status == 200 and b'Disallow: /' not in body and (ORIGIN + '/sitemap.xml').encode() in body
assert 'noindex' not in headers.get('X-Robots-Tag', '')
status, headers, body = fetch('/sitemap.xml')
assert status == 200
root = ET.fromstring(body)
urls = [item.text for item in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(urls) > 1000 and len(set(urls)) == len(urls)
assert all(url.startswith(ORIGIN + '/') and '?' not in url for url in urls)
print('OK: robots.txt and sitemap with ' + str(len(urls)) + ' URLs', flush=True)

for path in ['/en/biography/01-prinlaws-boy', '/en/timeline/1977-doll-by-doll?fragment=1']:
    status, headers, body = fetch(path)
    assert status == 200 and 'noindex' in headers.get('X-Robots-Tag', ''), path
print('OK: pastiche chapter and fragment excluded from indexing', flush=True)

for path in ['/.git/config', '/.dev/resend-api-key', '/app/config.local.php', '/app/bootstrap.php', '/research/README.md', '/autobiografie/00-rahmen.md', '/ops/prepare-go-release.py', '/data/stationen.json', '/templates/layout.gohtml', '/cmd/jackieleven/main.go', '/does-not-exist']:
    assert fetch(path)[0] in (403, 404), path
print('OK: private paths and missing pages inaccessible', flush=True)

for path in sorted(assets):
    status, _, body = fetch(path)
    assert status == 200 and body and b'<!DOCTYPE html>' not in body[:30], path
print('OK: ' + str(len(assets)) + ' local images, fonts, scripts and styles', flush=True)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


opener = build_opener(NoRedirect)
opener.addheaders = [('User-Agent', USER_AGENT)]
for origin in ['http://jackieleven.com', 'http://www.jackieleven.com', 'https://www.jackieleven.com']:
    try:
        opener.open(origin + '/en/', timeout=20)
        raise AssertionError('Missing redirect: ' + origin)
    except HTTPError as error:
        assert error.code in (301, 308) and error.headers['Location'] == ORIGIN + '/en/', origin
print('OK: HTTP/www redirect to canonical HTTPS domain', flush=True)
