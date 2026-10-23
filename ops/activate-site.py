"""Activate the full site after deploying its release. No secrets in CLI args."""
from pathlib import Path
import json
import shlex
import subprocess
import sys

if sys.argv[1:] != ['--activate']:
    raise SystemExit('Usage: python3 ops/activate-site.py --activate')
root = Path(__file__).resolve().parent.parent
payload = {
    'nginx': (root / 'ops/nginx-site.conf').read_text(),
    'pool': (root / 'ops/php-fpm-site.conf').read_text(),
    'security': (root / 'ops/nginx-security.conf').read_text(),
    'cleanup': (root / 'ops/clean-state.py').read_text(),
    'cleanup_service': (root / 'ops/jackieleven-clean-state.service').read_text(),
    'cleanup_timer': (root / 'ops/jackieleven-clean-state.timer').read_text(),
    'key': (root / '.dev/resend-api-key').read_text().strip(),
}
installer = (root / 'ops/install-site.py').read_text()
result = subprocess.run(
    ['ssh', '-o', 'BatchMode=yes', '-p', '29742', 'root@77.42.46.154',
     'python3 -c ' + shlex.quote(installer)],
    input=json.dumps(payload), text=True,
)
sys.exit(result.returncode)
