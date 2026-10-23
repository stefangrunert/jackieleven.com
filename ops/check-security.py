"""Bounded live hardening checks. Invalid-token POSTs cannot send email.

Run after other smoke tests: this deliberately exercises the per-client contact
limit, then waits for that limit to admit another invalid request again.
"""
import argparse
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ORIGIN = 'https://jackieleven.com'
UA = 'JackieLevenDeploymentCheck/1.0'


def fetch(path, data=None):
    request = Request(ORIGIN + path, data=data, headers={'User-Agent': UA})
    try:
        response = urlopen(request, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        return response.code, response.headers, response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin-ip', required=True, help='Origin IP already owned by this deployment')
    args = parser.parse_args()
    for path in ['/en/', '/en/contribute', '/security-check-missing-page']:
        status, headers, _ = fetch(path)
        assert status == (404 if path.endswith('missing-page') else 200), (path, status)
        csp = headers.get('Content-Security-Policy', '')
        for policy in ["default-src 'self'", "object-src 'none'", "base-uri 'none'", "frame-ancestors 'none'", "form-action 'self'", 'https://www.youtube-nocookie.com']:
            assert policy in csp, (path, policy)
        script_policy = next(part.strip() for part in csp.split(';') if part.strip().startswith('script-src '))
        assert "'unsafe-inline'" not in script_policy and "'unsafe-eval'" not in script_policy
        assert headers.get('X-Frame-Options') == 'DENY'
        assert headers.get('X-Content-Type-Options') == 'nosniff'
        assert 'camera=()' in headers.get('Permissions-Policy', '')
        assert 'max-age=' in headers.get('Strict-Transport-Security', '')
        if path.endswith('contribute'):
            cookie = headers.get('Set-Cookie', '').lower()
            assert all(flag in cookie for flag in ['secure', 'httponly', 'samesite=lax'])
            assert 'no-store' in headers.get('Cache-Control', '')
    print('OK: security headers on pages, contact and 404; secure uncached contact session', flush=True)

    for scheme, port in [('http', 80), ('https', 443)]:
        for host in ['jackieleven.com', 'www.jackieleven.com']:
            code = subprocess.check_output([
                'curl', '--silent', '--show-error', '--max-time', '15',
                '--noproxy', '*', '--resolve', f'{host}:{port}:{args.origin_ip}',
                '-H', 'CF-Connecting-IP: 127.0.0.1', '-H', 'X-Forwarded-For: 127.0.0.1',
                '-o', '/dev/null', '-w', '%{http_code}', f'{scheme}://{host}/en/',
            ], text=True)
            assert code == '403', (host, scheme, code)
    print('OK: direct origin HTTP/HTTPS denied, also with spoofed proxy headers', flush=True)

    code = subprocess.check_output([
        'curl', '--silent', '--show-error', '--max-time', '15', '--noproxy', '*',
        '--resolve', f'jackieleven.com:80:{args.origin_ip}', '-o', '/dev/null', '-w', '%{http_code}',
        'http://jackieleven.com/.well-known/acme-challenge/security-check-nonexistent',
    ], text=True)
    assert code == '404', code
    print('OK: certificate challenge location remains reachable', flush=True)

    # No token and no valid email: every POST fails before any possible mail send.
    invalid = b'token=&email=&nachricht='
    statuses = []
    for _ in range(8):
        status, _, body = fetch('/en/contribute', invalid)
        assert status in (400, 429), status
        statuses.append(status)
        if status == 429:
            assert b'<title>429 Too Many Requests</title>' in body, 'Expected rejection by nginx before PHP'
        time.sleep(0.15)
    assert 400 in statuses and 429 in statuses, statuses
    print('OK: invalid CSRF rejected; burst rejected by nginx before PHP', flush=True)
    for _ in range(18):
        time.sleep(2)
        if fetch('/en/contribute', invalid)[0] == 400:
            break
    else:
        raise AssertionError('Contact request limit did not recover')
    print('OK: contact rate limit recovers; no emails sent', flush=True)


if __name__ == '__main__':
    main()
