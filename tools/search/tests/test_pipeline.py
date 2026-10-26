import copy
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import canonical, sha
from exporter import chunks, column_text, inline, Snapshot, export
import ingest
from provider import DeepInfra, normalize, ProviderError, PROFILE
from state import State


def passage(text, index=0):
    return {'document_id': 'private/document/test', 'title': 'Fixture', 'text': text,
            'language': 'en', 'source_voice': 'third_party', 'text_voice': 'editorial',
            'text_kind': 'summary', 'year': 1997, 'url_de': '/de/stimmen/test',
            'url_en': '/en/voices/test', 'content_hash': sha(text), 'metadata': {}, '_family': 'summary:en'}


def corpus(state, texts):
    values = state.assign([passage(text, i) for i, text in enumerate(texts)])
    data = {'passages': values, 'entities': [{'id': 'event/test', 'data': {
        'id': 'event/test', 'time': [{'edtf_value': '1997-04-13'},
        {'edtf_value': '[1997-04-05,1997-04-06,1997-04-13]', 'certainty': 'uncertain'}]}}],
        'document_count': 1}
    data['data_version'] = sha(canonical(data))
    return data


class RegistryTests(unittest.TestCase):
    def test_repeat_move_correction_delete_and_restore(self):
        with tempfile.TemporaryDirectory() as root:
            state = State(root)
            first = corpus(state, ['Alpha', 'Bravo', 'Charlie'])
            ids = {p['text']: p['id'] for p in first['passages']}
            self.assertEqual(first, corpus(state, ['Alpha', 'Bravo', 'Charlie']))
            moved = corpus(state, ['Inserted', 'Bravo', 'Alpha', 'Charlie'])
            for p in moved['passages']:
                if p['text'] in ids:
                    self.assertEqual(p['id'], ids[p['text']])
            edited = corpus(state, ['Inserted', 'Bravo corrected', 'Alpha', 'Charlie'])
            self.assertEqual(next(p['id'] for p in edited['passages'] if p['text'] == 'Bravo corrected'), ids['Bravo'])
            remaining = corpus(state, ['Alpha'])
            self.assertEqual(len(remaining['passages']), 1)
            self.assertGreater(state.db.execute('SELECT count(*) FROM passages WHERE active=0').fetchone()[0], 0)
            restored = corpus(state, ['Alpha', 'Charlie'])
            self.assertEqual(next(p['id'] for p in restored['passages'] if p['text'] == 'Charlie'), ids['Charlie'])

    def test_artifact_integrity_and_profile_separation(self):
        with tempfile.TemporaryDirectory() as root:
            state = State(root)
            key = state.artifact_key(PROFILE, 'fixture')
            vector = normalize([1.0]*4096)
            state.save_artifact(key, vector)
            self.assertIsNotNone(state.artifact(key))
            self.assertNotEqual(key, state.artifact_key({**PROFILE, 'id': 'changed'}, 'fixture'))
            value = json.loads(state.artifact_path(key).read_text())
            value['vector'][0] += 1
            state.artifact_path(key).write_text(json.dumps(value))
            self.assertIsNone(state.artifact(key))

    def test_bounded_chunks_preserve_words(self):
        text = ('A sentence about the show. ' * 500).strip()
        result = list(chunks(text))
        self.assertTrue(all(0 < len(p) <= 2400 for p in result))
        self.assertEqual(' '.join(text.split()), ' '.join(' '.join(result).split()))
        self.assertEqual('x'*5001, ''.join(chunks('x'*5001)))

    def test_text_adapters(self):
        self.assertEqual(inline('The **great** [show](https://example.org) and *voice*.'), 'The great show and voice.')
        self.assertEqual(inline('*Shining Brother\nShining Sister*'), 'Shining Brother\nShining Sister')
        raw = '---\ntitel: "An original…"\nautor: "Jackie Leven"\ndatum: "2009-12"\n---\n\n# Heading\n\nActual narrative.\n'
        meta, art, text = column_text(raw, '2009-12_blog_title.md')
        self.assertEqual(text, 'Actual narrative.')
        self.assertEqual(meta['autor'], 'Jackie Leven')


class ProviderTests(unittest.TestCase):
    def test_reorders_and_normalizes(self):
        body = json.dumps({'data': [{'index': 1, 'embedding': [2.0]*4096}, {'index': 0, 'embedding': [1.0]*4096}]}).encode()
        requests = []
        def opener(request, timeout):
            requests.append(request)
            return io.BytesIO(body)
        vectors = DeepInfra('test-fixture-key', opener=opener).embed(['one', 'two'])
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 1024)
        self.assertAlmostEqual(sum(x*x for x in vectors[0]), 1)
        request = json.loads(requests[0].data)
        self.assertEqual(request['input'], ['one', 'two'])
        self.assertNotIn('dimensions', request)

    def test_rejects_bad_vectors_and_duplicate_indexes(self):
        for vector in ([0.0]*4096, [1.0]*1024, [float('nan')]*4096):
            with self.assertRaises(ProviderError): normalize(vector)
        body = json.dumps({'data': [{'index': 0, 'embedding': [1.0]*4096}, {'index': 0, 'embedding': [1.0]*4096}]}).encode()
        with self.assertRaises(ProviderError):
            DeepInfra('fixture', opener=lambda *a, **k: io.BytesIO(body)).embed(['a', 'b'])

    def test_retries_are_bounded_and_http_body_not_disclosed(self):
        calls = []
        def opener(*args, **kwargs):
            calls.append(1)
            raise urllib.error.HTTPError('https://example.org', 429, 'secret provider body', {}, io.BytesIO(b'secret'))
        with self.assertRaisesRegex(ProviderError, '^provider_http_error$'):
            DeepInfra('fixture', opener=opener, sleep=lambda t: None).embed(['fixture'])
        self.assertEqual(len(calls), 3)
        with self.assertRaises(ProviderError):
            DeepInfra('fixture').embed(['x'*2401])


class MockProvider:
    def __init__(self):
        self.calls = []
    def embed(self, texts):
        self.calls.append(list(texts))
        return [normalize([1.0]*4096) for _ in texts]


@unittest.skipUnless(os.environ.get('SEARCH_TEST_DSN'), 'SEARCH_TEST_DSN required for dedicated local PostgreSQL')
class PostgresTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.tmp = tempfile.TemporaryDirectory()
        self.state = State(self.tmp.name)
        self.manifest = Path(self.tmp.name) / 'manifest.json'
        self.dsn = os.environ['SEARCH_TEST_DSN']
        self.prefix = 'test_' + uuid.uuid4().hex
        self.salt = uuid.uuid4().hex
        self.db = psycopg.connect(self.dsn, autocommit=True)
        original = ingest.identity
        self.identities = []
        def test_identity(corpus, embed):
            build, version = original(corpus, embed)
            value = (self.prefix + '_' + version[:12], sha(self.prefix + version))
            self.identities.append(value[0])
            return value
        self.patch = patch('ingest.identity', side_effect=test_identity)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        for build in set(self.identities):
            self.db.execute('DELETE FROM indexer_state.run_items WHERE build_id=%s', (build,))
            self.db.execute('DELETE FROM indexer_state.runs WHERE build_id=%s', (build,))
            self.db.execute('DELETE FROM search.passages WHERE build_id=%s', (build,))
            self.db.execute('DELETE FROM search.entities WHERE build_id=%s', (build,))
            self.db.execute('DELETE FROM search.builds WHERE build_id=%s', (build,))
        self.db.execute('DELETE FROM indexer_state.artifacts WHERE local_path LIKE %s', (self.tmp.name + '/%',))
        self.db.close()
        self.state.db.close()
        self.tmp.cleanup()

    def run_import(self, data, provider, **kwargs):
        return ingest.import_corpus(data, self.state, self.dsn, self.manifest, True, provider, **kwargs)

    def test_repeat_edit_delete_preserves_old_builds_and_graph(self):
        provider = MockProvider()
        first = corpus(self.state, [self.salt + ' first', self.salt + ' second'])
        result = self.run_import(first, provider)
        self.assertEqual(sum(map(len, provider.calls)), 2)
        self.run_import(first, provider)
        self.assertEqual(sum(map(len, provider.calls)), 2)
        edited = corpus(self.state, [self.salt + ' first corrected', self.salt + ' second'])
        second = self.run_import(edited, provider)
        self.assertEqual(sum(map(len, provider.calls)), 3)
        removed = corpus(self.state, [self.salt + ' second'])
        final = self.run_import(removed, provider)
        self.assertEqual(sum(map(len, provider.calls)), 3)
        for build, count in [(result['build_id'], 2), (second['build_id'], 2), (final['build_id'], 1)]:
            self.assertEqual(self.db.execute('SELECT count(*) FROM search.passages WHERE build_id=%s', (build,)).fetchone()[0], count)
        graph = self.db.execute('SELECT data FROM search.entities WHERE build_id=%s', (final['build_id'],)).fetchone()[0]
        self.assertEqual(len(graph['time']), 2)
        self.assertEqual(graph['time'][1]['certainty'], 'uncertain')

    def test_resume_reuses_completed_batch_and_failed_build_never_publishes(self):
        provider = MockProvider()
        baseline = self.run_import(corpus(self.state, [self.salt + ' baseline']), provider)
        previous = self.manifest.read_bytes()
        data = corpus(self.state, [self.salt + ' new one', self.salt + ' new two'])
        def fail(stage):
            if stage == 'after_embedding_batch': raise RuntimeError('injected interruption')
        with self.assertRaises(RuntimeError): self.run_import(data, provider, batch_size=1, failpoint=fail)
        self.assertEqual(self.manifest.read_bytes(), previous)
        before_resume = sum(map(len, provider.calls))
        result = self.run_import(data, provider, batch_size=1)
        self.assertEqual(sum(map(len, provider.calls)) - before_resume, 1)
        status, attempt = self.db.execute('SELECT status,attempt FROM indexer_state.runs WHERE build_id=%s', (result['build_id'],)).fetchone()
        self.assertEqual((status, attempt), ('ready', 2))
        self.assertEqual(json.loads(self.manifest.read_text())['build_id'], result['build_id'])

    def test_transaction_failure_keeps_manifest_and_leaves_no_rows(self):
        provider = MockProvider()
        self.run_import(corpus(self.state, [self.salt + ' baseline']), provider)
        previous = self.manifest.read_bytes()
        data = corpus(self.state, [self.salt + ' failure'])
        def fail(stage):
            if stage == 'before_publish': raise RuntimeError('injected transaction failure')
        with self.assertRaises(RuntimeError): self.run_import(data, provider, failpoint=fail)
        failed_id = ingest.manifest_for(data, True)['build_id']
        self.assertEqual(self.manifest.read_bytes(), previous)
        self.assertEqual(self.db.execute('SELECT status FROM search.builds WHERE build_id=%s', (failed_id,)).fetchone()[0], 'failed')
        self.assertEqual(self.db.execute('SELECT count(*) FROM search.passages WHERE build_id=%s', (failed_id,)).fetchone()[0], 0)
        count = sum(map(len, provider.calls))
        self.run_import(data, provider)
        self.assertEqual(sum(map(len, provider.calls)), count)


if __name__ == '__main__': unittest.main()
