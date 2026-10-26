#!/usr/bin/env python3
"""Bounded local ARM64 smoke pilot. Own resources only; always tears down."""
from pathlib import Path
import hashlib, json, os, shutil, socket, statistics, subprocess, signal, time, urllib.request, zipfile
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
DOCKER = shutil.which('docker') or '/usr/local/bin/docker'
PROJECT = 'jackieleven-search-pilot'
COMPOSE = [DOCKER, 'compose', '-p', PROJECT, '-f', str(ROOT/'compose.yaml')]
RESULTS = ROOT/'results'
RESULTS.mkdir(exist_ok=True)
for marker in ('status.txt','cleanup.txt'):
    (RESULTS/marker).unlink(missing_ok=True)
def interrupted(signum, frame):
    raise SystemExit('Pilot interrupted by signal '+str(signum))
signal.signal(signal.SIGTERM, interrupted)
def call(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)
def capture(args):
    return subprocess.check_output(args, text=True).strip()
def log(name, args):
    with (RESULTS/name).open('w') as f:
        call(args, stdout=f, stderr=subprocess.STDOUT)
def sql(service, file, output):
    log(output, COMPOSE+['exec','-T',service,'psql','-X','-v','ON_ERROR_STOP=1','-U','pilot','-d','pilot','-f','/pilot/'+file])
if os.environ.get('DOCKER_CONTEXT'):
    endpoint = capture([DOCKER,'context','inspect',os.environ['DOCKER_CONTEXT'],'--format','{{.Endpoints.docker.Host}}'])
else:
    endpoint = os.environ.get('DOCKER_HOST') or capture([DOCKER,'context','inspect','--format','{{.Endpoints.docker.Host}}'])
if not endpoint.startswith('unix://'):
    raise SystemExit('Local unix Docker endpoint required; remote daemons are excluded.')
call([DOCKER,'info','--format','{{.OSType}}/{{.Architecture}}'])
for resource in ('container','volume','network'):
    found=capture([DOCKER,resource,'ls','-q','--filter','label=com.docker.compose.project='+PROJECT])
    if found:
        raise SystemExit('Existing pilot '+resource+' resources found; inspect them before running again.')
for port in (55471,55472):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',port))
downloads=ROOT/'downloads'; downloads.mkdir(exist_ok=True)
archive=downloads/'pg-textsearch-v1.5.1-pg17-arm64.zip'
if not archive.exists():
    urllib.request.urlretrieve('https://github.com/timescale/pg_textsearch/releases/download/v1.5.1/'+archive.name, archive)
expected='e65f953e99f47c05dde88a031884cf36ea269bcb62377f554b76ddb4d13fdc3e'
if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
    raise SystemExit('Package checksum mismatch')
with zipfile.ZipFile(archive) as z:
    name='pg-textsearch-postgresql-17_1.5.1-1_arm64.deb'
    (downloads/name).write_bytes(z.read(name))
call(COMPOSE+['config','--quiet'])
log('build.txt',COMPOSE+['build','textsearch'])
started=False
try:
    started=True
    call(COMPOSE+['up','-d'])
    for service in ('parade','textsearch'):
        ready=False
        for attempt in range(30):
            status=subprocess.run(COMPOSE+['exec','-T',service,'pg_isready','-U','pilot','-d','pilot'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if status.returncode==0:
                # initdb's temporary server is socket-only; require TCP readiness too.
                status=subprocess.run(COMPOSE+['exec','-T',service,'pg_isready','-h','127.0.0.1','-U','pilot','-d','pilot'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                if status.returncode==0: ready=True; break
            time.sleep(1)
        if not ready: raise RuntimeError(service+' not ready after 30 seconds')
        call(COMPOSE+['exec','-T',service,'mkdir','-p','/pilot'])
        for path in sorted(ROOT.glob('*.sql')):
            call(COMPOSE+['cp',str(path),service+':/pilot/'+path.name],stdout=subprocess.DEVNULL)
        sql(service,service+'.sql',service+'.txt')
        sql(service,'scale.sql',service+'-scale.txt')
        # Same phrase/filter workload, local socket; warm single client only.
        pgbench=COMPOSE+['exec','-T','-e','PGOPTIONS=-c default_text_search_config=simple -c statement_timeout=10000',service,'pgbench','-U','pilot','-d','pilot','-n','-c','1','-j','1','-f','/pilot/bench-'+service+'.sql']
        log(service+'-warmup.txt',pgbench+['-t','10'])
        log(service+'-pgbench.txt',pgbench+['-t','100','-l','--log-prefix=/pilot/latency'])
        logs=capture(COMPOSE+['exec','-T',service,'sh','-c','cat /pilot/latency.*'])
        (RESULTS/(service+'-latency.txt')).write_text(logs+'\n')
        values=sorted(float(line.split()[2])/1000 for line in logs.splitlines())
        summary={'transactions':len(values),'p50_ms':statistics.median(values),'p95_ms':values[int(len(values)*.95)-1],'max_ms':max(values),'scope':'1000 synthetic rows; 10 warmup + 100 transactions; one local-socket client'}
        (RESULTS/(service+'-latency.json')).write_text(json.dumps(summary,indent=2)+'\n')
    ids=capture(COMPOSE+['ps','-q']).splitlines()
    log('stats.txt',[DOCKER,'stats','--no-stream','--format','{{.Name}} CPU={{.CPUPerc}} Memory={{.MemUsage}} PIDs={{.PIDs}}']+ids)
    log('images.txt',[DOCKER,'image','inspect','paradedb/paradedb:0.26.3-pg17','postgres:17.11-bookworm','--format','{{json .RepoDigests}} Size={{.Size}}'])
    (RESULTS/'status.txt').write_text('PASS: SQL assertions, scaling, warm benchmarks completed.\n')
finally:
    if started:
        try:
            log('container-logs.txt',COMPOSE+['logs','--no-color'])
        finally:
            call(COMPOSE+['down','--volumes','--timeout','10'])
        (RESULTS/'cleanup.txt').write_text('Own containers, network and data volumes removed by compose down --volumes. Downloaded images/packages retained. Docker Desktop left running.\n')
