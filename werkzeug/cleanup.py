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
    def test_go_sessions_counters_and_active_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / 'sessions'
            sessions.mkdir()
            now = time.time()
            names = [('a' * 48 + '.json', 172801), ('b' * 48 + '.json', 172799), ('c' * 48 + '.json', 172801)]
            for name, age in names:
                path = sessions / name
                path.write_text('{}')
                os.utime(path, (now-age, now-age))
            (sessions / ('d' * 48 + '.json')).symlink_to(sessions / names[0][0])
            (sessions / ('e' * 48 + '.json')).mkdir()
            (sessions / 'unrelated').write_text('fixture')
            expired_counter = root / ('a' * 64 + '.json')
            fresh_counter = root / ('b' * 64 + '.json')
            for path, age in [(expired_counter, 172801), (fresh_counter, 172799)]:
                path.write_text('[]')
                os.utime(path, (now-age, now-age))
            with (sessions / names[2][0]).open() as locked:
                fcntl.flock(locked, fcntl.LOCK_EX)
                self.assertEqual(cleanup.clean_state(root, now), (1, 1))
                self.assertFalse((sessions / names[0][0]).exists())
                self.assertFalse(expired_counter.exists())
                self.assertTrue(fresh_counter.exists())
                self.assertTrue((sessions / names[1][0]).exists())
                self.assertTrue((sessions / names[2][0]).exists())
                self.assertTrue((sessions / ('d' * 48 + '.json')).is_symlink())
                self.assertTrue((sessions / ('e' * 48 + '.json')).is_dir())
                self.assertTrue((sessions / 'unrelated').exists())
                os.utime(sessions / names[2][0], (now, now))
            self.assertEqual(cleanup.clean_state(root, now), (0, 0))


if __name__ == '__main__':
    unittest.main()
