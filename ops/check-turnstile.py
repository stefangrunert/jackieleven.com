"""Bounded live negative checks: deliberately invalid bot proofs, no valid submission."""
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener
import re
import time

client = build_opener(HTTPCookieProcessor(CookieJar()))


def request(path, data=None):
    req = Request('https://jackieleven.com' + path, data=data,
                  headers={'User-Agent': 'JackieLevenDeploymentCheck/1.0'})
    try:
        response = client.open(req, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        return response.code, response.headers, response.read().decode()


for path, lang in [('/de/mitmachen', 'de'), ('/en/contribute', 'en')]:
    status, headers, html = request(path)
    assert status == 200 and 'data-language="' + lang + '"' in html
    assert 'data-action="contact"' in html and 'type="submit" disabled' not in html
    for directive in ('script-src', 'frame-src'):
        policy = next(p.strip() for p in headers['Content-Security-Policy'].split(';') if p.strip().startswith(directive + ' '))
        assert 'https://challenges.cloudflare.com' in policy
    token = re.search(r'name="token" value="([a-f0-9]+)"', html).group(1)
    time.sleep(2.1)  # Respect the form's minimum reading time.
    message = 'Turnstile rejection check: this must not be delivered.'
    data = {'name': 'Security check', 'email': 'turnstile-check@example.invalid',
            'nachricht': message, 'token': token}
    if lang == 'en':
        data['cf-turnstile-response'] = 'deliberately-invalid-proof'
    status, _, html = request(path, urlencode(data).encode())
    assert status == 422, (path, status)
    assert message in html, 'Message was lost on verification failure'
    assert ('Sicherheitsprüfung konnte nicht bestätigt' if lang == 'de' else 'security check could not be confirmed') in html
    print('OK: ' + lang + ' rejects missing/invalid Turnstile proof and preserves text', flush=True)
