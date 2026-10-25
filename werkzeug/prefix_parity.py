#!/usr/bin/env python3
"""Compare an explicitly mounted Go preview with the immutable PHP v2 baseline.

Only mount-related differences are normalized.  Production canonical URLs and
JSON-LD are intentionally compared byte-for-structure by parity.py.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from http.cookies import SimpleCookie
import hashlib
import json
from pathlib import Path
import posixpath
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parity  # noqa: E402


MOUNTED_HTML_ATTRIBUTES = {'href', 'src', 'action', 'data-youtube-preview'}
MOUNTED_JSON_ATTRIBUTES = {'data-alternativen'}
CANONICAL_ALTERNATIVES_ATTRIBUTE = 'data-canonical-alternativen'
CONTACT_PATHS = ('/de/mitmachen', '/en/contribute')
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)", re.IGNORECASE)


def clean_prefix(value: str) -> str:
    if not value.startswith('/') or value.startswith('//'):
        raise ValueError('prefix must be a root-relative path')
    value = value.rstrip('/')
    if not value or any(part in ('', '.', '..') for part in value[1:].split('/')):
        raise ValueError('prefix must contain one or more ordinary path segments')
    return value


def mounted_url(value: str, prefix: str, context: str, violations: list[dict]) -> str:
    """Remove prefix from one candidate root URL, rejecting unmounted roots."""
    if not value.startswith('/') or value.startswith('//'):
        return value
    split = urllib.parse.urlsplit(value)
    if split.path == prefix:
        path = '/'
    elif split.path.startswith(prefix + '/'):
        path = split.path[len(prefix):]
    else:
        violations.append({'context': context, 'value': value, 'reason': 'root-relative URL is outside mount prefix'})
        return value
    return parity.asset_url(urllib.parse.urlunsplit(('', '', path, split.query, split.fragment)))


def normalize_mounted_json(value: str, prefix: str, context: str, violations: list[dict]) -> str:
    try:
        data = json.loads(value)
    except ValueError:
        return value

    def visit(item):
        if isinstance(item, str):
            return mounted_url(item, prefix, context, violations)
        if isinstance(item, list):
            return [visit(child) for child in item]
        if isinstance(item, dict):
            return {key: visit(child) for key, child in item.items()}
        return item

    return json.dumps(visit(data), ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def normalize_candidate(expected: dict, candidate: dict, prefix: str) -> tuple[dict, list[dict], bool, int]:
    """Normalize mounted fields only; return result, violations, noindex proof."""
    result = json.loads(json.dumps(candidate))
    violations: list[dict] = []
    headers = result.get('headers', {})
    noindex = headers.get('x-robots-tag') == 'noindex'
    if noindex and expected.get('headers', {}).get('x-robots-tag') != 'noindex':
        del headers['x-robots-tag']
    location = headers.get('location')
    if isinstance(location, str):
        headers['location'] = mounted_url(location, prefix, 'header:location', violations)
    canonical_alternatives = 0
    for event_index, event in enumerate(result.get('body', [])):
        # jsonld and raw script/style events are deliberately untouched.
        if not (isinstance(event, list) and len(event) == 3 and event[0] == 'open'):
            continue
        expected_event = expected.get('body', [])[event_index] if event_index < len(expected.get('body', [])) else None
        expected_attrs = dict(expected_event[2]) if isinstance(expected_event, list) and len(expected_event) == 3 and expected_event[0] == 'open' else {}
        attrs = []
        saw_canonical_alternatives = False
        for key, value in event[2]:
            context = f'html:{event[1]}[{key}]@{event_index}'
            if key == CANONICAL_ALTERNATIVES_ATTRIBUTE:
                saw_canonical_alternatives = True
                canonical_alternatives += 1
                reference = expected_attrs.get('data-alternativen')
                try:
                    equal = isinstance(value, str) and isinstance(reference, str) and json.loads(value) == json.loads(reference)
                except ValueError:
                    equal = False
                if not equal:
                    violations.append({'context': context, 'value': value, 'reason': 'canonical alternatives differ from immutable production alternatives'})
                # Prefix-only runtime support field: verified above, then removed
                # so the underlying production DOM contract can be compared.
                continue
            if isinstance(value, str) and key in MOUNTED_HTML_ATTRIBUTES:
                value = mounted_url(value, prefix, context, violations)
            elif isinstance(value, str) and key in MOUNTED_JSON_ATTRIBUTES:
                value = normalize_mounted_json(value, prefix, context, violations)
            attrs.append([key, value])
        event[2] = attrs
        if 'data-alternativen' in expected_attrs and not saw_canonical_alternatives:
            violations.append({'context': f'html:{event[1]}@{event_index}', 'reason': 'mounted alternatives lack immutable canonical alternatives'})
    return result, violations, noindex, canonical_alternatives


def normalize_css(css: str, stylesheet: str, prefix: str = '', candidate: bool = False) -> tuple[str, list[dict], list[dict]]:
    violations: list[dict] = []
    forms: list[dict] = []
    mounted_stylesheet = prefix + stylesheet if candidate else stylesheet

    def replace(match):
        value = match.group(2).strip()
        if value.startswith(('data:', '#', '//')) or urllib.parse.urlsplit(value).scheme:
            logical = value
            form = 'external-or-data'
        elif value.startswith('/'):
            form = 'root-relative'
            logical = mounted_url(value, prefix, f'css:{stylesheet}', violations) if candidate else parity.asset_url(value)
        else:
            form = 'relative'
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(mounted_stylesheet), urllib.parse.urlsplit(value).path))
            split = urllib.parse.urlsplit(value)
            resolved = urllib.parse.urlunsplit(('', '', resolved, split.query, split.fragment))
            logical = mounted_url(resolved, prefix, f'css:{stylesheet}', violations) if candidate else parity.asset_url(resolved)
        forms.append({'source': value, 'logical': logical, 'form': form})
        return 'url(<MOUNTED:' + logical + '>)'

    return CSS_URL.sub(replace, css), violations, forms


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalized_preview_headers(expected: dict, actual: dict) -> tuple[dict, bool]:
    result = json.loads(json.dumps(actual))
    headers = result.get('headers', {})
    noindex = headers.get('x-robots-tag') == 'noindex'
    if noindex and expected.get('headers', {}).get('x-robots-tag') != 'noindex':
        del headers['x-robots-tag']
    return result, noindex


def raw_asset(client: parity.Client, case: dict) -> bytes:
    request = urllib.request.Request(client.base + case['path'], headers={'User-Agent': 'JackieLeven-Prefix-Parity/1.0'})
    try:
        response = client.opener.open(request, timeout=45)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.read()


def normalize_known_mount_javascript(path: str, value: str) -> tuple[str, list[str]]:
    """Reverse the two exact prefix-support edits; permit no other JS drift."""
    if path != '/assets/js/zeitgraph.js':
        return value, []
    replacements = [
        (
            "    var element = uebersicht ? track : marken[i];\n"
            "    var alternativen = JSON.parse(element.dataset.alternativen);\n"
            "    var canonicalAlternativen = JSON.parse(element.dataset.canonicalAlternativen || element.dataset.alternativen);",
            "    var alternativen = JSON.parse((uebersicht ? track : marken[i]).dataset.alternativen);",
            'separate mounted navigation alternatives from production canonical alternatives',
        ),
        (
            "      var adressen = link.tagName === 'LINK' ? canonicalAlternativen : alternativen;\n"
            "      var ziel = adressen[link.getAttribute('hreflang')];",
            "      var ziel = alternativen[link.getAttribute('hreflang')];",
            'select canonical alternatives only for head alternate links',
        ),
    ]
    applied = []
    for candidate, reference, description in replacements:
        if value.count(candidate) == 1:
            value = value.replace(candidate, reference)
            applied.append(description)
    return value, applied


def cookie_path_checks(origin: str, prefix: str, insecure: bool) -> list[dict]:
    client = parity.Client(origin, insecure)
    expected_secure = urllib.parse.urlsplit(origin).scheme == 'https'
    checks = []
    for path in CONTACT_PATHS:
        url = client.base + prefix + path
        request = urllib.request.Request(url, headers={'User-Agent': 'JackieLeven-Prefix-Parity/1.0'})
        try:
            response = client.opener.open(request, timeout=45)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.headers.get_all('Set-Cookie') or []
            status = response.status
        parsed = []
        for header in raw:
            cookies = SimpleCookie()
            cookies.load(header)
            for name, morsel in cookies.items():
                parsed.append({
                    'name': name,
                    'path': morsel['path'],
                    'secure': bool(morsel['secure']),
                    'httponly': bool(morsel['httponly']),
                    'samesite': morsel['samesite'].lower(),
                })
        checks.append({
            'path': path,
            'status': status,
            'cookies': parsed,
            'expected_path': prefix + '/',
            'expected_secure': expected_secure,
            'passed': status == 200 and bool(parsed) and all(
                cookie['path'] == prefix + '/'
                and cookie['secure'] == expected_secure
                and cookie['httponly']
                and cookie['samesite'] == 'lax'
                for cookie in parsed
            ),
        })
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, help='candidate origin without the mount prefix')
    parser.add_argument('--prefix', required=True, help='mount path, for example /jackieleven')
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--report', type=Path, default=Path('/tmp/jackie-prefix-parity.json'))
    parser.add_argument('--insecure', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--match', default='')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--assets', action='store_true')
    args = parser.parse_args()
    try:
        prefix = clean_prefix(args.prefix)
    except ValueError as exc:
        parser.error(str(exc))
    manifest = args.baseline / 'manifest.json'
    if not manifest.exists():
        parser.error('immutable baseline manifest does not exist')
    cases = json.loads(manifest.read_text())['cases']
    cases = [case for case in cases if args.match in case['path']]
    if args.limit:
        cases = cases[:args.limit]
    candidate = parity.Client(args.candidate.rstrip('/') + prefix, args.insecure)
    failures, assets, infrastructure_checks = [], set(), []
    noindex_count = 0
    canonical_alternatives_count = 0
    start = time.monotonic()

    def check(case):
        try:
            expected = parity.load_result(args.baseline, case)
            actual = candidate.fetch(case)
            normalized, violations, noindex, canonical_alternatives = normalize_candidate(expected, actual, prefix)
            differences = parity.diff_result(expected, normalized, case)
            differences.extend({'field': 'mount-contract', **item} for item in violations)
            infrastructure = parity.infrastructure_check(expected, normalized, case)
            return case, differences, expected.get('assets', []), infrastructure, noindex, canonical_alternatives
        except Exception as exc:
            return case, [{'field': 'error', 'error': str(exc)}], [], None, False, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for count, (case, differences, referenced, infrastructure, noindex, canonical_alternatives) in enumerate(pool.map(check, cases), 1):
            assets.update(referenced)
            noindex_count += int(noindex)
            canonical_alternatives_count += canonical_alternatives
            if infrastructure:
                infrastructure_checks.append(infrastructure)
            if differences:
                failures.append({'case': case, 'differences': differences})
            if count % 100 == 0 or count == len(cases):
                print(f'{count}/{len(cases)} pages; {len(failures)} failures; {time.monotonic()-start:.1f}s', flush=True)

    asset_cases = []
    asset_byte_differences = []
    asset_noindex_count = 0
    if args.assets:
        asset_cases = [{'path': value} for value in sorted(assets) if urllib.parse.urlsplit(value).path.endswith(('.css', '.js'))]
        for case in asset_cases:
            try:
                expected = parity.load_result(args.baseline, case)
                actual = candidate.fetch(case)
                actual, asset_noindex = normalized_preview_headers(expected, actual)
                asset_noindex_count += int(asset_noindex)
                if case['path'].endswith('.css') and isinstance(expected.get('body'), str) and isinstance(actual.get('body'), str):
                    expected_css, expected_violations, _ = normalize_css(expected['body'], case['path'])
                    actual_css, actual_violations, forms = normalize_css(actual['body'], case['path'], prefix, True)
                    comparable = json.loads(json.dumps(actual))
                    comparable['body'] = expected['body'] if actual_css == expected_css else actual_css
                    differences = parity.diff_result(expected, comparable, case)
                    differences.extend({'field': 'mount-contract', **item} for item in expected_violations + actual_violations)
                    if expected['body'] != actual['body']:
                        asset_byte_differences.append({
                            'path': case['path'],
                            'reference_sha256': text_hash(expected['body']),
                            'candidate_sha256': text_hash(actual['body']),
                            'reference_bytes': len(expected['body'].encode('utf-8')),
                            'candidate_bytes': len(actual['body'].encode('utf-8')),
                            'semantic_equal_after_css_url_resolution': actual_css == expected_css,
                            'candidate_url_forms': forms,
                        })
                elif case['path'].endswith('.js') and isinstance(expected.get('body'), list) and expected['body'][:1] == ['sha256']:
                    raw = raw_asset(candidate, case)
                    decoded = raw.decode('utf-8')
                    normalized_js, transformations = normalize_known_mount_javascript(case['path'], decoded)
                    normalized_contract = ['sha256', text_hash(normalized_js), len(normalized_js.encode('utf-8'))]
                    semantic_equal = normalized_contract == expected['body']
                    comparable = json.loads(json.dumps(actual))
                    comparable['body'] = expected['body'] if semantic_equal else normalized_contract
                    differences = parity.diff_result(expected, comparable, case)
                    if expected['body'] != actual['body']:
                        asset_byte_differences.append({
                            'path': case['path'],
                            'reference_sha256': expected['body'][1],
                            'candidate_sha256': actual['body'][1],
                            'reference_bytes': expected['body'][2],
                            'candidate_bytes': actual['body'][2],
                            'semantic_equal_after_exact_mount_transform': semantic_equal,
                            'exact_mount_transformations': transformations,
                        })
                else:
                    differences = parity.diff_result(expected, actual, case)
                if differences:
                    failures.append({'case': case, 'differences': differences})
            except Exception as exc:
                failures.append({'case': case, 'differences': [{'field': 'error', 'error': str(exc)}]})

    cookies = cookie_path_checks(args.candidate.rstrip('/'), prefix, args.insecure) if not args.match and not args.limit else []
    for check_result in cookies:
        if not check_result['passed']:
            failures.append({'case': {'path': prefix + check_result['path'], 'contract': 'cookie-path'}, 'differences': [{'field': 'cookie-path', 'actual': check_result['cookies'], 'expected': check_result['expected_path']}]})
    if noindex_count != len(cases):
        failures.append({'case': {'contract': 'preview-noindex'}, 'differences': [{'field': 'x-robots-tag', 'expected': f'noindex on {len(cases)} responses', 'actual': noindex_count}]})
    if args.assets and asset_noindex_count != len(asset_cases):
        failures.append({'case': {'contract': 'preview-asset-noindex'}, 'differences': [{'field': 'x-robots-tag', 'expected': f'noindex on {len(asset_cases)} asset responses', 'actual': asset_noindex_count}]})

    report = {
        'contract': 'prefix-parity-v1',
        'candidate_origin': args.candidate.rstrip('/'),
        'prefix': prefix,
        'baseline': str(args.baseline),
        'cases': len(cases),
        'assets': len(asset_cases),
        'failures': failures,
        'asset_byte_differences': asset_byte_differences,
        'cookie_path_checks': cookies,
        'preview_noindex': {'checked': len(cases), 'passed': noindex_count, 'asset_checked': len(asset_cases), 'asset_passed': asset_noindex_count},
        'canonical_alternatives': {'verified': canonical_alternatives_count},
        'infrastructure_checks': infrastructure_checks,
        'normalization_policy': {
            'mounted_html_attributes': sorted(MOUNTED_HTML_ATTRIBUTES),
            'mounted_json_attributes': sorted(MOUNTED_JSON_ATTRIBUTES),
            'redirect_location': True,
            'cookie_path_compared_not_normalized': True,
            'canonical_urls_normalized': False,
            'jsonld_normalized': False,
            'prefix_only_canonical_alternatives_verified_then_removed': True,
            'css_urls_resolved_to_logical_mount_paths': True,
            'css_byte_differences_reported': True,
            'javascript_mount_transform_exact_and_reported': True,
        },
        'duration_seconds': round(time.monotonic() - start, 2),
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Report: {args.report}; {len(failures)} failures; {len(asset_byte_differences)} documented asset byte differences', flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
