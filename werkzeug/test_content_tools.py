"""Offline regressions for catalogue publication and explicit maintenance actions."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import content
import contact_parity
import argparse
import sys
import inhalte
import livevideos
import quellen
import zitate


class ContentPublicationTest(unittest.TestCase):
    def test_entire_catalogue_matches_published_json_without_writes(self):
        expected_path = content.ROOT / 'data/quellen.json'
        before = expected_path.read_bytes()
        actual, stats = quellen.build()
        self.assertEqual(actual, json.loads(before))
        self.assertEqual(stats['stale_translations'], 0)
        self.assertEqual(expected_path.read_bytes(), before)
        self.assertGreater(len(actual), 700)

    def test_publication_levels_and_internal_references(self):
        q = {'datei': next(iter(quellen.SELECTED)), 'sicherheit': 'indirekt', 'art': 'Interview', 'kategorie': 'interviews', 'umfang': 'kurz'}
        self.assertEqual(quellen.level(q, None), 'auswahl')
        self.assertEqual(quellen.level(q, 'intern'), 'intern')
        q['datei'] = 'other.md'
        self.assertEqual(quellen.level(q, None), 'intern')
        q['sicherheit'] = 'belegt'
        self.assertEqual(quellen.level(q, None), 'verzeichnis')
        q['art'] = 'Sammeldatei'
        self.assertEqual(quellen.level(q, None), 'weitere')
        result = quellen.paragraphs('Public sentence (research/private.md). Internal research/work.md reference. Another public sentence.\n\nSee README.\n\nDr. Leven remains together.')
        self.assertEqual(result, ['Public sentence. Another public sentence.', 'Dr. Leven remains together.'])

    def test_stale_translation_is_withheld(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'research/quellen/interviews'
            directory.mkdir(parents=True)
            path = directory / '2000-01_test.md'
            path.write_text('---\nstufe: "verzeichnis"\n---\n## Inhalt\nOriginal sentence.\n')
            item = {'datei': 'interviews/2000-01_test.md', 'titel': 'Title', 'autor': 'Writer', 'medium': 'Medium', 'datum': '2000-01', 'kategorie': 'interviews', 'art': 'Interview', 'sprache': 'en', 'url': 'https://example.test/source', 'archiv': '', 'erreichbarkeit': 'live', 'thema': []}
            content.write_json(root / 'research/quellen/index.json', [item])
            content.write_json(root / 'data/diskografie.json', {'releases': []})
            digest = quellen.hashlib.sha1(b'Original sentence.Original sentence.').hexdigest()
            content.write_json(root / 'data/quellen-en.json', {'2000-01-test': {'quelle': digest, 'kurz': 'English', 'inhalt': ['English']}})
            catalogue, stats = quellen.build(root)
            self.assertEqual(catalogue[0]['kurz']['en'], 'English')
            self.assertEqual(stats['stale_translations'], 0)
            path.write_text(path.read_text().replace('Original sentence.', 'Changed sentence.'))
            catalogue, stats = quellen.build(root)
            self.assertNotIn('en', catalogue[0]['kurz'])
            self.assertEqual(stats['stale_translations'], 1)

    def test_licenses_refresh_only_through_injected_transport(self):
        index = [{'url': 'https://www.nb.no/items/URN:NBN:no-nb_digavis_test'}]
        def fake(_url):
            return {'_embedded': {'items': [{'accessInfo': {'license': 'ccbync', 'accessAllowedFrom': 'EVERYWHERE'}}]}}
        with patch.object(quellen.time, 'sleep'):
            result = quellen.refresh_licenses(index, {}, fetch=fake)
        self.assertEqual(result['URN:NBN:no-nb_digavis_test']['access'], 'EVERYWHERE')

    def test_quote_cli_root_selects_its_own_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content.write_json(root / 'data/stationen.json', [])
            with patch.object(sys, 'argv', ['zitate.py', '--root', str(root)]):
                with self.assertRaises(SystemExit) as result:
                    zitate.main()
            self.assertEqual(result.exception.code, False)

    def test_historical_contact_comparison_rejects_public_targets(self):
        self.assertEqual(contact_parity.isolated_origin('http://127.0.0.1:8092/'), 'http://127.0.0.1:8092')
        for url in ['https://jackieleven.com', 'https://unpubli.sh/jackieleven', 'http://localhost.evil.test', 'http://user@localhost', 'http://127.0.0.1:8080/?x=1']:
            with self.assertRaises(argparse.ArgumentTypeError):
                contact_parity.isolated_origin(url)

    def test_catalogues_and_quotes(self):
        errors, counts = inhalte.validate()
        self.assertEqual(errors, [])
        self.assertEqual(counts['columns'], 73)
        checked, errors = zitate.verify(content.read_json(content.ROOT / 'data/stationen.json'))
        self.assertGreater(checked, 0)
        self.assertEqual(errors, [])
        with self.assertRaises(ValueError):
            content.source_path(content.ROOT / 'research', '../data/quellen.json')


class VideoMaintenanceTest(unittest.TestCase):
    def test_api_embeddability_and_batches(self):
        ids = [str(i).zfill(11) for i in range(51)]
        calls = []
        def fake(url):
            requested = parse_qs(urlparse(url).query)['id'][0].split(',')
            calls.append(requested)
            items = []
            for ident in requested:
                if ident == ids[5]:
                    continue
                item = {'id': ident, 'status': {'embeddable': True, 'privacyStatus': 'public'}, 'contentDetails': {}}
                if ident == ids[0]: item['status']['embeddable'] = False
                if ident == ids[1]: item['status']['privacyStatus'] = 'private'
                if ident == ids[2]: item['contentDetails']['contentRating'] = {'ytRating': 'ytAgeRestricted'}
                if ident == ids[3]: item['contentDetails']['regionRestriction'] = {'blocked': ['DE']}
                if ident == ids[4]: item['contentDetails']['regionRestriction'] = {'allowed': ['NO']}
                items.append(item)
            return 200, json.dumps({'items': items}).encode()
        result = livevideos.api_permissions(ids, 'synthetic-test-key', fake)
        self.assertEqual([len(c) for c in calls], [50, 1])
        self.assertTrue(all(not result[i]['embeddable'] for i in ids[:6]))
        self.assertTrue(all(result[i]['embeddable'] for i in ids[6:]))

    def test_oembed_status_and_failure(self):
        for status, expected in [(200, True), (401, False), (403, False), (404, False)]:
            self.assertEqual(livevideos.oembed_permission('abcdefghijk', lambda _: (status, b''))['embeddable'], expected)
        with self.assertRaises(RuntimeError):
            livevideos.oembed_permission('abcdefghijk', lambda _: (503, b''))

    def test_update_is_copy_and_creates_only_needed_previews(self):
        data = {'concert': {'videos': [{'id': 'abcdefghijk', 'checked': 'old', 'embeddable': False}, {'id': 'ABCDEFGHIJK', 'checked': 'old', 'embeddable': True}]}}
        before = deepcopy(data)
        previews = []
        def transport(url):
            return (404 if 'ABCDEFGHIJK' in url else 200), b''
        with tempfile.TemporaryDirectory() as tmp:
            updated, _ = livevideos.update(data, tmp, transport=transport, previewer=lambda ident: previews.append(ident) or 1024, today='2026-10-25', pause=lambda _: None)
            self.assertEqual(data, before)
            self.assertEqual(previews, ['abcdefghijk'])
            self.assertTrue(updated['concert']['videos'][0]['embeddable'])
            self.assertFalse(updated['concert']['videos'][1]['embeddable'])
            self.assertEqual(updated['concert']['videos'][0]['checked'], '2026-10-25')
            with self.assertRaises(ValueError):
                livevideos.update({'x': {'videos': [{'id': '../bad'}]}}, tmp, transport=lambda _: self.fail('unexpected network'))

    def test_thumbnail_dimensions_without_network(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow optional image dependency is not installed')
        image = BytesIO()
        Image.new('RGB', (480, 360), 'red').save(image, format='PNG')
        with tempfile.TemporaryDirectory() as tmp:
            size = livevideos.thumbnail('abcdefghijk', tmp, transport=lambda _: (200, image.getvalue()))
            with Image.open(Path(tmp) / 'abcdefghijk.webp') as result:
                self.assertEqual(result.size, (480, 270))
                self.assertEqual(result.format, 'WEBP')
            self.assertGreater(size, 0)


if __name__ == '__main__':
    unittest.main()
