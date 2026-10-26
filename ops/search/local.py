#!/usr/bin/env python3
"""Manage only the local Jackie Leven search service and isolated database."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.dev/runtime/search'
LABEL = 'com.stefan.jackieleven.search'
AGENT = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
DOMAIN = 'gui/' + str(os.getuid())
BINARY = ROOT / '.dev/bin/jackieleven-search'
MANIFEST = STATE / 'manifest.json'

def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, **kwargs)

def configuration():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    STATE.chmod(0o700)
    envfile = STATE / 'db.env'
    if not envfile.exists():
        envfile.write_text('JACKIE_SEARCH_DB_PASSWORD=' + secrets.token_hex(24) + '\n')
    envfile.chmod(0o600)
    password = envfile.read_text().strip().split('=', 1)[1]
    configfile = STATE / 'local.json'
    if not configfile.exists():
        configfile.write_text(json.dumps({'admin_dsn': 'postgresql://search_admin:' + password + '@127.0.0.1:55473/jackieleven_search?sslmode=disable', 'reader_password': secrets.token_hex(24)}, indent=2) + '\n')
    configfile.chmod(0o600)
    return json.loads(configfile.read_text())

def retain_manifest():
    if not MANIFEST.is_file():
        return
    data = MANIFEST.read_bytes()
    version = json.loads(data)['content_version']
    if len(version) != 64 or any(c not in '0123456789abcdef' for c in version):
        raise SystemExit('Invalid manifest version')
    directory = STATE / 'manifests'
    directory.mkdir(exist_ok=True, mode=0o700)
    target = directory / (version + '.json')
    if not target.exists():
        with target.open('xb') as f:
            f.write(data)
        target.chmod(0o600)

def compose(*args):
    # Explicit context prevents inherited DOCKER_HOST/CONTEXT from targeting another daemon.
    env = os.environ.copy()
    env.pop('DOCKER_HOST', None)
    env.pop('DOCKER_CONTEXT', None)
    cmd = ['docker', '--context', 'desktop-linux', 'compose', '-p', 'jackieleven-search-dev', '--env-file', str(STATE / 'db.env'), '-f', str(ROOT / 'ops/search/compose.yaml'), *args]
    return run(cmd, env=env)

def build(website=False):
    global BINARY
    if website:
        BINARY = ROOT / '.dev/bin/jackieleven-search-test'
    BINARY.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='jackieleven-search-', dir=BINARY.parent)
    os.close(fd)
    try:
        run(['go', 'build', '-trimpath', '-o', name, './cmd/jackieleven' if website else './cmd/jackieleven-search'], cwd=ROOT)
        os.chmod(name, 0o755)
        os.replace(name, BINARY)
    finally:
        Path(name).unlink(missing_ok=True)

def loaded():
    return subprocess.run(['launchctl', 'print', DOMAIN + '/' + LABEL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def stop():
    if loaded():
        run(['launchctl', 'bootout', DOMAIN + '/' + LABEL])

def install(website=False):
    if not MANIFEST.is_file():
        raise SystemExit('Import and publish a local manifest before installing the search service.')
    build(website)
    logs = ROOT / '.dev/logs'
    logs.mkdir(parents=True, exist_ok=True)
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    config = {'Label': LABEL, 'ProgramArguments': [sys.executable, str(Path(__file__).resolve()), 'serve-test' if website else 'serve'], 'WorkingDirectory': str(ROOT), 'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 5, 'ExitTimeOut': 15, 'StandardOutPath': str(logs/('search-test.out.log' if website else 'search.out.log')), 'StandardErrorPath': str(logs/('search-test.err.log' if website else 'search.err.log'))}
    stop()
    with tempfile.NamedTemporaryFile(dir=AGENT.parent, delete=False) as f:
        temporary = Path(f.name)
        plistlib.dump(config, f)
    try:
        temporary.chmod(0o600)
        temporary.replace(AGENT)
    finally:
        temporary.unlink(missing_ok=True)
    run(['plutil', '-lint', str(AGENT)])
    run(['launchctl', 'enable', DOMAIN + '/' + LABEL])
    run(['launchctl', 'bootstrap', DOMAIN, str(AGENT)])
    endpoint = 'http://127.0.0.1:8082/de/suche-test' if website else 'http://127.0.0.1:8081/healthz'
    for attempt in range(50):
        try:
            with urllib.request.urlopen(endpoint, timeout=1) as response:
                if response.status == 200:
                    print('Local process reachable: ' + endpoint)
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(.2)
    raise SystemExit('Local process did not start; inspect its .dev/logs/search*.err.log.')

def grant_reader(config):
    # Generated password is hexadecimal, never user-provided SQL; pass only on stdin.
    password = config['reader_password']
    if not password or any(c not in '0123456789abcdef' for c in password):
        raise SystemExit('Invalid local reader credential format')
    sql = """DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='search_reader') THEN CREATE ROLE search_reader LOGIN; END IF; END $$;
ALTER ROLE search_reader PASSWORD '%s';
GRANT CONNECT ON DATABASE jackieleven_search TO search_reader;
GRANT USAGE ON SCHEMA search TO search_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA search TO search_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE search_admin IN SCHEMA search GRANT SELECT ON TABLES TO search_reader;
ALTER ROLE search_reader SET statement_timeout='2000ms';
ALTER ROLE search_reader SET default_transaction_read_only=on;
""" % password
    env = os.environ.copy()
    env.pop('DOCKER_HOST', None); env.pop('DOCKER_CONTEXT', None)
    run(['docker', '--context', 'desktop-linux', 'exec', '-i', 'jackieleven-search-dev-postgres-1', 'psql', '-X', '-v', 'ON_ERROR_STOP=1', '-U', 'search_admin', '-d', 'jackieleven_search'], input=sql.encode(), stdout=subprocess.DEVNULL, env=env)
    print('Read-only search role configured; credentials not printed.')

def serve(config):
    env = os.environ.copy()
    env['JACKIE_SEARCH_DATABASE_URL'] = 'postgresql://search_reader:' + config['reader_password'] + '@127.0.0.1:55473/jackieleven_search?sslmode=disable'
    env['JACKIE_DEEPINFRA_API_KEY_FILE'] = str(ROOT / '.dev/deepinfra-api-key')
    env['JACKIE_SEARCH_EXTERNAL'] = '1'
    os.execve(BINARY, [str(BINARY), '-listen', '127.0.0.1:8081', '-manifest', str(MANIFEST), '-mcp'], env)

def serve_test():
    env = os.environ.copy()
    # The independent preview does not inherit live contact credentials.
    for key in ('JACKIE_RESEND_API_KEY', 'JACKIE_TURNSTILE_SITEKEY', 'JACKIE_TURNSTILE_SECRET'):
        env.pop(key, None)
    env['JACKIE_CONTACT_STATE_DIR'] = str(STATE / 'test-contact')
    env['JACKIE_SEARCH_URL'] = 'http://127.0.0.1:8081'
    env['JACKIE_SEARCH_MANIFEST'] = str(MANIFEST)
    binary = ROOT / '.dev/bin/jackieleven-search-test'
    os.execve(binary, [str(binary), '-listen', '127.0.0.1:8082', '-root', str(ROOT)], env)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['db-up','db-stop','build','grant-reader','install','restart','stop','status','serve','install-test','stop-test','serve-test','index'])
    parser.add_argument('--website-revision', help='Explicit content Git revision for a new index snapshot')
    parser.add_argument('--archive-revision', help='Explicit archive Git revision for a new index snapshot')
    parser.add_argument('--workers', type=int, choices=range(1,5), default=4, help='Bounded embedding batches in flight')
    parser.add_argument('--plan', action='store_true', help='Preview index counts without DB/provider calls')
    parser.add_argument('--lexical-only', action='store_true', help='Build a snapshot without embeddings')
    args=parser.parse_args()
    if args.action in ('install-test', 'stop-test', 'serve-test'):
        LABEL = 'com.stefan.jackieleven.search-test'
        AGENT = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
    config=configuration()
    if args.action=='index':
        env = os.environ.copy()
        env['JACKIE_SEARCH_DATABASE_URL'] = config['admin_dsn']
        env['JACKIE_DEEPINFRA_API_KEY_FILE'] = str(ROOT / '.dev/deepinfra-api-key')
        env['PYTHONUNBUFFERED'] = '1'
        command = [str(STATE / 'venv/bin/python'), str(ROOT / 'tools/search/ingest.py'),
                   '--website-root', str(ROOT), '--archive-root', str(ROOT.parent / 'jackieleven-archive'),
                   '--state-dir', str(STATE), '--lexical-only' if args.lexical_only else '--embed',
                   '--workers', str(args.workers)]
        for name in ('website_revision', 'archive_revision'):
            value = getattr(args, name)
            if value: command.extend(['--' + name.replace('_', '-'), value])
        if args.plan: command.append('--plan')
        retain_manifest()
        run(command, env=env, cwd=ROOT)
        retain_manifest()
    elif args.action=='db-up': compose('up','-d','--wait')
    elif args.action=='db-stop': compose('stop')
    elif args.action=='build': build()
    elif args.action=='grant-reader': grant_reader(config)
    elif args.action in ('install','restart'): install()
    elif args.action in ('stop','stop-test'): stop()
    elif args.action=='install-test': install(website=True)
    elif args.action=='serve-test': serve_test()
    elif args.action=='serve': serve(config)
    elif args.action=='status':
        compose('ps')
        run(['launchctl','print',DOMAIN+'/'+LABEL])
