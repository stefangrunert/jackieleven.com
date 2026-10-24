"""Run as root on the existing host, receiving configuration and key on stdin.

Only changes this site's PHP pool/vhost, named security variables and cleanup timer.
Backs up and restores configuration if
validation or origin smoke checks fail. Never logs the Resend key.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import ipaddress
import json
import os
import pwd
import re
import subprocess
import sys
import time


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def origin(path):
    return run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20',
                '--resolve', 'jackieleven.com:443:127.0.0.1',
                'https://jackieleven.com' + path], capture_output=True).stdout


payload = json.load(sys.stdin)
key = payload['key'].strip()
if not re.fullmatch(r're_[A-Za-z0-9_-]+', key):
    raise SystemExit('Invalid Resend key format')
pool = payload['pool'].replace('@RESEND_API_KEY@', key)
for name in ('sitekey', 'secret'):
    value = payload['turnstile_' + name]
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,100}', value):
        raise SystemExit('Invalid Turnstile credential format')
    # Test credentials must never reach the public production pool.
    if value.startswith(('1x', '2x', '3x')):
        raise SystemExit('Turnstile test credentials are not allowed in production')
    pool = pool.replace('@TURNSTILE_' + name.upper() + '@', value)
nginx = payload['nginx']
if 'server_name jackieleven.com' not in nginx or '[jackieleven]' not in pool:
    raise SystemExit('Wrong site configuration')
if not Path('/var/www/jackieleven/site-current/public/index.php').is_file():
    raise SystemExit('Deploy a complete PHP release first')

# Only trust visitor-address headers received from Cloudflare's published networks.
with urlopen('https://api.cloudflare.com/client/v4/ips', timeout=20) as response:
    published = json.load(response)
if published.get('success') is not True:
    raise SystemExit('Cloudflare network lookup failed')
networks = [str(ipaddress.ip_network(net)) for family in ('ipv4_cidrs', 'ipv6_cidrs') for net in published['result'][family]]
if len(networks) < 10:
    raise SystemExit('Incomplete Cloudflare network list')
realip = ''.join('set_real_ip_from ' + net + ';\n' for net in networks) + 'real_ip_header CF-Connecting-IP;\n'
security = payload['security'].replace('@CLOUDFLARE_NETWORKS@', '\n    '.join(net + ' 1;' for net in networks))

try:
    account = pwd.getpwnam('jackieleven')
except KeyError:
    run(['useradd', '--system', '--user-group', '--home-dir', '/var/lib/jackieleven', '--shell', '/usr/sbin/nologin', 'jackieleven'])
    account = pwd.getpwnam('jackieleven')
for name in ('', 'sessions', 'contact'):
    directory = Path('/var/lib/jackieleven') / name
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chown(directory, account.pw_uid, account.pw_gid)
    directory.chmod(0o700)

config = Path('/etc/nginx/sites-available/jackieleven.com')
enabled = Path('/etc/nginx/sites-enabled/jackieleven.com')
if not enabled.is_symlink() or enabled.resolve() != config:
    raise SystemExit('Expected existing Jackie Leven vhost symlink')
changes = {config: (nginx, 0o644),
           Path('/etc/nginx/jackieleven-cloudflare.conf'): (realip, 0o644),
           Path('/etc/nginx/conf.d/jackieleven-security.conf'): (security, 0o644),
           Path('/etc/php/8.3/fpm/pool.d/jackieleven.conf'): (pool, 0o600),
           Path('/usr/local/libexec/jackieleven-clean-state.py'): (payload['cleanup'], 0o644),
           Path('/etc/systemd/system/jackieleven-clean-state.service'): (payload['cleanup_service'], 0o644),
           Path('/etc/systemd/system/jackieleven-clean-state.timer'): (payload['cleanup_timer'], 0o644)}
timer = 'jackieleven-clean-state.timer'
timer_enabled = subprocess.run(['systemctl', 'is-enabled', '--quiet', timer]).returncode == 0
timer_active = subprocess.run(['systemctl', 'is-active', '--quiet', timer]).returncode == 0
backup = Path('/var/backups/jackieleven-site') / datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
backup.mkdir(parents=True, mode=0o700)
previous = {}
for path in changes:
    previous[path] = (path.read_bytes(), path.stat().st_mode & 0o777) if path.exists() else None
    if previous[path] is not None:
        saved = backup / path.name
        saved.write_bytes(previous[path][0])
        saved.chmod(0o600)
(backup / 'manifest.json').write_text(json.dumps({str(p): p.name if value else None for p, value in previous.items()}, indent=2))
try:
    for path, (content, mode) in changes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(mode=mode, exist_ok=True)
        path.chmod(mode)
        path.write_text(content)
    # Do not use -tt: a full config dump would expose env secrets.
    run(['php-fpm8.3', '-t'], capture_output=True)
    run(['nginx', '-t'], capture_output=True)
    run(['systemd-analyze', 'verify', '/etc/systemd/system/jackieleven-clean-state.service',
         '/etc/systemd/system/jackieleven-clean-state.timer'], capture_output=True)
    run(['systemctl', 'reload', 'php8.3-fpm'])
    for _ in range(30):
        if Path('/run/php/jackieleven.sock').exists():
            break
        time.sleep(0.2)
    else:
        raise RuntimeError('Site PHP socket unavailable')
    run(['systemctl', 'reload', 'nginx'])
    for lang in ('de', 'en'):
        for attempt in range(10):
            try:
                body = origin('/' + lang + '/')
                if ('<html lang="' + lang + '">').encode() in body and b'noindex' not in body:
                    break
            except subprocess.CalledProcessError:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError('Homepage smoke check failed')
    contact = origin('/en/contribute')
    if b'name="token"' not in contact or b'type="submit" disabled' in contact:
        raise RuntimeError('Contact form is not ready')
    if b'Disallow: /' in origin('/robots.txt') or b'<urlset' not in origin('/sitemap.xml'):
        raise RuntimeError('Indexing smoke check failed')
    # Verify Cloudflare still reaches the vhost after the peer-address gate.
    with urlopen(Request('https://jackieleven.com/en/', headers={
        'User-Agent': 'JackieLevenDeploymentCheck/1.0',
    }), timeout=20) as response:
        if response.status != 200 or response.headers.get('X-Frame-Options') != 'DENY':
            raise RuntimeError('Public security-header check failed')
        if b'home-vers' not in response.read():
            raise RuntimeError('Public homepage check failed')
    run(['systemctl', 'daemon-reload'])
    run(['systemctl', 'enable', '--now', timer], capture_output=True)
    run(['systemctl', 'start', 'jackieleven-clean-state.service'])
    run(['systemctl', 'is-active', '--quiet', timer])
except Exception:
    if not timer_active:
        subprocess.run(['systemctl', 'stop', timer], capture_output=True)
    if not timer_enabled:
        subprocess.run(['systemctl', 'disable', timer], capture_output=True)
    for path, old in previous.items():
        if old is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(old[0])
            path.chmod(old[1])
    run(['systemctl', 'daemon-reload'])
    if timer_active:
        run(['systemctl', 'restart', timer])
    run(['php-fpm8.3', '-t'], capture_output=True)
    run(['nginx', '-t'], capture_output=True)
    run(['systemctl', 'reload', 'php8.3-fpm'])
    run(['systemctl', 'reload', 'nginx'])
    raise SystemExit('Activation failed; previous site configuration restored. Secret values suppressed.')
print('Full site active; origin checks passed. Configuration backup: ' + str(backup))
