"""Expire only this site's old sessions and mail-limit counters; never active locks."""
import fcntl
import os
from pathlib import Path
import re
import stat
import time


def clean(directory: Path, pattern: str, lifetime: int, now: float) -> int:
    removed = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            if not re.fullmatch(pattern, entry.name):
                continue
            try:
                # Do not follow symlinks or block on a special file.
                fd = os.open(entry.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except (FileNotFoundError, OSError):
                continue
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                current = os.fstat(fd)
                if not stat.S_ISREG(current.st_mode) or current.st_mtime >= now - lifetime:
                    continue
                # Confirm the locked file is still the directory entry being removed.
                named = os.stat(entry.path, follow_symlinks=False)
                if (named.st_dev, named.st_ino) != (current.st_dev, current.st_ino):
                    continue
                os.unlink(entry.path)
                removed += 1
            except FileNotFoundError:
                pass
            finally:
                os.close(fd)
    return removed


def clean_state(root: Path, now: float) -> tuple[int, int]:
    # Match the runtime's two-day retention and exact state-file namespaces.
    sessions = clean(root / 'sessions', r'[a-f0-9]{48}\.json', 172800, now) if (root / 'sessions').is_dir() else 0
    counters = clean(root, r'[a-f0-9]{64}\.json', 172800, now) if root.is_dir() else 0
    return sessions, counters


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', required=True, type=Path,
                        help='Private Go contact directory (JACKIE_CONTACT_STATE_DIR)')
    args = parser.parse_args()
    sessions, counters = clean_state(args.state_dir, time.time())
    print(f'Expired {sessions} sessions and {counters} mail-limit counters.')
