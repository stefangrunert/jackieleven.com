"""Behavioral checks for private-state cleanup; all files are isolated in /tmp."""
import fcntl
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest

spec = importlib.util.spec_from_file_location('cleanup', Path(__file__).resolve().parents[1] / 'ops/clean-state.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupTest(unittest.TestCase):
    def test_expiry_and_active_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            for name in ['sess_expired', 'sess_recent', 'sess_locked', 'unrelated']:
                path = root / name
                path.write_text('fixture')
                age = 60 if name == 'sess_recent' else 22000
                os.utime(path, (now - age, now - age))
            (root / 'sess_symlink').symlink_to(root / 'unrelated')
            (root / 'sess_directory').mkdir()
            with (root / 'sess_locked').open() as locked:
                fcntl.flock(locked, fcntl.LOCK_EX)
                self.assertEqual(cleanup.clean(root, r'sess_[A-Za-z0-9,-]+', 21600, now), 1)
                self.assertFalse((root / 'sess_expired').exists())
                for name in ['sess_recent', 'sess_locked', 'sess_symlink', 'sess_directory', 'unrelated']:
                    self.assertTrue((root / name).exists(), name)
                # A request touching a previously old session makes it fresh again.
                os.utime(root / 'sess_locked', (now, now))
            self.assertEqual(cleanup.clean(root, r'sess_[A-Za-z0-9,-]+', 21600, now), 0)

    def test_counter_retention(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            now = time.time()
            for key, age in [('a', 172801), ('b', 172799)]:
                path = root / (key * 64 + '.json')
                path.write_text('[]')
                os.utime(path, (now - age, now - age))
            self.assertEqual(cleanup.clean(root, r'[a-f0-9]{64}\.json', 172800, now), 1)
            self.assertTrue((root / ('b' * 64 + '.json')).exists())


if __name__ == '__main__':
    unittest.main()
