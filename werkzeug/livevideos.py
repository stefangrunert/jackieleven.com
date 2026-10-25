#!/usr/bin/env python3
"""Refresh live-video permissions and local 480×270 WebP thumbnails.

The updater, never the Go server, contacts YouTube. JACKIE_YOUTUBE_API_KEY enables
Data API checks (embedding, public status, age and Germany availability). Without
it, oEmbed checks embedding availability only. --vorschau renews all thumbnails.
Pillow is required only when a thumbnail needs to be written.
"""
import argparse
from copy import deepcopy
from datetime import date
from io import BytesIO
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from content import ROOT, read_json, write_json

VIDEO_ID = re.compile(r'[A-Za-z0-9_-]{11}\Z')


def fetch(url):
    try:
        with urlopen(Request(url, headers={'User-Agent': 'jackieleven-werkzeug'}), timeout=20) as response:
            body = response.read((16 << 20) + 1)
            if len(body) > 16 << 20:
                raise RuntimeError('Upstream response exceeds 16 MiB')
            return response.status, body
    except HTTPError as error:
        return error.code, b''
    except URLError:
        # In particular, do not print a Data API URL containing its credential.
        raise RuntimeError('Network request failed') from None


def api_permissions(ids, key, transport=fetch):
    result = {video_id: {'embeddable': False, 'grund': 'nicht gefunden'} for video_id in ids}
    for offset in range(0, len(ids), 50):
        batch = ids[offset:offset + 50]
        status, body = transport('https://www.googleapis.com/youtube/v3/videos?' + urlencode({'part': 'status,contentDetails', 'id': ','.join(batch), 'key': key}))
        if status != 200:
            raise RuntimeError(f'YouTube Data API antwortet mit {status}')
        for video in json.loads(body)['items']:
            details, state = video.get('contentDetails', {}), video.get('status', {})
            regions = details.get('regionRestriction', {})
            if not state.get('embeddable', False):
                reason = 'Einbetten gesperrt'
            elif state.get('privacyStatus') != 'public':
                reason = 'nicht öffentlich'
            elif details.get('contentRating', {}).get('ytRating') == 'ytAgeRestricted':
                reason = 'altersbeschränkt'
            elif 'DE' in regions.get('blocked', []) or ('allowed' in regions and 'DE' not in regions['allowed']):
                reason = 'in Deutschland gesperrt'
            else:
                reason = ''
            result[video['id']] = {'embeddable': reason == '', 'grund': reason}
    return result


def oembed_permission(video_id, transport=fetch):
    status, _ = transport('https://www.youtube.com/oembed?' + urlencode({'url': 'https://www.youtube.com/watch?v=' + video_id, 'format': 'json'}))
    if status == 200:
        return {'embeddable': True, 'grund': ''}
    if status in (401, 403):
        return {'embeddable': False, 'grund': 'Einbetten gesperrt'}
    if status == 404:
        return {'embeddable': False, 'grund': 'entfernt oder privat'}
    raise RuntimeError(f'oEmbed antwortet für {video_id} mit {status}')


def thumbnail(video_id, directory, transport=fetch):
    if not VIDEO_ID.fullmatch(video_id):
        raise ValueError('Invalid YouTube video ID')
    from PIL import Image
    status, body = transport('https://i.ytimg.com/vi/' + video_id + '/hqdefault.jpg')
    if status != 200:
        raise RuntimeError('Kein Vorschaubild für ' + video_id)
    with Image.open(BytesIO(body)) as image:
        width, height = image.size
        crop_height = int(width * 9 / 16 + .5)
        top = (height - crop_height) // 2
        result = image.crop((0, top, width, top + crop_height)).convert('RGB').resize((480, 270), Image.Resampling.LANCZOS)
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (video_id + '.webp')
        result.save(path, 'WEBP', quality=62)
    return path.stat().st_size


def update(catalogue, directory, key='', refresh=False, transport=fetch, previewer=None, today=None, pause=time.sleep):
    data = deepcopy(catalogue)
    ids = list(dict.fromkeys(video['id'] for concert in data.values() for video in concert['videos']))
    if not all(VIDEO_ID.fullmatch(video_id) for video_id in ids):
        raise ValueError('Invalid YouTube video ID in catalogue')
    permissions = api_permissions(ids, key, transport) if key else {}
    day = today or date.today().isoformat()
    previewer = previewer or (lambda video_id: thumbnail(video_id, directory, transport))
    messages = []
    for name, concert in data.items():
        for video in concert['videos']:
            video_id = video['id']
            permission = permissions.get(video_id) if key else oembed_permission(video_id, transport)
            video['embeddable'], video['checked'] = permission['embeddable'], day
            size = ''
            if permission['embeddable'] and (refresh or not (Path(directory) / (video_id + '.webp')).is_file()):
                size = f' · Vorschau {previewer(video_id) / 1024:.1f} KB'
            state = ' einbettbar' if permission['embeddable'] else ' NICHT einbettbar (' + permission['grund'] + ')'
            messages.append(name.ljust(18) + video_id + state + size)
            if not key:
                pause(.25)
    return data, messages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--vorschau', action='store_true')
    args = parser.parse_args()
    path = args.root / 'data/live-videos.json'
    key = os.environ.get('JACKIE_YOUTUBE_API_KEY', '')
    try:
        data, messages = update(read_json(path), args.root / 'assets/bilder/live', key=key, refresh=args.vorschau)
    except (OSError, ValueError, KeyError, RuntimeError, ImportError) as error:
        raise SystemExit(str(error)) from None
    write_json(path, data, indent=2)
    print('\n'.join(messages))
    print('Geprüft über die YouTube Data API.' if key else 'Geprüft über oEmbed (ohne API-Schlüssel: Länder- und Alterssperren nicht erfasst).')


if __name__ == '__main__':
    main()
