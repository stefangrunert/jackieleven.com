#!/usr/bin/env python3
"""Root-only, reversible installer for the explicitly requested unpubli.sh preview.
Run on Hetzner after uploading a verified Go release and these three templates.
Never changes jackieleven.com, its PHP service, or the unpubli.sh document root.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import time
import urllib.error
import urllib.request

BASE = Path('/var/www/jackieleven-go-preview')
VHOST = Path('/etc/nginx/sites-enabled/unpublish')
UNIT = Path('/etc/systemd/system/jackieleven-go-preview.service')
LOCATION = Path('/etc/nginx/snippets/jackieleven-preview.conf')
LIMITS = Path('/etc/nginx/conf.d/jackieleven-preview-limits.conf')
REALIP = Path('/etc/nginx/snippets/jackieleven-preview-realip.conf')
SOURCE_REALIP = Path('/etc/nginx/jackieleven-cloudflare.conf')
SERVICE = 'jackieleven-go-preview.service'
ANCHOR = '    root /var/www/unpublish/public;\n    include snippets/optimistic-subpath.conf;'
INCLUDE = '    include snippets/jackieleven-preview.conf;'


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True)


def atomic_write(path, data, mode=0o644):
    temp = path.with_name(path.name + '.jackie-next')
    with temp.open('xb') as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    temp.chmod(mode)
    os.replace(temp, path)


def healthcheck():
    request = urllib.request.Request('http://127.0.0.1:18766/jackieleven/de/',
                                    headers={'Host': 'unpubli.sh', 'X-Forwarded-Proto': 'https'})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode()
        if response.status != 200 or '/jackieleven/assets/' not in body or 'noindex' not in response.headers.get('X-Robots-Tag', ''):
            raise RuntimeError('Preview health contract failed')



def https_healthcheck():
    # systemctl reload returns after signalling nginx, before its replacement
    # workers necessarily accept connections. Retry the verified endpoint briefly.
    for attempt in range(20):
        try:
            result = run('curl', '--silent', '--show-error', '--fail', '--max-time', '5',
                         '--resolve', 'unpubli.sh:443:127.0.0.1', 'https://unpubli.sh/jackieleven/de/')
            if '/jackieleven/assets/' not in result.stdout:
                raise RuntimeError('HTTPS smoke check failed')
            return
        except (subprocess.CalledProcessError, RuntimeError):
            if attempt == 19: raise
            time.sleep(0.5)


def install(release, expected_sha):
    if os.geteuid() != 0:
        raise RuntimeError('Run as root on the target server')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', release):
        raise ValueError('Invalid release ID')
    root = BASE / 'releases' / release
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Release must be an existing real directory')
    for line in (root / 'release-manifest.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if not re.fullmatch(r'[0-9a-f]{64}', digest) or any(p in ('', '.', '..') for p in name.split('/')) or name.startswith('/'):
            raise ValueError('Invalid manifest entry')
        path = root
        for part in name.split('/'):
            path = path / part
            if path.is_symlink(): raise ValueError('Symlink in release')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Checksum mismatch: ' + name)
    meta = json.loads((root / 'build.json').read_text())
    if meta['goos'] != 'linux' or meta['goarch'] != 'amd64':
        raise ValueError('Expected Linux/amd64 release')
    original = VHOST.read_bytes()
    if hashlib.sha256(original).hexdigest() != expected_sha:
        raise RuntimeError('Vhost changed since inspection; refusing to overwrite concurrent work')
    config = original.decode()
    if INCLUDE not in config:
        if config.count(ANCHOR) != 1 or re.search(r'location\s+(?:[=^~*]+\s+)?/jackieleven', config):
            raise RuntimeError('Ambiguous preview insertion point')
        config = config.replace(ANCHOR, ANCHOR + '\n' + INCLUDE, 1)
    templates = Path(__file__).resolve().parent
    unit = (templates / 'jackieleven-preview.service').read_text().replace('@RELEASE_ROOT@', str(root)).encode()
    replacements = {VHOST: config.encode(), UNIT: unit,
                    LOCATION: (templates / 'nginx-preview-location.conf').read_bytes(),
                    LIMITS: (templates / 'nginx-preview-limits.conf').read_bytes(),
                    REALIP: SOURCE_REALIP.read_bytes()}
    backup = Path('/var/backups/jackieleven-go-preview') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup.mkdir(parents=True, mode=0o700)
    old = {}
    for index, path in enumerate(replacements):
        if path.is_symlink(): raise RuntimeError('Refusing symlink configuration: ' + str(path))
        saved = None
        if path.exists():
            saved = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
            item = backup / str(index)
            item.write_bytes(saved[0]); item.chmod(0o600)
        old[path] = saved
    (backup / 'manifest.json').write_text(json.dumps({str(path): {'file': str(i) if old[path] else None, 'mode': old[path][1] if old[path] else None} for i, path in enumerate(old)}, indent=2))
    (backup / 'manifest.json').chmod(0o600)
    was_active = subprocess.run(['systemctl', 'is-active', '--quiet', SERVICE]).returncode == 0
    was_enabled = subprocess.run(['systemctl', 'is-enabled', '--quiet', SERVICE], capture_output=True).returncode == 0
    try:
        pwd.getpwnam('jackieleven-preview')
    except KeyError:
        run('useradd', '--system', '--user-group', '--no-create-home', '--home-dir', '/nonexistent', '--shell', '/usr/sbin/nologin', 'jackieleven-preview')
    try:
        for path, data in replacements.items(): atomic_write(path, data)
        run('systemd-analyze', 'verify', str(UNIT))
        run('nginx', '-t')
        run('systemctl', 'daemon-reload')
        run('systemctl', 'restart', SERVICE)
        for attempt in range(20):
            try:
                healthcheck(); break
            except (OSError, urllib.error.URLError):
                if attempt == 19: raise
                time.sleep(0.2)
        run('systemctl', 'reload', 'nginx')
        # Local HTTPS exercises TLS and the exact nginx path before enabling.
        https_healthcheck()
        run('systemctl', 'enable', SERVICE)
    except Exception:
        for path, saved in old.items():
            if saved is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, saved[0], saved[1])
        run('systemctl', 'daemon-reload')
        if was_active: run('systemctl', 'restart', SERVICE)
        else: subprocess.run(['systemctl', 'stop', SERVICE], check=False)
        if not was_enabled: subprocess.run(['systemctl', 'disable', SERVICE], check=False, capture_output=True)
        run('nginx', '-t'); run('systemctl', 'reload', 'nginx')
        raise
    print(json.dumps({'release': release, 'backup': str(backup), 'url': 'https://unpubli.sh/jackieleven/', 'service': SERVICE}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', required=True)
    parser.add_argument('--expected-vhost-sha', required=True)
    args = parser.parse_args()
    install(args.release, args.expected_vhost_sha)
