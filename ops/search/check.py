#!/usr/bin/env python3
"""Bounded HTTP acceptance checks against the running LOCAL search pair."""
import argparse,json,re,urllib.request,urllib.error,urllib.parse
from pathlib import Path

def request(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=12) as r:
            return r.status,dict(r.headers),r.read(2_000_001)
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers),e.read(2_000_001)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--service',default='http://127.0.0.1:8081')
    ap.add_argument('--website',default='http://127.0.0.1:8082')
    ap.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parents[2]/'.dev/runtime/search/manifest.json')
    ap.add_argument('--external',action='store_true',help='also run genuine semantic/hybrid queries')
    args=ap.parse_args()
    for u in [args.service,args.website]:
        v=urllib.parse.urlsplit(u)
        if v.scheme!='http' or v.hostname not in ('127.0.0.1','localhost','::1'):raise SystemExit('Only loopback HTTP targets allowed')
    manifest=json.loads(args.manifest.read_text())
    headers={'X-Archive-Content-Version':manifest['content_version']}
    passed=[]
    def check(ok,label):
        if not ok:raise RuntimeError('Failed: '+label)
        passed.append(label)
    def search(q,**extra):
        status,h,body=request(args.service+'/v1/search?'+urllib.parse.urlencode({'q':q,'lang':'de','mode':'lexical','limit':10,**extra}),headers)
        check(status==200,'search HTTP success')
        data=json.loads(body)
        check(data['content_version']==manifest['content_version'],'search snapshot matches')
        return data
    for path in ['/healthz','/readyz']:
        status,h,b=request(args.service+path);check(status==200,path)
    status,h,b=request(args.service+'/v1/search?q=Leven');check(status==409,'missing version rejected')
    status,h,b=request(args.service+'/v1/search?q=Leven',{'X-Archive-Content-Version':'wrong-snapshot'})
    check(status==409,'mismatched version rejected')
    status,h,b=request(args.service+'/v1/search?q=x&limit=51',headers);check(status==400,'excessive result limit rejected')
    status,h,b=request(args.service+'/v1/passages?id=nonexistent-check-id&lang=de',headers);check(status==404,'unknown passage rejected')
    data=search('Jackie Leven')
    check(bool(data['hits']),'lexical hits')
    hit=data['hits'][0]
    check(all(k in hit for k in ['id','document_id','source_voice','text_voice','text_kind']),'provenance fields')
    status,h,b=request(args.service+'/v1/passages?'+urllib.parse.urlencode({'id':hit['id'],'lang':'de'}),headers)
    check(status==200,'exact passage fetch')
    passage=json.loads(b)['passage'];check(bool(passage['text']),'passage text exists')
    empty=search('zxqvnonexistentvalidationtoken209483')
    check(not empty['hits'],'true zero-hit query')
    filtered=search('Leven',voice='editorial')
    check(all(h['text_voice']=='editorial' for h in filtered['hits']),'text voice filter')
    for language,path in [('de','/de/suche-test'),('en','/en/search-test')]:
        status,h,b=request(args.website+path+'?'+urllib.parse.urlencode({'q':'Leven','mode':'lexical'}))
        check(status==200,language+' SSR search')
        check(b'Leven' in b,language+' SSR results')
        check('no-store' in h.get('Cache-Control',''),language+' no cache')
        check('noindex' in h.get('X-Robots-Tag',''),language+' no indexing')
        check(h.get('Referrer-Policy')=='no-referrer',language+' no referrer')
    status,h,b=request(args.website+'/de/suche/textstelle?'+urllib.parse.urlencode({'id':hit['id']}))
    check(status==200 and b'Leven' in b,'website exact passage reader')
    status,h,b=request(args.website+'/de/');check(status==200,'ordinary page remains available')
    if args.external:
        for mode in ['semantic','hybrid']:
            data=search('Norwegen',mode=mode)
            check(bool(data['hits']) and data['mode']==mode and not data.get('degraded',False),'genuine '+mode+' retrieval')
        data=search('Norwegen',mode='hybrid',rerank=1,limit=3)
        check(data.get('reranked') is True and not data.get('degraded',False),'genuine reranking')
    print(json.dumps({'status':'passed','checks':len(passed),'external':args.external,'content_version':manifest['content_version']},indent=2))
if __name__=='__main__': main()
