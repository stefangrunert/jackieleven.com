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


if __name__ == '__main__':
    root = Path('/var/lib/jackieleven')
    now = time.time()
    sessions = clean(root / 'sessions', r'sess_[A-Za-z0-9,-]+', 21600, now)
    counters = clean(root / 'contact', r'[a-f0-9]{64}\.json', 172800, now)
    print(f'Expired {sessions} sessions and {counters} mail-limit counters.')
