"""Check the published holding page, redirects, assets and private paths."""
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

ORIGIN = 'https://jackieleven.com'
USER_AGENT = 'JackieLevenDeploymentCheck/1.0'

def fetch(path):
    request = Request(ORIGIN + path, headers={'User-Agent': USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.status, response.headers, response.read()

status, headers, body = fetch('/')
assert status == 200
assert b'An independent tribute is taking shape here.' in body
assert b'<html lang="en">' in body
assert b'lang="de"' not in body
assert 'noindex' in headers.get('X-Robots-Tag', '')
print('OK: English holding page over verified HTTPS')

for path in ['/assets/fonts/newsreader-normal.woff2', '/assets/fonts/space-grotesk-normal.woff2']:
    status, _, body = fetch(path)
    assert status == 200 and body.startswith(b'wOF2'), path
    print('OK: ' + path)

status, _, body = fetch('/robots.txt')
assert status == 200 and b'Disallow: /' in body
print('OK: temporary search-engine exclusion')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

opener = build_opener(NoRedirect)
opener.addheaders = [('User-Agent', USER_AGENT)]
for origin in ['http://jackieleven.com', 'http://www.jackieleven.com', 'https://www.jackieleven.com']:
    try:
        opener.open(origin + '/?check=redirect', timeout=20)
        raise AssertionError('Missing redirect: ' + origin)
    except HTTPError as error:
        assert error.code in (301, 308), (origin, error.code)
        assert error.headers['Location'] == ORIGIN + '/?check=redirect', origin
    print('OK: redirect from ' + origin)

for path in ['/.git/config', '/research/README.md', '/app/bootstrap.php', '/index.php', '/autobiografie/00-rahmen.md']:
    try:
        fetch(path)
        raise AssertionError('Unexpected public file: ' + path)
    except HTTPError as error:
        assert error.code in (403, 404), (path, error.code)
    print('OK: not exposed ' + path)
