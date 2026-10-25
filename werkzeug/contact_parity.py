#!/usr/bin/env python3
"""Credential-free PHP/Go contact HTTP parity; never point this at production."""
from __future__ import annotations
import argparse
from http.cookies import SimpleCookie
import http.cookiejar
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from parity import HTMLContract, NoRedirect, compact

HEADERS = ('content-type', 'content-language', 'cache-control', 'x-robots-tag', 'retry-after', 'location')
TOKEN = re.compile(r'^[a-f0-9]{48}$')


class TokenParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.token = ''
        self.sitekeys = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'input' and values.get('name') == 'token':
            self.token = values.get('value', '')
        if values.get('data-sitekey') is not None:
            self.sitekeys.append(values['data-sitekey'])


def cookie_contract(values):
    result = []
    for raw in values:
        parsed = SimpleCookie(); parsed.load(raw)
        for name, morsel in parsed.items():
            result.append({
                'name': name, 'value': '<SESSION>', 'path': morsel['path'],
                'httponly': bool(morsel['httponly']), 'secure': bool(morsel['secure']),
                'samesite': morsel['samesite'].lower(),
            })
    return sorted(result, key=lambda item: item['name'])


class Session:
    def __init__(self, base):
        self.base = base.rstrip('/')
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect(), urllib.request.HTTPCookieProcessor(self.jar))
    def cookie(self):
        return next((c.value for c in self.jar if c.name == 'jackie_contact'), '')
    def request(self, path, raw=None):
        data = raw.encode() if raw is not None else None
        headers = {'User-Agent':'JackieLeven-Contact-Parity/1.0'}
        if data is not None: headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method='POST' if data is not None else 'GET')
        try: response = self.opener.open(req, timeout=15)
        except urllib.error.HTTPError as exc: response = exc
        with response:
            body = response.read().decode('utf-8')
            headers = {k.lower():v for k,v in response.headers.items()}
            cookies = response.headers.get_all('Set-Cookie') or []
            status = response.status
        parser = HTMLContract(); parser.feed(body); parser.close()
        tokens = TokenParser(); tokens.feed(body); tokens.close()
        contract = {
            'status': status,
            'headers': {key:headers[key] for key in HEADERS if key in headers},
            'cookies': cookie_contract(cookies),
            'body': parser.events,
            'inline_text': parser.inline_text,
        }
        return contract, tokens.token, tokens.sitekeys


def encode(pairs):
    return urllib.parse.urlencode(pairs)


def compare(reference, candidate):
    differences = []
    for key in ('status','headers','cookies','body','inline_text'):
        if reference.get(key) != candidate.get(key):
            differences.append({'field':key, 'reference':reference.get(key), 'candidate':candidate.get(key)})
    return differences


def cookie_ok(contract):
    cookies = contract['cookies']
    return len(cookies) == 1 and cookies[0] == {
        'name':'jackie_contact', 'value':'<SESSION>', 'path':'/',
        'httponly':True, 'secure':False, 'samesite':'lax',
    }


def expire_php(session_dir, cookie):
    path = session_dir / ('sess_' + cookie)
    data = path.read_text(encoding='latin-1')
    data, count = re.subn(r's:4:"zeit";i:\d+;', f's:4:"zeit";i:{int(time.time())-7201};', data)
    if count < 1: raise RuntimeError('PHP contact timestamp not found')
    path.write_text(data, encoding='latin-1')


def expire_go(state_dir, cookie, token):
    path = state_dir / 'sessions' / (cookie + '.json')
    data = json.loads(path.read_text())
    data['forms'][token]['created'] = int(time.time()) - 7201
    path.write_text(json.dumps(data, separators=(',',':')))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--php', required=True, help='Isolated credential-free PHP base URL')
    ap.add_argument('--go', required=True, help='Isolated credential-free Go base URL')
    ap.add_argument('--php-session-dir', type=Path, required=True)
    ap.add_argument('--go-state-dir', type=Path, required=True)
    ap.add_argument('--report', type=Path, default=Path('/tmp/jackie-contact-http-parity.json'))
    args = ap.parse_args()
    cases, guard_failures = [], []

    def pair(): return Session(args.php), Session(args.go)
    def record(name, php_result, go_result, expected_status=None, checks=None):
        diffs = compare(php_result, go_result)
        checks = checks or []
        if expected_status is not None:
            checks += [
                {'check':'php-status', 'ok':php_result['status']==expected_status, 'actual':php_result['status']},
                {'check':'go-status', 'ok':go_result['status']==expected_status, 'actual':go_result['status']},
            ]
        cases.append({'name':name, 'passed':not diffs and all(c['ok'] for c in checks), 'differences':diffs, 'checks':checks})

    # Guard first: rendered public config must be empty on both isolated servers.
    for lang, path in [('de','/de/mitmachen'),('en','/en/contribute')]:
        p, g = pair(); pr, pt, ps = p.request(path); gr, gt, gs = g.request(path)
        safe = not ps and not gs
        if not safe: guard_failures.append(f'{lang}: public sitekey present; POST suite aborted')
        record('get-'+lang, pr, gr, 200, [
            {'check':'php-token-48hex','ok':bool(TOKEN.fullmatch(pt))},
            {'check':'go-token-48hex','ok':bool(TOKEN.fullmatch(gt))},
            {'check':'php-cookie-contract','ok':cookie_ok(pr)},
            {'check':'go-cookie-contract','ok':cookie_ok(gr)},
            {'check':'empty-public-sitekey','ok':safe},
        ])
    if guard_failures:
        report = {'php_reference_contact_used':False, 'guard_failures':guard_failures, 'cases':cases, 'failures':sum(not c['passed'] for c in cases)}
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print('POST suite aborted:', *guard_failures, file=sys.stderr)
        return 1

    valid = [('name','Test'),('email','test@example.test'),('nachricht','Test message')]

    # Invalid/missing/array CSRF never reaches timing, validation, verification or send.
    for name, prepare in [
        ('missing-token', lambda _t: valid),
        ('invalid-token', lambda _t: [('token','f'*48),*valid]),
        ('array-token', lambda t: [('token[]',t),*valid]),
    ]:
        p,g = pair(); _,pt,_=p.request('/de/mitmachen'); _,gt,_=g.request('/de/mitmachen')
        pr,_,_=p.request('/de/mitmachen',encode(prepare(pt))); gr,_,_=g.request('/de/mitmachen',encode(prepare(gt)))
        record(name,pr,gr,400)

    # A valid fresh token must hit the <2 second guard with Retry-After 60.
    p,g=pair(); _,pt,_=p.request('/de/mitmachen'); _,gt,_=g.request('/de/mitmachen')
    pr,prt,_=p.request('/de/mitmachen',encode([('token',pt),*valid])); gr,grt,_=g.request('/de/mitmachen',encode([('token',gt),*valid]))
    record('too-fast',pr,gr,429,[
        {'check':'php-token-retained','ok':prt==pt}, {'check':'go-token-retained','ok':grt==gt},
        {'check':'php-retry-after-60','ok':pr['headers'].get('retry-after')=='60'}, {'check':'go-retry-after-60','ok':gr['headers'].get('retry-after')=='60'},
    ])

    # Prepare all mature-token scenarios before one bounded wait.
    mature_specs = [
        ('honeypot-scalar','/de/mitmachen',lambda t:[('token',t),('website','spam'),*valid],429),
        ('honeypot-array','/de/mitmachen',lambda t:[('token',t),('website[]','spam'),*valid],429),
        ('honeypot-map','/de/mitmachen',lambda t:[('token',t),('website[x]','spam'),*valid],429),
        ('honeypot-empty-array','/de/mitmachen',lambda t:[('token',t),('website[]',''),*valid],429),
        ('validation-escaped-de','/de/mitmachen',lambda t:[('token',t),('name','<b>O\'Reilly</b>'),('email','bad"<@example'),('nachricht','<script>alert(1)</script> & "x"')],422),
        ('validation-array-fields','/de/mitmachen',lambda t:[('token',t),('email[]','x'),('nachricht[]','x')],422),
        ('empty-config-de','/de/mitmachen',lambda t:[('token',t),*valid],503),
        ('empty-config-en','/en/contribute',lambda t:[('token',t),*valid],503),
    ]
    prepared=[]
    for name,path,build,status in mature_specs:
        p,g=pair(); _,pt,_=p.request(path); _,gt,_=g.request(path)
        prepared.append((name,path,build,status,p,g,pt,gt))
    time.sleep(2.2)
    for name,path,build,status,p,g,pt,gt in prepared:
        pr,prt,_=p.request(path,encode(build(pt))); gr,grt,_=g.request(path,encode(build(gt)))
        checks=[{'check':'php-token-retained','ok':prt==pt},{'check':'go-token-retained','ok':grt==gt}]
        if status==429:
            checks += [{'check':'php-retry-after-60','ok':pr['headers'].get('retry-after')=='60'},{'check':'go-retry-after-60','ok':gr['headers'].get('retry-after')=='60'}]
        record(name,pr,gr,status,checks)

    # Expiry is induced only in the isolated state files; no long sleep required.
    p,g=pair(); _,pt,_=p.request('/de/mitmachen'); _,gt,_=g.request('/de/mitmachen')
    expire_php(args.php_session_dir,p.cookie()); expire_go(args.go_state_dir,g.cookie(),gt)
    pr,_,_=p.request('/de/mitmachen',encode([('token',pt),*valid])); gr,_,_=g.request('/de/mitmachen',encode([('token',gt),*valid]))
    record('expired-token',pr,gr,400)

    failures = sum(not case['passed'] for case in cases)
    report = {
        'php':args.php, 'go':args.go, 'php_reference_contact_used':False,
        'credentials':{'resend_key':'empty','turnstile_sitekey':'empty','turnstile_secret':'empty'},
        'external_verification_or_send_reachable':False,
        'cases':cases, 'case_count':len(cases), 'failures':failures,
    }
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for case in cases: print(('PASS' if case['passed'] else 'FAIL'),case['name'])
    print(f'Report: {args.report}; {failures} failures')
    return 1 if failures else 0


if __name__ == '__main__': sys.exit(main())
