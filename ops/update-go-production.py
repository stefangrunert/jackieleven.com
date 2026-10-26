#!/usr/bin/env python3
"""Transactional update of the existing Go site, with a separate search process.

Existing form environment, state, PHP fallback and staging services are preserved.
The initial production search uses the verified immutable staging database with
read-only credentials; it never imports, drops or rewrites a database.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import subprocess
import time
import urllib.request

SOURCE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('initial', SOURCE / 'install-go-production.py')
initial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(initial)
run, write, digest = initial.run, initial.atomic_write, initial.digest
BASE = Path('/var/www/jackieleven')
CURRENT = BASE / 'go-current'
VHOST = Path('/etc/nginx/sites-available/jackieleven.com')
WEB_UNIT = Path('/etc/systemd/system/jackieleven-go.service')
SEARCH_UNIT = Path('/etc/systemd/system/jackieleven-search.service')
SECRET_DIR = Path('/etc/jackieleven-search')
KEY = SECRET_DIR / 'deepinfra-key'
SEARCH_ENV = SECRET_DIR / 'production.env'
WEB_ENV = Path('/etc/jackieleven/search.env')
LOCATION = Path('/etc/nginx/snippets/jackieleven-search-production.conf')
LIMITS = Path('/etc/nginx/conf.d/jackieleven-search-production-limits.conf')
BACKUPS = Path('/var/backups/jackieleven-go-updates')
SEARCH_SERVICE = 'jackieleven-search.service'
WEB_SERVICE = 'jackieleven-go.service'
INCLUDE = '    include /etc/nginx/snippets/jackieleven-search-production.conf;'


def nginx_config(original):
    if INCLUDE in original:
        return original
    anchor = '    include /etc/nginx/jackieleven-cloudflare.conf;'
    referrer = 'add_header Referrer-Policy strict-origin-when-cross-origin always;'
    if original.count(anchor) != 1 or original.count(referrer) != 1:
        raise RuntimeError('Unexpected production vhost; inspect before updating')
    return original.replace(anchor, anchor + '\n' + INCLUDE).replace(referrer, 'add_header Referrer-Policy $jackie_production_referrer always;')


def snapshot(paths, backup):
    result = {}
    for i, p in enumerate(paths):
        if p.is_symlink():
            result[str(p)] = {'link': os.readlink(p)}
        elif p.exists():
            info = p.stat()
            if not p.is_file(): raise RuntimeError('Expected regular configuration file')
            name = str(i)
            write(backup / name, p.read_bytes(), 0o600)
            result[str(p)] = {'file': name, 'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid}
        else:
            result[str(p)] = None
    return result


def link_to(path, target):
    temp = path.with_name(path.name + '.next')
    if temp.exists() or temp.is_symlink(): raise RuntimeError('Pending release link exists')
    temp.symlink_to(target)
    temp.replace(path)


def restore_files(backup, entries):
    for name, entry in entries.items():
        p = Path(name)
        if entry is None:
            p.unlink(missing_ok=True)
        elif 'link' in entry:
            link_to(p, entry['link'])
        else:
            write(p, (backup / entry['file']).read_bytes(), entry['mode'])
            os.chown(p, entry['uid'], entry['gid'])


def active(service):
    return subprocess.run(['systemctl', 'is-active', '--quiet', service], capture_output=True).returncode == 0


def rollback(backup, manifest):
    if not manifest['search_enabled'] and SEARCH_UNIT.exists():
        run('systemctl', 'disable', SEARCH_SERVICE)
    if not manifest['search_active'] and active(SEARCH_SERVICE):
        run('systemctl', 'stop', SEARCH_SERVICE)
    restore_files(backup, manifest['entries'])
    run('systemctl', 'daemon-reload')
    if manifest['search_active']:
        run('systemctl', 'restart', SEARCH_SERVICE)
    run('systemctl', 'restart', WEB_SERVICE)
    run('nginx', '-t')
    run('systemctl', 'reload', 'nginx')
    initial.wait_health(tls=True)
    manifest['state'] = 'rolled-back'
    write(backup / 'transaction.json', json.dumps(manifest, indent=2).encode(), 0o600)


def ready(version):
    for attempt in range(30):
        try:
            with urllib.request.urlopen('http://127.0.0.1:18768/readyz', timeout=3) as response:
                if response.status != 200 or response.headers.get('X-Archive-Content-Version') != version:
                    raise RuntimeError('Unexpected search content version')
            return
        except OSError:
            if attempt == 29: raise RuntimeError('Production search not ready') from None
            time.sleep(.3)


def verify_semantic(version):
    request = urllib.request.Request('http://127.0.0.1:18768/v1/search?q=konzerte+in+norwegen&lang=de&mode=hybrid&rerank=1&grouped=1',
                                    headers={'X-Archive-Content-Version': version})
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.load(response)
    if result.get('degraded') or not result.get('hits') or result.get('content_version') != version:
        raise RuntimeError('Real semantic search check failed')
    return {'hits':len(result['hits']), 'duration_ms':result.get('duration_ms'), 'degraded':False}


def verify_public_search():
    # TLS origin checks avoid cache ambiguity. No email is sent.
    for path, label in [('/de/suche', 'Suchen'), ('/en/search', 'Search')]:
        response = run('curl', '--fail', '--silent', '--show-error', '--max-time', '10',
                       '--resolve', 'jackieleven.com:443:127.0.0.1', 'https://jackieleven.com' + path)
        if 'data-search-pending' not in response.stdout or label not in response.stdout or '/jackieleven/assets/' in response.stdout:
            raise RuntimeError('Public search page check failed')


def install(release_id, expected_sha, expected_current):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', release_id) or not re.fullmatch(r'[a-f0-9]{64}', expected_sha):
        raise RuntimeError('Invalid deployment arguments')
    root = BASE / 'go-releases' / release_id
    initial.verify_release(root)
    if json.loads((root/'build.json').read_text()).get('dirty'):
        raise RuntimeError('Refusing uncommitted production release')
    version = json.loads((root/'search-manifest.json').read_text())['content_version']
    if not re.fullmatch('[a-f0-9]{64}', version): raise RuntimeError('Invalid index version')
    if not (root/'bin/jackieleven-search').is_file(): raise RuntimeError('Missing search binary')
    if not CURRENT.is_symlink() or str(CURRENT.resolve()) != expected_current or digest(VHOST.read_bytes()) != expected_sha:
        raise RuntimeError('Production changed since inspection')
    if not active(WEB_SERVICE): raise RuntimeError('Existing Go website must be active')
    vhost = nginx_config(VHOST.read_text()).encode()
    webunit = WEB_UNIT.read_text()
    webenv_line = 'EnvironmentFile=/etc/jackieleven/search.env'
    if webenv_line not in webunit:
        anchor = 'EnvironmentFile=/etc/jackieleven/go.env'
        if webunit.count(anchor) != 1: raise RuntimeError('Unexpected website unit')
        webunit = webunit.replace(anchor, anchor + '\n' + webenv_line)
    # The source file is root-only and never returned in diagnostics.
    source_env = Path('/etc/jackieleven-search-preview.env').read_text()
    db_lines = [line for line in source_env.splitlines() if line.startswith('JACKIE_SEARCH_DATABASE_URL=')]
    if len(db_lines) != 1 or '@127.0.0.1:55473/search_' + version[:16] + '?' not in db_lines[0]:
        raise RuntimeError('Preview does not reference the expected immutable database')
    if not active(SEARCH_SERVICE):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1',18768)) == 0: raise RuntimeError('Production search port already occupied')
    try:
        account = pwd.getpwnam('jackieleven-search')
    except KeyError:
        run('useradd','--system','--user-group','--no-create-home','--home-dir','/nonexistent','--shell','/usr/sbin/nologin','jackieleven-search')
        account = pwd.getpwnam('jackieleven-search')
    SECRET_DIR.mkdir(mode=0o755, exist_ok=True)
    replacements = {
        VHOST: (vhost,0o644), WEB_UNIT: (webunit.encode(),0o644),
        SEARCH_UNIT: ((SOURCE/'search/search-production.service').read_text().replace('@RELEASE_ROOT@',str(root)).replace('@MANIFEST@',str(root/'search-manifest.json')).encode(),0o644),
        WEB_ENV: (('JACKIE_SEARCH_URL=http://127.0.0.1:18768\nJACKIE_SEARCH_MANIFEST='+str(root/'search-manifest.json')+'\n').encode(),0o600),
        SEARCH_ENV: ((db_lines[0]+'\nJACKIE_SEARCH_EXTERNAL=1\nJACKIE_DEEPINFRA_API_KEY_FILE='+str(KEY)+'\n').encode(),0o600),
        KEY: (Path('/etc/jackieleven-search-preview/deepinfra-key').read_bytes(),0o600),
        LOCATION: ((SOURCE/'nginx-search-production-location.conf').read_bytes(),0o644),
        LIMITS: ((SOURCE/'nginx-search-production-limits.conf').read_bytes(),0o644),
    }
    if any(p.is_symlink() for p in replacements): raise RuntimeError('Linked configuration refused')
    backup = BACKUPS / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup.mkdir(parents=True,mode=0o700)
    manifest = {'release':str(root),'state':'prepared','search_active':active(SEARCH_SERVICE),
                'search_enabled':subprocess.run(['systemctl','is-enabled','--quiet',SEARCH_SERVICE],capture_output=True).returncode == 0,
                'entries':snapshot([*replacements,CURRENT],backup)}
    write(backup/'transaction.json',json.dumps(manifest,indent=2).encode(),0o600)
    # Self-contained rollback code is retained with the transaction.
    for name in ('update-go-production.py','install-go-production.py'):
        write(backup/name,(SOURCE/name).read_bytes(),0o700)
    if digest(VHOST.read_bytes()) != expected_sha or str(CURRENT.resolve()) != expected_current:
        raise RuntimeError('Production changed during preparation; no configuration changed')
    phase = 'configuration'
    try:
        for p,(data,mode) in replacements.items(): write(p,data,mode)
        os.chown(KEY,account.pw_uid,account.pw_gid)
        run('systemd-analyze','verify',str(SEARCH_UNIT),str(WEB_UNIT))
        run('nginx','-t')
        run('systemctl','daemon-reload')
        phase = 'search startup'
        run('systemctl','restart',SEARCH_SERVICE)
        ready(version)
        semantic = verify_semantic(version)
        phase = 'website activation'
        link_to(CURRENT,root)
        run('systemctl','restart',WEB_SERVICE)
        initial.wait_health()
        run('systemctl','reload','nginx')
        initial.wait_health(tls=True)
        verify_public_search()
        run('systemctl','enable',SEARCH_SERVICE)
        manifest['state'] = 'installed'
        manifest['semantic_check'] = semantic
        write(backup/'transaction.json',json.dumps(manifest,indent=2).encode(),0o600)
    except BaseException:
        try:
            rollback(backup,manifest)
            status = 'previous Go website restored'
        except BaseException:
            status = 'rollback incomplete; use saved transaction'
        raise RuntimeError(f'Deployment failed during {phase}; {status}; backup {backup}') from None
    return {'release':release_id,'backup':str(backup),'content_version':version,'semantic_check':semantic,'url':'https://jackieleven.com'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release'); p.add_argument('--expected-sha'); p.add_argument('--expected-current'); p.add_argument('--rollback',type=Path)
    a = p.parse_args()
    if os.geteuid() != 0: p.error('Root required')
    with open('/run/lock/jackieleven-go-update.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        if a.rollback:
            backup = a.rollback.resolve()
            if backup.parent != BACKUPS: p.error('Invalid backup path')
            manifest = json.loads((backup/'transaction.json').read_text())
            if manifest['state'] == 'rolled-back':
                print('Already rolled back'); return
            if str(CURRENT.resolve()) not in (manifest['release'],manifest['entries'][str(CURRENT)]['link']):
                p.error('A later release is active; refusing stale rollback')
            rollback(backup,manifest)
            print('Previous Go website restored')
        else:
            if not all((a.release,a.expected_sha,a.expected_current)): p.error('Release and both expected preconditions required')
            print(json.dumps(install(a.release,a.expected_sha,a.expected_current)))

if __name__ == '__main__':
    try: main()
    except (Exception, KeyboardInterrupt) as error:
        # Do not print provider, process or environment details containing secrets.
        if isinstance(error,RuntimeError): print(str(error))
        else: print('Deployment failed; inspect the protected server transaction')
        raise SystemExit(1)
