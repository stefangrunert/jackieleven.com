#!/usr/bin/env python3
"""One-time, transactional PHP-to-Go production switch; never prints credentials.

Install: sudo python3 install-go-production.py --release REV --expected-sha SHA256
Rollback: sudo python3 /var/backups/jackieleven-go-production/TRANSACTION/installer.py --rollback /var/backups/jackieleven-go-production/TRANSACTION
PHP's pool, release link, sessions and services are never modified.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request

BASE = Path('/var/www/jackieleven')
VHOST = Path('/etc/nginx/sites-available/jackieleven.com')
UNIT = Path('/etc/systemd/system/jackieleven-go.service')
ENV = Path('/etc/jackieleven/go.env')
START = Path('/usr/local/libexec/jackieleven-go-start')
PROXY = Path('/etc/nginx/jackieleven-go-proxy.conf')
CURRENT = BASE / 'go-current'
POOL = Path('/etc/php/8.3/fpm/pool.d/jackieleven.conf')
BACKUPS = Path('/var/backups/jackieleven-go-production')
SERVICE = 'jackieleven-go.service'
REQUIRED = ('JACKIE_RESEND_API_KEY', 'JACKIE_TURNSTILE_SITEKEY', 'JACKIE_TURNSTILE_SECRET')
ALLOWED = REQUIRED + ('JACKIE_FAN_VIDEOS',)
SOURCE = Path(__file__).resolve().parent

class DeploymentError(Exception):
    """Only static, credential-free diagnostics belong in this exception."""


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=60)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode=0o644):
    fd, name = tempfile.mkstemp(prefix='.jackie-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.lexists(name): os.unlink(name)


def credentials(text):
    """Read only literal env[] assignments in the named FPM pool; no interpolation."""
    result = {}
    section = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith((';', '#')): continue
        if line.startswith('['):
            match = re.fullmatch(r'\[([^\]]+)\]\s*(?:;.*)?', line)
            section = match.group(1) if match else None
            continue
        if section != 'jackieleven': continue
        match = re.match(r'env\[([^\]]+)\]\s*=\s*(.*)\Z', line)
        if not match:
            if any(re.match(r'env\[\s*'+key+r'\s*\]', line) for key in ALLOWED):
                raise DeploymentError('Invalid credential assignment')
            continue
        key, literal = match.groups()
        if key not in ALLOWED: continue
        if key in result: raise DeploymentError('Duplicate credential assignment')
        if literal.startswith(('"', "'")):
            quote = literal[0]
            value = ''
            i = 1
            while i < len(literal) and literal[i] != quote:
                char = literal[i]
                if char == '\\':
                    i += 1
                    if i >= len(literal) or literal[i] not in ('\\', quote):
                        raise DeploymentError('Unsupported credential escape')
                    char = literal[i]
                value += char
                i += 1
            if i == len(literal) or not re.fullmatch(r'\s*(?:;.*)?', literal[i+1:]):
                raise DeploymentError('Invalid credential literal')
        else:
            match = re.fullmatch(r'([A-Za-z0-9_./:@+\-=]+)\s*(?:;.*)?', literal)
            if not match: raise DeploymentError('Credential must be a literal')
            value = match.group(1)
        if not value or '$' in value or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise DeploymentError('Unsupported credential value')
        result[key] = value
    if any(key not in result for key in REQUIRED): raise DeploymentError('Required credentials missing')
    if result.get('JACKIE_FAN_VIDEOS', '0') not in ('0', '1'):
        raise DeploymentError('Invalid fan-video switch')
    return result


def environment(values):
    return ''.join(key+'="'+values[key].replace('\\', '\\\\').replace('"', '\\"')+'"\n'
                   for key in ALLOWED if key in values).encode()


def verify_release(release):
    if release.is_symlink() or not release.is_dir(): raise DeploymentError('Release missing or linked')
    paths = set()
    manifest = release / 'release-manifest.sha256'
    if manifest.is_symlink(): raise DeploymentError('Invalid release manifest')
    for line in manifest.read_text().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  (.+)', line)
        if not match: raise DeploymentError('Invalid release manifest')
        checksum, name = match.groups()
        if name in paths or '\\' in name or any(p in ('', '.', '..') for p in name.split('/')):
            raise DeploymentError('Invalid release path')
        paths.add(name)
        path = release
        for part in name.split('/'):
            path /= part
            if path.is_symlink(): raise DeploymentError('Linked release file')
        if not path.is_file() or digest(path.read_bytes()) != checksum:
            raise DeploymentError('Release checksum mismatch')
    actual = set()
    for path in [release, *release.rglob('*')]:
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise DeploymentError('Invalid release entry')
        if path.is_file(): actual.add(str(path.relative_to(release)))
        if path.stat().st_mode & 0o022: raise DeploymentError('Writable release entry')
        if path.stat().st_uid != os.getuid(): raise DeploymentError('Release owner mismatch')
    if actual != paths | {'release-manifest.sha256'} or not {'bin/jackieleven', 'build.json'} <= paths:
        raise DeploymentError('Incomplete release manifest')
    build = json.loads((release/'build.json').read_text())
    if build.get('goos') != 'linux' or build.get('goarch') != 'amd64':
        raise DeploymentError('Release platform mismatch')
    if not os.access(release/'bin/jackieleven', os.X_OK): raise DeploymentError('Release not executable')


class Form(HTMLParser):
    def __init__(self):
        super().__init__(); self.token = False; self.ready = False; self.sitekey = False
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'input' and attrs.get('name') == 'token':
            self.token = bool(re.fullmatch('[a-f0-9]{48}', attrs.get('value', '')))
        if tag == 'button' and attrs.get('type') == 'submit': self.ready = 'disabled' not in attrs
        if 'cf-turnstile' in attrs.get('class', '').split(): self.sitekey = bool(attrs.get('data-sitekey'))


def check_response(path, headers, body):
    if path == '/de/':
        if '/assets/' not in body or 'https://jackieleven.com/de' not in body or 'noindex' in headers.get('X-Robots-Tag', ''):
            raise DeploymentError('Home response contract failed')
    else:
        form = Form(); form.feed(body)
        cookie = SimpleCookie(); cookie.load(headers.get('Set-Cookie', ''))
        item = cookie.get('jackie_contact')
        if not (form.token and form.ready and form.sitekey and item and item['secure'] and item['httponly']
                and item['samesite'].lower() == 'lax' and item['path'] == '/'
                and headers.get('Cache-Control') == 'no-store, no-cache, must-revalidate'):
            raise DeploymentError('Contact readiness contract failed')


def healthcheck(tls=False):
    # GET only: no Turnstile verification, email or credential-bearing request.
    for path in ('/de/', '/de/mitmachen'):
        if tls:
            with tempfile.TemporaryDirectory(prefix='jackie-health-') as tmp:
                head, body = Path(tmp)/'headers', Path(tmp)/'body'
                run('curl', '--silent', '--show-error', '--fail', '--max-time', '5',
                    '--resolve', 'jackieleven.com:443:127.0.0.1', '--dump-header', str(head),
                    '--output', str(body), 'https://jackieleven.com'+path)
                from email.parser import Parser
                header_text = head.read_text().replace('\r\n', '\n').strip().split('\n\n')[-1]
                headers = Parser().parsestr(header_text.partition('\n')[2])
                check_response(path, headers, body.read_text())
        else:
            request = urllib.request.Request('http://127.0.0.1:18765'+path,
                headers={'Host':'jackieleven.com', 'X-Forwarded-Proto':'https'})
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status != 200: raise DeploymentError('Backend status failed')
                check_response(path, response.headers, response.read().decode())
        time.sleep(0.3)


def wait_health(tls=False):
    for attempt in range(12):
        try: healthcheck(tls); return
        except Exception:
            if attempt == 11: raise DeploymentError('TLS health check failed' if tls else 'Backend health check failed') from None
            time.sleep(0.5)


def artifact_paths():
    return {'vhost': VHOST, 'unit': UNIT, 'env': ENV, 'start': START, 'proxy': PROXY, 'current': CURRENT}


def snapshot(backup, installed_vhost):
    entries = {}
    for name, path in artifact_paths().items():
        if path.is_symlink(): raise DeploymentError('Unexpected linked configuration')
        entry = {'path':str(path), 'present':path.exists()}
        if path.exists():
            if not path.is_file(): raise DeploymentError('Unexpected configuration type')
            data = path.read_bytes()
            entry.update(mode=stat.S_IMODE(path.stat().st_mode), sha=digest(data))
            atomic_write(backup/name, data, 0o600)
        entries[name] = entry
    manifest = {'version':1, 'entries':entries, 'installed_vhost_sha':digest(installed_vhost), 'created_dirs':[]}
    save_manifest(backup, manifest)
    return manifest


def save_manifest(backup, manifest):
    atomic_write(backup/'manifest.json', (json.dumps(manifest, indent=2)+'\n').encode(), 0o600)


def restore(name, backup, manifest):
    entry = manifest['entries'][name]
    path = artifact_paths()[name]
    if entry['present']:
        data = (backup/name).read_bytes()
        if digest(data) != entry['sha']: raise DeploymentError('Backup checksum mismatch')
        atomic_write(path, data, entry['mode'])
    elif path.exists() or path.is_symlink(): path.unlink()


def nginx_workers():
    result = run('ps', '-C', 'nginx', '-o', 'pid=,args=')
    workers = [int(line.split(None, 1)[0]) for line in result.stdout.splitlines()
               if 'nginx: worker process' in line]
    if not workers: raise DeploymentError('No nginx workers found')
    return workers


def wait_worker_drain(workers):
    # nginx reload returns before old workers drain keepalive/in-flight requests.
    # Keep the Go backend available until every old worker has exited.
    for attempt in range(80):
        active = []
        for pid in workers:
            try:
                if b'nginx: worker process' in Path(f'/proc/{pid}/cmdline').read_bytes(): active.append(pid)
            except FileNotFoundError: pass
        if not active: return
        time.sleep(0.5)
    raise DeploymentError('Old nginx workers have not drained; backend retained')


def rollback(backup, manifest=None):
    if os.geteuid() != 0: raise DeploymentError('Root required')
    backup = Path(backup)
    if manifest is None:
        if backup.parent.resolve() != BACKUPS.resolve() or backup.is_symlink():
            raise DeploymentError('Invalid backup directory')
        for path in (backup, backup/'manifest.json'):
            info = path.lstat()
            if info.st_uid != 0 or info.st_mode & 0o077: raise DeploymentError('Unsafe backup permissions')
        manifest = json.loads((backup/'manifest.json').read_text())
        if manifest.get('version') != 1 or set(manifest.get('entries', {})) != set(artifact_paths()):
            raise DeploymentError('Invalid backup manifest')
        for name, path in artifact_paths().items():
            if manifest['entries'][name]['path'] != str(path): raise DeploymentError('Backup path mismatch')
    if digest(VHOST.read_bytes()) not in (manifest['installed_vhost_sha'], manifest['entries']['vhost']['sha']):
        raise DeploymentError('Vhost changed since installation')
    if manifest.get('state') == 'rolled-back': return
    # Restore and reload PHP before stopping Go. If nginx cannot reload, retain
    # the running Go service and its files so old nginx workers remain usable.
    workers = nginx_workers()
    for name in ('vhost', 'proxy'): restore(name, backup, manifest)
    run('nginx', '-t')
    run('systemctl', 'reload', 'nginx')
    wait_worker_drain(workers)
    if manifest.get('start_attempted'): run('systemctl', 'stop', SERVICE)
    if manifest.get('enable_attempted'): run('systemctl', 'disable', SERVICE)
    for name in ('unit', 'env', 'start', 'current'): restore(name, backup, manifest)
    run('systemctl', 'daemon-reload')
    for directory in reversed(manifest['created_dirs']):
        try: Path(directory).rmdir()
        except OSError: pass  # Never remove nonempty or pre-existing directories.
    manifest['state'] = 'rolled-back'
    save_manifest(backup, manifest)


def install(revision, expected_sha):
    if os.geteuid() != 0: raise DeploymentError('Root required')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,79}', revision or '') or not re.fullmatch('[a-f0-9]{64}', expected_sha or ''):
        raise DeploymentError('Invalid release or expected digest')
    release = BASE/'go-releases'/revision
    verify_release(release)
    pwd.getpwnam('jackieleven')
    if VHOST.is_symlink() or digest(VHOST.read_bytes()) != expected_sha: raise DeploymentError('Vhost precondition failed')
    for path in (UNIT, ENV, START, CURRENT):
        if path.exists() or path.is_symlink(): raise DeploymentError('Production Go artifact already exists')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 18765)) == 0: raise DeploymentError('Backend port already occupied')
    values = credentials(POOL.read_text())
    templates = {name:(SOURCE/source).read_bytes() for name, source in {
        'unit':'jackieleven-go.service', 'start':'run-go-release.sh',
        'proxy':'nginx-go-proxy.conf', 'vhost':'nginx-go-site.conf'}.items()}
    BACKUPS.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=time.strftime('%Y%m%dT%H%M%S-'), dir=BACKUPS))
    backup.chmod(0o700)
    manifest = snapshot(backup, templates['vhost'])
    atomic_write(backup/'installer.py', Path(__file__).read_bytes(), 0o700)
    phase = 'service installation'
    try:
        for parent in (ENV.parent, START.parent):
            if not parent.exists():
                # Known system paths have existing grandparents; no broad mkdir.
                manifest['created_dirs'].append(str(parent)); save_manifest(backup, manifest)
                parent.mkdir(mode=0o755)
        atomic_write(ENV, environment(values), 0o600)
        for name in ('unit', 'start', 'proxy'):
            atomic_write(artifact_paths()[name], templates[name], 0o755 if name == 'start' else 0o644)
        CURRENT.symlink_to(release)
        run('systemd-analyze', 'verify', str(UNIT))
        run('systemctl', 'daemon-reload')
        manifest['start_attempted'] = True; save_manifest(backup, manifest)
        run('systemctl', 'start', SERVICE)
        phase = 'backend readiness'
        wait_health()
        phase = 'nginx switch'
        # Do not overwrite concurrent configuration changes after preflight.
        if digest(VHOST.read_bytes()) != expected_sha: raise DeploymentError('Vhost changed during installation')
        atomic_write(VHOST, templates['vhost'], manifest['entries']['vhost']['mode'])
        run('nginx', '-t')
        run('systemctl', 'reload', 'nginx')
        phase = 'TLS readiness'
        wait_health(tls=True)
        manifest['enable_attempted'] = True; save_manifest(backup, manifest)
        run('systemctl', 'enable', SERVICE)
        manifest['state'] = 'installed'; save_manifest(backup, manifest)
    except BaseException:
        try:
            rollback(backup, manifest)
            status = 'restored PHP'
        except BaseException:
            status = 'incomplete; use saved rollback command'
        raise DeploymentError(f'Installation failed during {phase}; rollback {status}; backup {backup}') from None
    return {'release':str(release), 'backup':str(backup), 'url':'https://jackieleven.com',
            'service':SERVICE, 'rollback':['python3', str(backup/'installer.py'), '--rollback', str(backup)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release')
    parser.add_argument('--expected-sha')
    parser.add_argument('--rollback', type=Path)
    args = parser.parse_args(argv)
    if args.rollback and (args.release or args.expected_sha): parser.error('Rollback cannot be combined with installation')
    if not args.rollback and not (args.release and args.expected_sha): parser.error('Installation requires release and expected digest')
    try:
        if args.rollback:
            rollback(args.rollback); result = {'state':'PHP restored', 'backup':str(args.rollback)}
        else: result = install(args.release, args.expected_sha)
        print(json.dumps(result))
        return 0
    except DeploymentError as error:
        print(str(error), file=sys.stderr)
    except BaseException:
        # OS/subprocess/INI errors can contain secrets; never expose exception text.
        print('Production operation failed; no diagnostic payload was printed', file=sys.stderr)
    return 1

if __name__ == '__main__': sys.exit(main())
