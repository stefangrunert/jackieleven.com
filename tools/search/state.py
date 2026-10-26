"""Private persistent passage identities and content-addressed embedding artifacts."""
from collections import defaultdict
import json
import math
from pathlib import Path
import sqlite3
import uuid
from common import atomic_json, canonical, sha


class State:
    def __init__(self, directory):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.root / 'registry.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE IF NOT EXISTS passages (id TEXT PRIMARY KEY, document TEXT, family TEXT, ordinal INTEGER, hash TEXT, active INTEGER)')
        self.db.execute('CREATE INDEX IF NOT EXISTS passage_group ON passages(document,family)')

    def assign(self, candidates):
        groups = defaultdict(list)
        for p in candidates:
            groups[(p['document_id'], p.pop('_family'))].append(p)
        result = []
        with self.db:
            # All candidates were successfully enumerated before any tombstones are written.
            old_groups = defaultdict(list)
            for row in self.db.execute('SELECT id,document,family,ordinal,hash,active FROM passages ORDER BY ordinal,id'):
                old_groups[(row[1], row[2])].append(row)
            self.db.execute('UPDATE passages SET active=0')
            for group, items in sorted(groups.items()):
                old = old_groups[group]
                claimed = set()
                assignments = {}
                # Match unchanged text before positional correction, so insertions cannot steal moved IDs.
                for i, item in enumerate(items):
                    matches = [r for r in old if r[4] == item['content_hash'] and r[0] not in claimed]
                    if matches:
                        row = min(matches, key=lambda r: (not r[5], abs(r[3]-i), r[0]))
                        assignments[i] = row[0]
                        claimed.add(row[0])
                for i, item in enumerate(items):
                    if i not in assignments:
                        matches = [r for r in old if r[5] and r[3] == i and r[0] not in claimed]
                        if matches:
                            assignments[i] = matches[0][0]
                        else:
                            seed = '|'.join(group) + '|' + item['content_hash'] + '|' + str(i)
                            assignments[i] = group[0] + '#p-' + uuid.uuid5(uuid.NAMESPACE_URL, seed).hex
                            # Never reuse a historical ID for another current occurrence.
                            counter = 0
                            while assignments[i] in claimed:
                                counter += 1
                                assignments[i] = group[0] + '#p-' + uuid.uuid5(uuid.NAMESPACE_URL, seed + ':' + str(counter)).hex
                        claimed.add(assignments[i])
                    item['id'] = assignments[i]
                    self.db.execute('INSERT INTO passages VALUES(?,?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET ordinal=excluded.ordinal,hash=excluded.hash,active=1',
                                    (item['id'], group[0], group[1], i, item['content_hash']))
                    result.append(item)
        return sorted(result, key=lambda p: p['id'])

    def artifact_key(self, profile, text):
        return sha(canonical({'profile': profile, 'text': text}))

    def artifact_path(self, key):
        return self.root / 'artifacts' / (key + '.json')

    def artifact(self, key):
        path = self.artifact_path(key)
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text())
            vector = value['vector']
            if value['key'] != key or value['sha256'] != sha(canonical(vector)) or len(vector) != 1024:
                return None
            if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in vector):
                return None
            if abs(sum(x*x for x in vector)-1) > 1e-5:
                return None
            return value
        except (ValueError, TypeError, KeyError, OSError):
            return None

    def save_artifact(self, key, vector):
        value = {'key': key, 'sha256': sha(canonical(vector)), 'vector': vector}
        atomic_json(self.artifact_path(key), value)
        if self.artifact(key) is None:
            raise ValueError('artifact_validation_failed')
        return value
