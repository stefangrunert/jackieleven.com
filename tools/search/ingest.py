#!/usr/bin/env python3
"""Pinned search export/import. All credential values and provider bodies stay private."""
import argparse
from contextlib import contextmanager, closing
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import json
import os
from pathlib import Path
import sys
from common import atomic_json, canonical, sha
from exporter import Snapshot, export
from provider import DeepInfra, PROFILE, PROFILE_NAME, load_key
from state import State

RETRIEVAL_PROFILE = 'paradedb-unicode-title3-v1'


@contextmanager
def writer_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def identity(corpus, embed):
    profile = PROFILE if embed else 'none'
    version = sha(canonical({'data_version': corpus['data_version'], 'embedding': profile, 'retrieval': RETRIEVAL_PROFILE}))
    return 'build_' + version[:32], version


def manifest_for(corpus, embed):
    build, version = identity(corpus, embed)
    return {'api_version': 'v1', 'build_id': build, 'content_version': version,
            'data_version': corpus['data_version'], 'embedding_profile': PROFILE_NAME if embed else 'none',
            'passage_count': len(corpus['passages']), 'document_count': corpus['document_count']}


def embedding_plan(corpus, state, embed):
    unique = {state.artifact_key(PROFILE, p['text']): p['text'] for p in corpus['passages']} if embed else {}
    missing = {key: text for key, text in unique.items() if state.artifact(key) is None}
    return unique, missing


def embedding_batches(items, provider, batch_size=16, workers=1):
    """Only provider calls run in threads; at most workers batches exist in flight."""
    if not 1 <= workers <= 4:
        raise ValueError('worker_limit')
    batch_size = min(max(batch_size, 1), 16)
    batches = iter(items[i:i+batch_size] for i in range(0, len(items), batch_size))
    executor = ThreadPoolExecutor(max_workers=workers)
    pending = {}
    def submit_one():
        batch = next(batches, None)
        if batch is not None:
            future = executor.submit(provider.embed, [text for key, text in batch])
            pending[future] = batch
    try:
        for _ in range(workers):
            submit_one()
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                batch = pending.pop(future)
                vectors = future.result()
                if len(vectors) != len(batch):
                    raise ValueError('provider_batch_mismatch')
                yield batch, vectors
                # The caller has persisted this result before the replacement is submitted.
                submit_one()
    finally:
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)


def import_corpus(corpus, state, dsn, manifest_path, embed=False, provider=None, batch_size=16, failpoint=None, workers=1):
    import psycopg
    from psycopg.types.json import Jsonb
    manifest = manifest_for(corpus, embed)
    build = manifest['build_id']
    profile = manifest['embedding_profile']
    unique, missing = embedding_plan(corpus, state, embed)
    batch_size = min(max(batch_size, 1), 16)
    with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as db:
        db.execute("SET statement_timeout='120s'")
        db.execute("SET lock_timeout='5s'")
        # One corpus writer across state directories; readers do not acquire this lock.
        db.execute('SELECT pg_advisory_lock(59379124)')
        try:
            db.execute(Path(__file__).with_name('schema.sql').read_text())
            existing = db.execute('SELECT status,content_version FROM search.builds WHERE build_id=%s', (build,)).fetchone()
            if existing and existing[0] == 'ready':
                if existing[1] != manifest['content_version']:
                    raise ValueError('build_identity_collision')
                atomic_json(manifest_path, manifest)
                return {**manifest, 'embedding_calls': 0, 'reused_ready_build': True}
            db.execute('INSERT INTO search.builds(build_id,content_version,data_version,embedding_profile,status) VALUES(%s,%s,%s,%s,\'building\') ON CONFLICT(build_id) DO UPDATE SET status=\'building\'',
                       (build, manifest['content_version'], corpus['data_version'], profile))
            db.execute('INSERT INTO indexer_state.runs(build_id,input_hash,profile,status) VALUES(%s,%s,%s,\'running\') ON CONFLICT(build_id) DO UPDATE SET status=\'running\',attempt=indexer_state.runs.attempt+1,updated_at=now(),error_code=NULL',
                       (build, corpus['data_version'], profile))
            with db.cursor() as cursor:
                cursor.executemany('INSERT INTO indexer_state.run_items(build_id,passage_id,input_hash,artifact_key,status) VALUES(%s,%s,%s,%s,\'pending\') ON CONFLICT(build_id,passage_id) DO UPDATE SET status=\'pending\'',
                                   [(build, p['id'], p['content_hash'], state.artifact_key(PROFILE, p['text']) if embed else None) for p in corpus['passages']])
            calls = 0
            try:
                missing_items = list(sorted(missing.items()))
                if missing_items and provider is None:
                    raise ValueError('provider_required_for_missing_artifacts')
                with closing(embedding_batches(missing_items, provider, batch_size, workers)) as batches:
                    for batch, vectors in batches:
                        calls += 1
                        for (key, text), vector in zip(batch, vectors):
                            artifact = state.save_artifact(key, vector)
                            db.execute('INSERT INTO indexer_state.artifacts(artifact_key,profile,input_hash,sha256,dimensions,local_path) VALUES(%s,%s,%s,%s,1024,%s) ON CONFLICT(artifact_key) DO UPDATE SET sha256=excluded.sha256,local_path=excluded.local_path,validated_at=now()',
                                       (key, profile, sha(text), artifact['sha256'], str(state.artifact_path(key))))
                            db.execute("UPDATE indexer_state.run_items SET status='validated' WHERE build_id=%s AND artifact_key=%s", (build, key))
                        if failpoint:
                            failpoint('after_embedding_batch')
                # A transaction contains the entire membership and ready transition. Failed writes cannot publish a partial build.
                with db.transaction():
                    db.execute('DELETE FROM search.passages WHERE build_id=%s', (build,))
                    db.execute('DELETE FROM search.entities WHERE build_id=%s', (build,))
                    with db.cursor() as cursor:
                        cursor.executemany('INSERT INTO search.entities(build_id,id,data) VALUES(%s,%s,%s)',
                                           [(build, e['id'], Jsonb(e['data'])) for e in corpus['entities']])
                        rows = []
                        for p in corpus['passages']:
                            vector = None
                            if embed:
                                key = state.artifact_key(PROFILE, p['text'])
                                artifact = state.artifact(key)
                                if artifact is None:
                                    raise ValueError('artifact_missing_before_publish')
                                vector = json.dumps(artifact['vector'], separators=(',', ':'), allow_nan=False)
                            rows.append((build, p['id'], p['document_id'], p['title'], p['text'], p['language'], p['source_voice'], p['text_voice'], p['text_kind'], p['year'], p['url_de'], p['url_en'], p['content_hash'], vector, Jsonb(p['metadata'])))
                        cursor.executemany('INSERT INTO search.passages(build_id,id,document_id,title,text,language,source_voice,text_voice,text_kind,year,url_de,url_en,content_hash,embedding,metadata) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::halfvec,%s)', rows)
                    actual = db.execute('SELECT count(*) FROM search.passages WHERE build_id=%s', (build,)).fetchone()[0]
                    if actual != len(corpus['passages']):
                        raise ValueError('membership_count_mismatch')
                    if failpoint:
                        failpoint('before_publish')
                    db.execute("UPDATE indexer_state.run_items SET status='validated' WHERE build_id=%s", (build,))
                    db.execute("UPDATE indexer_state.runs SET status='ready',updated_at=now() WHERE build_id=%s", (build,))
                    db.execute("UPDATE search.builds SET status='ready' WHERE build_id=%s", (build,))
                atomic_json(manifest_path, manifest)
                return {**manifest, 'embedding_calls': calls, 'reused_ready_build': False}
            except BaseException:
                # Do not persist exception text: drivers/provider bodies can contain credentials or source text.
                db.execute("UPDATE search.builds SET status='failed' WHERE build_id=%s AND status<>'ready'", (build,))
                db.execute("UPDATE indexer_state.runs SET status='failed',error_code='ingest_failed',updated_at=now() WHERE build_id=%s AND status<>'ready'", (build,))
                raise
        finally:
            db.execute('SELECT pg_advisory_unlock(59379124)')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--website-root', required=True, type=Path)
    parser.add_argument('--archive-root', required=True, type=Path)
    parser.add_argument('--website-revision', default='a1ea027')
    parser.add_argument('--archive-revision', default='7d353a4')
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--database-url')
    parser.add_argument('--dsn-env', default='JACKIE_SEARCH_DATABASE_URL')
    parser.add_argument('--key-file')
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=1)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--embed', action='store_true')
    group.add_argument('--lexical-only', action='store_true')
    parser.add_argument('--plan', action='store_true', help='Export and print counts; no DB or provider access')
    args = parser.parse_args()
    with writer_lock(args.state_dir):
        state = State(args.state_dir)
        corpus = export(Snapshot(args.website_root, args.website_revision), Snapshot(args.archive_root, args.archive_revision), state)
        atomic_json(args.state_dir / 'exports' / (corpus['data_version'] + '.json'), corpus)
        unique, missing = embedding_plan(corpus, state, args.embed)
        print(json.dumps({'stage': 'plan', 'document_count': corpus['document_count'], 'passage_count': len(corpus['passages']),
                          'entity_count': len(corpus['entities']), 'data_version': corpus['data_version'], 'coverage': corpus.get('coverage', {}),
                          'embedding_profile': PROFILE_NAME if args.embed else 'none', 'embedding_unique_inputs': len(unique),
                          'embedding_cached': len(unique)-len(missing), 'embedding_missing': len(missing),
                          'batch_size': min(max(args.batch_size, 1), 16), 'workers': args.workers}, sort_keys=True), flush=True)
        if args.plan:
            return
        dsn = args.database_url or os.environ.get(args.dsn_env)
        if not dsn:
            raise ValueError('database_url_required')
        provider = DeepInfra(load_key(args.key_file)) if args.embed and missing else None
        result = import_corpus(corpus, state, dsn, args.manifest or args.state_dir / 'manifest.json', args.embed, provider, args.batch_size, workers=args.workers)
        print(json.dumps({'stage': 'ready', **result}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('search_ingest_interrupted', file=sys.stderr)
        sys.exit(130)
    except Exception:
        print('search_ingest_failed (no active manifest was replaced unless the build is ready)', file=sys.stderr)
        sys.exit(1)
