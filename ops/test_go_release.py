#!/usr/bin/env python3
"""Release boundary regression checks; no application service or network required."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_go_release', Path(__file__).with_name('prepare-go-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

class ReleaseBoundaryTests(unittest.TestCase):
    def test_invalid_sources_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            (root / 'data/public.json').write_text('{}')
            self.assertEqual(release.source_file(root, 'data/public.json'), root / 'data/public.json')
            (root / 'data/link.json').symlink_to(root / 'data/public.json')
            (root / 'assets').symlink_to(root / 'data', target_is_directory=True)
            for name in ('../secret', '/etc/passwd', 'data/../secret.json', 'data//public.json',
                         'data/./public.json', 'app/config.local.php', '.dev/notes.html',
                         'research/private.md', 'data/link.json', 'assets/public.json',
                         'data/missing.json', 'templates/config.php'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    release.source_file(root, name)

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / 'release'
            existing.mkdir()
            sentinel = existing / 'keep'
            sentinel.write_text('unchanged')
            with self.assertRaises(ValueError): release.prepare(existing, None, None)
            self.assertEqual(sentinel.read_text(), 'unchanged')
            link = root / 'link'
            link.symlink_to(existing, target_is_directory=True)
            with self.assertRaises(ValueError): release.prepare(link, None, None)

if __name__ == '__main__': unittest.main()
