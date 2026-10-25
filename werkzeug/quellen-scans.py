"""Build page references and licensed facsimiles from research and NB IIIF manifests.

Run manually; no requests are made while serving the site. No page offsets are
guessed: printed page labels must match the manifest. Images stay at the archive.
"""
import concurrent.futures
import datetime
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = re.compile(r'\b(?:S\.|Seite[n]?|pp?\.)\s*(\d+(?:\s*(?:[–-]|/|und|,)\s*\d+)*)')


def page_numbers(label):
    result = []
    for part in re.split(r'\s*(?:/|und|,)\s*', label):
        bounds = re.split(r'\s*[–-]\s*', part)
        if len(bounds) == 2:
            a, b = map(int, bounds)
            if b < a or b - a > 30:
                return []
            result.extend(range(a, b + 1))
        else:
            result.append(int(part))
    return list(dict.fromkeys(result))


def build(q):
    source_id = pathlib.Path(q['datei']).stem.replace('_', '-')
    # Only source metadata, never a reference to a different article in the body.
    evidence = q.get('gefunden_ueber', '')
    match = PAGE.search(evidence) or PAGE.search(q['medium'])
    result = {'pages': match[1] if match else '', 'url': q['url'], 'facsimiles': []}
    urn = re.search(r'URN:NBN:no-nb_[A-Za-z0-9_]+', q['url'])
    if not urn:
        return source_id, result
    urn = urn[0]
    manifest_url = f'https://api.nb.no/catalog/v1/iiif/{urn}/manifest'
    try:
        response = subprocess.run(['curl', '-LsS', '--fail', '--max-time', '25', manifest_url], capture_output=True, check=True)
        manifest = json.loads(response.stdout)
        result['manifest'] = manifest_url
        result['checked'] = datetime.date.today().isoformat()
        license_url = manifest.get('license', '')
        result['rights'] = license_url
        result['public_access'] = any(m.get('label') == 'Tilgang' and m.get('value') == 'Tilgang for alle' for m in manifest.get('metadata', []))
        # Explicit NB reuse licences only. Mere access is not permission.
        license_name = ('ccbyncnd' if '#cc-by-nc-nd' in license_url else
                        'ccbync' if '#cc-by-nc-' in license_url else None)
        result['license'] = license_name
        canvases = manifest['sequences'][0]['canvases']
        wanted = page_numbers(result['pages']) if result['pages'] else []
        links = []
        for number in wanted:
            matches = [(i, c) for i, c in enumerate(canvases) if str(c.get('label', '')).strip() == str(number)]
            if len(matches) != 1:
                continue
            index, canvas = matches[0]
            link = f'https://www.nb.no/items/{urn}?page={index}'
            links.append({'page': str(number), 'url': link})
            if not license_name or not result['public_access']:
                continue
            resource = canvas['images'][0]['resource']
            service = resource['service']['@id']
            result['facsimiles'].append({'page': str(number), 'url': link,
                'image': service + '/full/800,/0/native.jpg',
                'full': resource['@id'], 'width': resource['width'], 'height': resource['height']})
        if links:
            result['url'] = links[0]['url']
            result['page_links'] = links
        else:
            result['url'] = f'https://www.nb.no/items/{urn}'
    except (subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        result['error'] = type(error).__name__
    return source_id, result


if __name__ == '__main__':
    sources = json.loads((ROOT / 'research/quellen/index.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        data = dict(pool.map(build, sources))
    (ROOT / 'data/quellen-scans.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'sources': len(data), 'with_pages': sum(bool(x['pages']) for x in data.values()),
        'with_facsimiles': sum(bool(x['facsimiles']) for x in data.values()),
        'errors': sum('error' in x for x in data.values())}))
