#!/usr/bin/env python3
"""Test isolated local failure paths, without stopping the running search pair."""
import json, os, subprocess, time, urllib.request, urllib.error
from contextlib import contextmanager
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STATE=ROOT/'.dev/runtime/search'

def get(url,headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=10) as r:return r.status,r.read()
    except urllib.error.HTTPError as r:return r.code,r.read()

@contextmanager
def running(cmd,env,origin):
    process=subprocess.Popen(cmd,env=env,cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for attempt in range(50):
            if process.poll() is not None:raise RuntimeError('test process exited')
            try:get(origin);break
            except urllib.error.URLError:time.sleep(.1)
        else:raise RuntimeError('test process did not become reachable')
        yield
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()

def main():
    config=json.loads((STATE/'local.json').read_text())
    manifest=json.loads((STATE/'manifest.json').read_text())
    env=os.environ.copy()
    for key in ('JACKIE_DEEPINFRA_API_KEY','JACKIE_DEEPINFRA_API_KEY_FILE','JACKIE_RESEND_API_KEY','JACKIE_TURNSTILE_SITEKEY','JACKIE_TURNSTILE_SECRET'):env.pop(key,None)
    env['JACKIE_SEARCH_EXTERNAL']='0'
    env['JACKIE_SEARCH_DATABASE_URL']='postgresql://search_reader:'+config['reader_password']+'@127.0.0.1:55473/jackieleven_search?sslmode=disable'
    service=[str(ROOT/'.dev/bin/jackieleven-search'),'-listen','127.0.0.1:18083','-manifest',str(STATE/'manifest.json')]
    origin='http://127.0.0.1:18083'
    headers={'X-Archive-Content-Version':manifest['content_version']}
    with running(service,env,origin+'/healthz'):
        status,body=get(origin+'/v1/search?q=Leven&lang=de&mode=hybrid',headers)
        data=json.loads(body)
        assert status==200 and data['mode']=='lexical' and data['degraded'] and data['reason']=='external_disabled' and data['hits']
    env['JACKIE_SEARCH_DATABASE_URL']='postgresql://search_reader:unused@127.0.0.1:1/jackieleven_search?sslmode=disable&connect_timeout=1'
    with running(service,env,origin+'/healthz'):
        assert get(origin+'/healthz')[0]==200
        assert get(origin+'/readyz')[0]==503
        status,body=get(origin+'/v1/search?q=Leven&lang=de&mode=lexical',headers)
        assert status==503 and b'postgresql' not in body
    env['JACKIE_SEARCH_URL']=origin
    env['JACKIE_SEARCH_MANIFEST']=str(STATE/'manifest.json')
    env['JACKIE_CONTACT_STATE_DIR']=str(STATE/'failure-test-contact')
    site=[str(ROOT/'.dev/bin/jackieleven-search-test'),'-listen','127.0.0.1:18082','-root',str(ROOT)]
    with running(site,env,'http://127.0.0.1:18082/de/'):
        assert get('http://127.0.0.1:18082/de/suche-test?q=Leven&mode=lexical')[0]==503
        assert get('http://127.0.0.1:18082/de/')[0]==200
        assert get('http://127.0.0.1:18082/de/mitmachen')[0]==200
    print(json.dumps({'status':'passed','checks':['provider-disabled lexical fallback','database failure distinct from no hits','health/readiness distinction','search service failure isolated from ordinary and contact pages']}))
if __name__=='__main__':main()
