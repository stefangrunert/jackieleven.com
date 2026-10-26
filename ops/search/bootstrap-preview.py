#!/usr/bin/env python3
"""Create the isolated Hetzner preview database. Root-only, deliberately one-shot.
Requires verified pg_search 0.26.3 and existing vector 0.8.6 with PostgreSQL 17.
Does not modify/restart existing PostgreSQL clusters. Never prints credentials.
"""
import os
from pathlib import Path
import pwd
import secrets
import subprocess

BASE = Path('/mnt/HC_Volume_107171732/jackieleven-search-preview')
PG = '/usr/lib/postgresql/17/bin/'
DBUSER = 'jackieleven-search-db'
APPUSER = 'jackieleven-search-preview'
SERVICE = 'jackieleven-search-db-preview.service'

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def write(path, text, mode=0o600):
    with path.open('x') as f:
        f.write(text)
    path.chmod(mode)

def main():
    if os.geteuid() != 0:
        raise SystemExit('Requires root on the preview host')
    if not Path('/mnt/HC_Volume_107171732').is_mount():
        raise SystemExit('Expected data volume is not mounted')
    if BASE.exists():
        raise SystemExit('Preview data directory exists; refusing to reinitialize')
    for extension, version in [('vector','0.8.6'), ('pg_search','0.26.3')]:
        control = Path('/usr/share/postgresql/17/extension/'+extension+'.control').read_text()
        if version not in control:
            raise SystemExit('Unexpected extension version: '+extension)
    for name in (DBUSER,APPUSER):
        try: pwd.getpwnam(name)
        except KeyError:
            run('useradd','--system','--user-group','--no-create-home','--home-dir','/nonexistent','--shell','/usr/sbin/nologin',name)
    BASE.mkdir(mode=0o700)
    owner = pwd.getpwnam(DBUSER)
    os.chown(BASE, owner.pw_uid, owner.pw_gid)
    run('runuser','-u',DBUSER,'--',PG+'initdb','-D',str(BASE/'pgdata'),'-U','search_admin','--auth-local=peer','--auth-host=scram-sha-256','--encoding=UTF8','--locale=C.UTF-8',stdout=subprocess.DEVNULL)
    config = BASE/'pgdata/postgresql.conf'
    with config.open('a') as f:
        f.write("""
# Dedicated Jackie Leven preview only.
listen_addresses='127.0.0.1'
port=55473
unix_socket_directories='/run/jackieleven-search-db'
shared_preload_libraries='pg_search'
shared_buffers='64MB'
work_mem='4MB'
maintenance_work_mem='64MB'
max_connections=16
max_parallel_workers_per_gather=0
log_statement='none'
log_min_error_statement='panic'
log_parameter_max_length_on_error=0
logging_collector=off
""")
    (BASE/'pgdata/pg_ident.conf').write_text('jackie_admin '+DBUSER+' search_admin\n')
    (BASE/'pgdata/pg_hba.conf').write_text('local all search_admin peer map=jackie_admin\nhost jackieleven_search search_reader 127.0.0.1/32 scram-sha-256\n')
    unit = Path('/etc/systemd/system')/SERVICE
    write(unit, f"""[Unit]
Description=Isolated Jackie Leven preview PostgreSQL
After=network.target
RequiresMountsFor={BASE}
[Service]
Type=simple
User={DBUSER}
Group={DBUSER}
RuntimeDirectory=jackieleven-search-db
RuntimeDirectoryMode=0700
ExecStart={PG}postgres -D {BASE}/pgdata
KillSignal=SIGINT
TimeoutStopSec=60
Restart=on-failure
RestartSec=5
MemoryMax=1G
CPUQuota=150%
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={BASE} /run/jackieleven-search-db
[Install]
WantedBy=multi-user.target
""",0o644)
    run('systemctl','daemon-reload')
    run('systemctl','enable','--now',SERVICE)
    import time
    for attempt in range(30):
        ready = subprocess.run([PG+'pg_isready','-h','/run/jackieleven-search-db','-p','55473'],stdout=subprocess.DEVNULL)
        if ready.returncode == 0: break
        time.sleep(.2)
    else: raise SystemExit('Database startup failed; inspect dedicated service')
    psql=['runuser','-u',DBUSER,'--',PG+'psql','-X','-v','ON_ERROR_STOP=1','-h','/run/jackieleven-search-db','-p','55473','-U','search_admin']
    run(*psql,'-d','postgres',input='CREATE DATABASE jackieleven_search;\n',text=True,stdout=subprocess.DEVNULL)
    password=secrets.token_hex(32)
    sql="CREATE EXTENSION IF NOT EXISTS pg_search CASCADE; CREATE EXTENSION IF NOT EXISTS vector; CREATE ROLE search_reader LOGIN PASSWORD '"+password+"'; ALTER ROLE search_reader SET default_transaction_read_only=on; ALTER ROLE search_reader SET statement_timeout='2000ms'; REVOKE CONNECT ON DATABASE jackieleven_search FROM PUBLIC; GRANT CONNECT ON DATABASE jackieleven_search TO search_reader;"
    run(*psql,'-d','jackieleven_search',input=sql,text=True,stdout=subprocess.DEVNULL)
    write(Path('/etc/jackieleven-search-preview.env'), 'JACKIE_SEARCH_DATABASE_URL=postgresql://search_reader:'+password+'@127.0.0.1:55473/jackieleven_search?sslmode=disable\nJACKIE_SEARCH_EXTERNAL=1\nJACKIE_DEEPINFRA_API_KEY_FILE=/etc/jackieleven-search-preview/deepinfra-key\n')
    keydir=Path('/etc/jackieleven-search-preview')
    keydir.mkdir(mode=0o750)
    app=pwd.getpwnam(APPUSER)
    os.chown(keydir,0,app.pw_gid)
    print('Isolated database initialized; reader credential saved privately.')

if __name__ == '__main__': main()
