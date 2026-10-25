#!/usr/bin/env python3
"""Exercise deployment rollback without touching a server, nginx or systemd."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('preview', Path(__file__).with_name('install-go-preview.py'))
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)

class PreviewRollbackTest(unittest.TestCase):
    def test_https_waits_for_new_nginx_workers(self):
        results = [subprocess.CalledProcessError(22, 'curl'), SimpleNamespace(stdout='old worker'),
                   SimpleNamespace(stdout='/jackieleven/assets/site.css')]
        with patch.object(preview, 'run', side_effect=results) as run, patch.object(preview.time, 'sleep') as sleep:
            preview.https_healthcheck()
        self.assertEqual(run.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_https_failure_remains_bounded(self):
        with patch.object(preview, 'run', side_effect=subprocess.CalledProcessError(22, 'curl')) as run, patch.object(preview.time, 'sleep'):
            with self.assertRaises(subprocess.CalledProcessError): preview.https_healthcheck()
        self.assertEqual(run.call_count, 20)

    def test_failed_service_restores_vhost_and_removes_new_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / 'site'; release = base / 'releases' / 'test'; release.mkdir(parents=True)
            (release / 'build.json').write_text(json.dumps({'goos':'linux','goarch':'amd64'}))
            digest = hashlib.sha256((release / 'build.json').read_bytes()).hexdigest()
            (release / 'release-manifest.sha256').write_text(digest+'  build.json\n')
            vhost = root / 'unpublish'; original = ('server {\n'+preview.ANCHOR+'\n}\n').encode()
            vhost.write_bytes(original); vhost.chmod(0o640)
            paths = {name:root/name.lower() for name in ('UNIT','LOCATION','LIMITS','REALIP')}
            source = root / 'source-realip'; source.write_text('real_ip_header CF-Connecting-IP;\n')
            calls = []
            def fake_run(*args):
                calls.append(args)
                if args == ('systemctl','restart',preview.SERVICE):
                    raise subprocess.CalledProcessError(1,args)
                return SimpleNamespace(stdout='',returncode=0)
            real_path = Path
            def fake_path(value):
                if value == '/var/backups/jackieleven-go-preview': return root/'backups'
                return real_path(value)
            with patch.multiple(preview,BASE=base,VHOST=vhost,SOURCE_REALIP=source,**paths), \
                 patch.object(preview,'Path',side_effect=fake_path), \
                 patch.object(preview.os,'geteuid',return_value=0), \
                 patch.object(preview.pwd,'getpwnam',return_value=SimpleNamespace()), \
                 patch.object(preview,'run',side_effect=fake_run), \
                 patch.object(preview.subprocess,'run',return_value=SimpleNamespace(returncode=3)):
                with self.assertRaises(subprocess.CalledProcessError):
                    preview.install('test',hashlib.sha256(original).hexdigest())
            self.assertEqual(vhost.read_bytes(),original)
            self.assertEqual(stat.S_IMODE(vhost.stat().st_mode),0o640)
            for path in paths.values(): self.assertFalse(path.exists(),path)
            self.assertIn(('nginx','-t'),calls)
            self.assertIn(('systemctl','reload','nginx'),calls)
            self.assertEqual(len(list((root/'backups').glob('*/manifest.json'))),1)

if __name__ == '__main__': unittest.main()
