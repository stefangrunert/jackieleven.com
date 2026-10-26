"""Pinned full-corpus checks: no provider calls, database writes or source mutations."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import canonical
from exporter import Snapshot, export
from sections import chapter_parts, SECTIONS
from state import State

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = Path(os.environ.get('SEARCH_TEST_ARCHIVE_ROOT', '/Users/stefan/www/jackieleven-archive'))


class ChapterTests(unittest.TestCase):
    def test_reader_separates_public_parts_and_drops_editorial_frontmatter(self):
        raw = '---\nprivate_editorial_status: do not index\n---\n\n> **Hinweis:** replace this warning\n\n# A chapter\n\nA fictional scene.\n\n---\n\n## Documented / invented\n\nThe scene is invented.'
        parts = chapter_parts(raw)
        self.assertEqual(parts['text'], 'A fictional scene.')
        self.assertEqual(parts['anmerkung'], '')
        self.assertEqual(parts['apparat'], '## Documented / invented\n\nThe scene is invented.')
        self.assertNotIn('private_editorial_status', str(parts))
        self.assertNotIn('replace this warning', str(parts))


@unittest.skipUnless(ARCHIVE.is_dir(), 'Pinned archive checkout is required')
class FullCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.state = State(cls.tmp.name)
        cls.website = Snapshot(ROOT, '11947ff9ed768bdd525defbc1807d6ebb1f88266')
        cls.archive = Snapshot(ARCHIVE, '7d353a4')
        cls.corpus = export(cls.website, cls.archive, cls.state)

    @classmethod
    def tearDownClass(cls):
        cls.state.db.close()
        cls.tmp.cleanup()

    def test_all_public_sections_and_catalogue_members_are_covered(self):
        coverage = self.corpus['coverage']
        self.assertEqual(set(coverage['sections']), SECTIONS)
        self.assertTrue(all(v['passages'] > 0 for v in coverage['sections'].values()))
        self.assertEqual((coverage['sources'], coverage['source_detail_pages'], coverage['catalog_only_sources']), (741, 500, 241))
        self.assertEqual((coverage['columns'], coverage['releases'], coverage['track_rows'], coverage['stations'], coverage['pastiche_chapters']), (73, 88, 881, 14, 15))
        source_ids = {p['metadata']['website_source_id'] for p in self.corpus['passages'] if p['metadata'].get('website_source_id')}
        self.assertEqual(source_ids, {q['id'] for q in self.website.json('data/quellen.json')})
        self.assertEqual(coverage['fan_video_groups_excluded_by_default'], 5)
        self.assertEqual(coverage['public_official_concerts'], 1)

    def test_all_pastiche_parts_are_explicit_fiction(self):
        passages = [p for p in self.corpus['passages'] if p['document_id'].startswith('private/document/pastiche/')]
        self.assertEqual(len({p['document_id'] for p in passages}), 15)
        self.assertEqual({p['language'] for p in passages}, {'de', 'en'})
        self.assertTrue(all(p['metadata']['fiction'] is True and p['text_voice'] == 'pastiche' and p['source_voice'] == 'pastiche' for p in passages))
        self.assertTrue(all(p['metadata']['section'] == 'biography' for p in passages))
        self.assertTrue(any(p['metadata']['chapter_part'] == 'apparat' for p in passages))
        self.assertFalse(any('/00-' in path for path in self.corpus['inputs']['website']['files']))

    def test_catalogue_only_does_not_expose_stored_detail_texts(self):
        catalog_only = [p for p in self.corpus['passages'] if p['metadata'].get('record_kind') == 'catalog_source']
        self.assertEqual(len({p['metadata']['website_source_id'] for p in catalog_only}), 241)
        self.assertTrue(all('?auswahl=0#' in p['url_de'] for p in catalog_only))
        for p in catalog_only:
            selector = p['metadata']['source_selector']
            self.assertIsInstance(selector, str)
            self.assertFalse(any(token in selector for token in ['/inhalt/', '/kurz/', '/beleg/', '/zitate/']))
        # Only allowlisted columns are read from research; no source research notes or private .dev inputs.
        files = self.corpus['inputs']['website']['files']
        self.assertTrue(all(not path.startswith('research/') or path.startswith('research/columns/') for path in files))
        self.assertFalse(any(path.startswith('.dev/') for path in files))

    def test_graph_and_all_statement_statuses_are_preserved(self):
        original = self.archive.graph()
        self.assertEqual(self.corpus['entities'], original)
        statements = {s['statement_id']: s for entity in original for values in entity['data'].values() if isinstance(values, list) for s in values if isinstance(s, dict) and s.get('statement_id')}
        records = [p for p in self.corpus['passages'] if p['metadata'].get('record_kind') == 'archive_statement']
        self.assertEqual({p['metadata']['statement_id'] for p in records}, set(statements))
        self.assertEqual(len(statements), 1853)
        for p in records:
            s = statements[p['metadata']['statement_id']]
            self.assertEqual(p['metadata']['rank'], s.get('rank', 'normal'))
            self.assertEqual(p['metadata']['certainty'], s.get('certainty'))
            self.assertEqual(p['metadata']['references'], s.get('references', []))
            self.assertEqual(p['text_voice'], 'editorial')
            self.assertEqual(p['metadata']['representation'], 'archive_record')
        bodo = next(e['data'] for e in original if e['id'] == 'event/1997-04-13-bodo-den-siste-glaede')
        self.assertEqual(len(bodo['time']), 2)
        records = [p for p in self.corpus['passages'] if p['metadata'].get('entity_id') == bodo['id']]
        self.assertTrue(all('1997-04-13' in p['metadata']['display_date'] and '[1997-04-05,1997-04-06,1997-04-13]' in p['metadata']['display_date'] for p in records))
        self.assertTrue(all(p['year'] is None for p in records))
        self.assertTrue(all(p['url_de'].startswith('/de/suche/objekt?id=') for p in records))

    def test_repeat_export_is_identical(self):
        again = export(Snapshot(ROOT, '11947ff9ed768bdd525defbc1807d6ebb1f88266'), Snapshot(ARCHIVE, '7d353a4'), self.state)
        self.assertEqual(canonical(self.corpus), canonical(again))

    @unittest.skipUnless(os.environ.get('SEARCH_BASELINE_EXPORT'), 'Set SEARCH_BASELINE_EXPORT to check the retained vector inputs')
    def test_all_previous_embedding_inputs_remain_unchanged(self):
        baseline = json.loads(Path(os.environ['SEARCH_BASELINE_EXPORT']).read_text())
        old = {p['content_hash'] for p in baseline['passages']}
        new = {p['content_hash'] for p in self.corpus['passages']}
        self.assertEqual(len(old), 7730)
        self.assertFalse(old - new)


if __name__ == '__main__': unittest.main()
