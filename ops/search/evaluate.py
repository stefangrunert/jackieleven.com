#!/usr/bin/env python3
"""Record ranks for the fixed pilot questions; not a relevance benchmark or an answer grader."""
import argparse,json,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--external',action='store_true',help='Also evaluate semantic and hybrid modes through DeepInfra')
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    manifest=json.loads((ROOT/'.dev/runtime/search/manifest.json').read_text())
    corpus=json.loads((ROOT/'.dev/runtime/search/exports'/(manifest['data_version']+'.json')).read_text())
    indexed_documents={p['document_id'] for p in corpus['passages']}
    cases=json.loads((ROOT/'docs/search/phase-1/validation-cases.json').read_text())['cases']
    results=[]
    for case in cases:
        for mode in (['lexical','semantic','hybrid'] if args.external else ['lexical']):
            params={'q':case['query'],'lang':'en' if case.get('query_language')=='en' else 'de','mode':mode,'limit':10}
            req=urllib.request.Request('http://127.0.0.1:8081/v1/search?'+urllib.parse.urlencode(params),headers={'X-Archive-Content-Version':manifest['content_version']})
            with urllib.request.urlopen(req,timeout=12) as response:data=json.loads(response.read(4*1024*1024))
            docs=[h['document_id'] for h in data['hits']]
            ranks=[{'document_id':expectation['document_id'],'in_corpus':expectation['document_id'] in indexed_documents,'expected_top':expectation.get('within_top',10),'actual_rank':docs.index(expectation['document_id'])+1 if expectation['document_id'] in docs else None} for expectation in case.get('expected',{}).get('must_return',[]) if 'document_id' in expectation]
            results.append({'case_id':case['id'],'requested_mode':mode,'used_mode':data['mode'],'degraded':data['degraded'],'duration_ms':data['duration_ms'],'expected_document_ranks':ranks,'top_hits':[{'document_id':h['document_id'],'passage_id':h['id'],'title':h['title'],'text_voice':h['text_voice'],'text_kind':h['text_kind']} for h in data['hits']]})
    output={'status':'observations_not_full_quality_acceptance','content_version':manifest['content_version'],'note':'Ten pilot cases, top 10 passages. Distinct passages/translation variants of one document occupy ranks; exact short within-document duplicates are collapsed; absent expected documents are marked in_corpus=false; statement/entity assertions and negative relevance are not automatically graded. No held-out statistical benchmark. Semantic retrieval may return nearest neighbours even without a relevant answer.','results':results}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'queries':len(results),'degraded':sum(r['degraded'] for r in results),'expected_documents_found':sum(x['actual_rank'] is not None for r in results for x in r['expected_document_ranks']),'expected_document_checks':sum(len(r['expected_document_ranks']) for r in results)}))
if __name__=='__main__':main()
