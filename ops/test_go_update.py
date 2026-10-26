"""Offline update rollback and production routing checks; never uses credentials."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('update', Path(__file__).with_name('update-go-production.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

class UpdateTests(unittest.TestCase):
    def test_nginx_keeps_contact_origin_and_security_controls(self):
        original = (u.SOURCE/'nginx-go-site.conf').read_text()
        result = u.nginx_config(original)
        self.assertEqual(u.nginx_config(result), result)
        self.assertEqual(result.count(u.INCLUDE), 1)
        for control in ('limit_req zone=jackie_contact', 'jackie_origin_allowed', 'challenges.cloudflare.com', 'location ~ /\\.', 'client_max_body_size 128k'):
            self.assertIn(control, result)
        self.assertIn('$jackie_production_referrer', result)
        with self.assertRaises(RuntimeError): u.nginx_config('unexpected site')

    def test_rollback_restores_link_mode_owner_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); backup = root/'backup'; backup.mkdir()
            config = root/'config'; config.write_bytes(b'original configuration'); config.chmod(0o600)
            current = root/'current'; current.symlink_to('/releases/old')
            new = root/'new'; unit = root/'search.service'
            entries = u.snapshot([config,current,new,unit],backup)
            config.write_bytes(b'changed'); config.chmod(0o644)
            u.link_to(current,'/releases/new'); new.write_bytes(b'new secret'); unit.write_text('new service')
            manifest = {'entries':entries,'search_active':False,'search_enabled':False,'state':'prepared'}
            calls=[]
            with patch.object(u,'SEARCH_UNIT',unit), patch.object(u,'active',return_value=True), patch.object(u,'run',side_effect=lambda *args: calls.append(args)), patch.object(u.initial,'wait_health'):
                u.rollback(backup,manifest)
            self.assertEqual(config.read_bytes(),b'original configuration')
            self.assertEqual(config.stat().st_mode & 0o777,0o600)
            self.assertEqual(config.stat().st_uid,os.getuid())
            self.assertEqual(os.readlink(current),'/releases/old')
            self.assertFalse(new.exists()); self.assertFalse(unit.exists())
            self.assertEqual(json.loads((backup/'transaction.json').read_text())['state'],'rolled-back')
            self.assertLess(calls.index(('systemctl','disable',u.SEARCH_SERVICE)),calls.index(('systemctl','daemon-reload')))
            self.assertIn(('systemctl','restart',u.WEB_SERVICE),calls)

    def test_semantic_gate_rejects_degraded_empty_and_wrong_snapshot(self):
        class Response:
            def __init__(self,value): self.value=value
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self): return json.dumps(self.value).encode()
        for value in ({'hits':[1],'degraded':True,'content_version':'v'}, {'hits':[],'content_version':'v'}, {'hits':[1],'content_version':'wrong'}):
            with patch.object(u.urllib.request,'urlopen',return_value=Response(value)),self.assertRaises(RuntimeError): u.verify_semantic('v')
        with patch.object(u.urllib.request,'urlopen',return_value=Response({'hits':[1],'content_version':'v','duration_ms':123})):
            self.assertEqual(u.verify_semantic('v')['hits'],1)

    def test_search_configuration_keeps_secrets_and_api_private(self):
        unit=(u.SOURCE/'search/search-production.service').read_text()
        self.assertIn('127.0.0.1:18768',unit)
        self.assertIn('User=jackieleven-search\n',unit)
        self.assertIn('ProtectSystem=strict',unit)
        routing=(u.SOURCE/'nginx-search-production-location.conf').read_text()
        self.assertNotIn('18768',routing)
        self.assertIn('location = /de/suche-test { return 404; }',routing)
        self.assertEqual(routing.count('jackie_production_search_private'),2)
        limits=(u.SOURCE/'nginx-search-production-limits.conf').read_text()
        logline=next(x for x in limits.splitlines() if x.startswith('log_format'))
        for forbidden in ('$args','$request_uri','$remote_addr','$http_referer'):
            self.assertNotIn(forbidden,logline)
        self.assertIn('rate=12r/m',limits); self.assertIn('rate=60r/m',limits)

if __name__ == '__main__': unittest.main()
