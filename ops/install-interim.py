"""Install only the Jackie Leven vhost, retaining a backup and validating nginx."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

config = Path('/etc/nginx/sites-available/jackieleven.com')
enabled = Path('/etc/nginx/sites-enabled/jackieleven.com')
previous = config.read_bytes() if config.exists() else None
was_enabled = enabled.is_symlink()
if enabled.exists() and not was_enabled:
    raise SystemExit('Expected a symlink for the enabled vhost')
if was_enabled and enabled.resolve() != config:
    raise SystemExit('Existing vhost symlink points elsewhere')
incoming = sys.stdin.read()
if 'server_name jackieleven.com' not in incoming:
    raise SystemExit('Jackie Leven server name is missing')
backup = Path('/var/backups/jackieleven-nginx') / datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
backup.mkdir(parents=True)
if previous is not None:
    (backup / 'jackieleven.com.conf').write_bytes(previous)
try:
    config.write_text(incoming)
    if not was_enabled:
        enabled.symlink_to(config)
    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
except Exception:
    if previous is None:
        config.unlink(missing_ok=True)
    else:
        config.write_bytes(previous)
    if not was_enabled:
        enabled.unlink(missing_ok=True)
    subprocess.run(['nginx', '-t'], check=True)
    raise
print(f'Jackie Leven vhost installed; backup: {backup}')
