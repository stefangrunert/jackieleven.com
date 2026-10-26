#!/usr/bin/env python3
"""Restore an immutable search read model and activate the preview search service.
Root-only on Hetzner. The website installer runs afterwards; backups record the
previous service and both environment files for a coordinated rollback.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.request

UNIT=Path('/etc/systemd/system/jackieleven-search-preview.service')
ENV=Path('/etc/jackieleven-search-preview.env')
WEBENV=Path('/etc/jackieleven-go-preview-search.env')
PG='/usr/lib/postgresql/17/bin/'
PSQL=['runuser','-u','jackieleven-search-db','--',PG+'psql','-X','-A','-t','-v','ON_ERROR_STOP=1','-h','/run/jackieleven-search-db','-p','55473','-U','search_admin']
SERVICE='jackieleven-search-preview.service'

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def write(path, data, mode=0o600):
    tmp=path.with_name(path.name+'.next')
    with tmp.open('xb') as f: f.write(data)
    tmp.chmod(mode); tmp.replace(path)

def sql(database, text):
    return run(*PSQL,'-d',database,input=text,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def install(release, dump, digest):
    if os.geteuid()!=0: raise SystemExit('Requires root')
    if not re.fullmatch('[A-Za-z0-9_-]+',release): raise ValueError('Invalid release')
    root=Path('/var/www/jackieleven-go-preview/releases')/release
    for line in (root/'release-manifest.sha256').read_text().splitlines():
        expected,name=line.split('  ',1)
        if name.startswith('/') or any(p in ('','..','.') for p in name.split('/')): raise ValueError('Invalid manifest')
        file=root/name
        if file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest()!=expected: raise ValueError('Release checksum mismatch')
    if hashlib.sha256(dump.read_bytes()).hexdigest()!=digest: raise ValueError('Database checksum mismatch')
    manifest=json.loads((root/'search-manifest.json').read_text())
    version=manifest['content_version']
    if not re.fullmatch('[0-9a-f]{64}',version): raise ValueError('Invalid content version')
    database='search_'+version[:16]
    exists=sql('postgres',"SELECT datname FROM pg_database WHERE datname='"+database+"';").stdout
    if database not in exists:
        sql('postgres','CREATE DATABASE '+database+';')
        try:
            sql(database,'CREATE EXTENSION pg_search CASCADE; CREATE EXTENSION IF NOT EXISTS vector;')
            # stdin avoids exposing the private dump directory to the DB OS account.
            with dump.open('rb') as source:
                run('runuser','-u','jackieleven-search-db','--',PG+'pg_restore','--exit-on-error','--no-owner','--no-acl','-h','/run/jackieleven-search-db','-p','55473','-U','search_admin','-d',database,stdin=source,stdout=subprocess.DEVNULL)
        except Exception:
            # This database was created by this invocation and has never been activated.
            sql('postgres','DROP DATABASE '+database+';')
            raise
    # Permit only this concrete immutable database, never a wildcard.
    hba=Path('/mnt/HC_Volume_107171732/jackieleven-search-preview/pgdata/pg_hba.conf')
    rule='host '+database+' search_reader 127.0.0.1/32 scram-sha-256\n'
    if rule not in hba.read_text():
        with hba.open('a') as f: f.write(rule)
        sql('postgres','SELECT pg_reload_conf();')
    ready=sql(database,"SELECT count(*) FROM search.builds WHERE content_version='"+version+"' AND status='ready';").stdout
    if ready.strip() != '1': raise RuntimeError('Published build missing')
    sql(database,'REVOKE CONNECT ON DATABASE '+database+' FROM PUBLIC; GRANT CONNECT ON DATABASE '+database+' TO search_reader; GRANT USAGE ON SCHEMA search TO search_reader; GRANT SELECT ON ALL TABLES IN SCHEMA search TO search_reader; ANALYZE;')
    backup=Path('/var/backups/jackieleven-search-preview')/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup.mkdir(parents=True,mode=0o700)
    old={p:p.read_bytes() if p.exists() else None for p in (UNIT,ENV,WEBENV)}
    for p,data in old.items():
        if data is not None: (backup/p.name).write_bytes(data); (backup/p.name).chmod(0o600)
    (backup/'deployment.json').write_text(json.dumps({'release':release,'database':database,'version':version,'dump_sha256':digest},indent=2)+'\n')
    env=ENV.read_text()
    env,replacements=re.subn(r'(?m)(^JACKIE_SEARCH_DATABASE_URL=postgresql://[^\n]+@127\.0\.0\.1:55473/)[^?\n]+',lambda m:m[1]+database,env)
    if replacements != 1: raise ValueError('Expected one database URL in private environment')
    unit=(Path(__file__).parent/'search-preview.service').read_text().replace('@RELEASE_ROOT@',str(root)).replace('@MANIFEST@',str(root/'search-manifest.json'))
    was_active=subprocess.run(['systemctl','is-active','--quiet',SERVICE]).returncode==0
    try:
        write(ENV,env.encode())
        write(UNIT,unit.encode(),0o644)
        write(WEBENV,('JACKIE_SEARCH_URL=http://127.0.0.1:18767\nJACKIE_SEARCH_MANIFEST='+str(root/'search-manifest.json')+'\n').encode())
        run('systemd-analyze','verify',str(UNIT))
        run('systemctl','daemon-reload'); run('systemctl','restart',SERVICE)
        for attempt in range(30):
            try:
                with urllib.request.urlopen('http://127.0.0.1:18767/readyz',timeout=3) as response:
                    if response.status==200 and response.headers.get('X-Archive-Content-Version')==version: break
                    raise RuntimeError('Search service reports a different content version')
            except OSError:
                if attempt==29: raise
                time.sleep(.3)
        run('systemctl','enable',SERVICE)
    except Exception:
        for p,data in old.items():
            if data is None: p.unlink(missing_ok=True)
            else: write(p,data,0o644 if p==UNIT else 0o600)
        run('systemctl','daemon-reload')
        run('systemctl','restart' if was_active else 'stop',SERVICE)
        raise
    print(json.dumps({'database':database,'backup':str(backup),'content_version':version}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release',required=True); p.add_argument('--dump',type=Path,required=True);p.add_argument('--sha256',required=True)
    a=p.parse_args(); install(a.release,a.dump,a.sha256)
