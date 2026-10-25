#!/usr/bin/env python3
"""Offline first-install, fault injection and PHP fallback contracts; no network."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('production', Path(__file__).with_name('install-go-production.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
SECRET = 'private-test-value'
POOL = '[jackieleven]\n' + '\n'.join('env['+key+'] = '+SECRET for key in p.REQUIRED) + '\nenv[JACKIE_CONTACT_STATE_DIR] = /untouched/php\n'

class ProductionTests(unittest.TestCase):
    def test_literal_credentials_and_systemd_encoding(self):
        for value in (SECRET, '"'+SECRET+'"', "'"+SECRET+"'"):
            text = '[ignored]\nenv[JACKIE_RESEND_API_KEY] = ignored\n[jackieleven]\n'
            text += '\n'.join('env['+key+'] = '+value+' ; comment' for key in p.REQUIRED)
            values = p.credentials(text)
            self.assertEqual(set(values),set(p.REQUIRED))
            self.assertEqual(values[p.REQUIRED[0]],SECRET)
            self.assertEqual(p.environment(values).count(b'="'),3)
        quoted = p.credentials(POOL.replace(SECRET,'"a\\\"b\\\\c"'))
        self.assertIn(b'="a\\"b\\\\c"',p.environment(quoted))

    def test_rejects_dynamic_missing_duplicate_or_multiline_values(self):
        for bad in ('$ENV', '${ENV}', '"$ENV"', '"bad\\nvalue"', '"unterminated', 'a b', '"x" evil'):
            with self.subTest(bad=bad), self.assertRaises(p.DeploymentError):
                p.credentials(POOL.replace(SECRET,bad))
        for text in ('[other]\n'+POOL.split('\n',1)[1], POOL+'env[JACKIE_RESEND_API_KEY]=again\n'):
            with self.assertRaises(p.DeploymentError): p.credentials(text)

    @contextlib.contextmanager
    def fixture(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.ExitStack() as stack:
            root=Path(temp); base=root/'site'; release=base/'go-releases'/'test'; release.mkdir(parents=True)
            (release/'bin').mkdir(); (release/'bin/jackieleven').write_bytes(b'not executed'); (release/'bin/jackieleven').chmod(0o755)
            (release/'build.json').write_text(json.dumps({'goos':'linux','goarch':'amd64'}))
            (release/'release-manifest.sha256').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(release))+'\n' for f in sorted(release.rglob('*')) if f.is_file()))
            vhost=root/'vhost'; vhost.write_bytes(b'original PHP vhost\n'); vhost.chmod(0o640)
            pool=root/'pool'; pool.write_text(POOL)
            paths={name:root/name.lower() for name in ('UNIT','ENV','START','PROXY','CURRENT')}
            paths['ENV']=root/'new-env-dir'/'go.env'
            stack.enter_context(patch.multiple(p,BASE=base,VHOST=vhost,POOL=pool,BACKUPS=root/'backups',**paths))
            stack.enter_context(patch.object(p.os,'geteuid',return_value=0))
            stack.enter_context(patch.object(p.pwd,'getpwnam',return_value=SimpleNamespace()))
            sock=stack.enter_context(patch.object(p.socket,'socket')); sock.return_value.__enter__.return_value.connect_ex.return_value=1
            stack.enter_context(patch.object(p,'nginx_workers',return_value=[123]))
            stack.enter_context(patch.object(p,'wait_worker_drain'))
            yield SimpleNamespace(root=root,base=base,release=release,vhost=vhost,pool=pool,paths=paths,sha=p.digest(vhost.read_bytes()),stack=stack)

    def test_failure_phases_restore_exact_php_and_remove_only_go_artifacts(self):
        for phase in ('start','backend','nginx-test','TLS','enable','early-write','unit-write','unit-verify'):
            with self.subTest(phase=phase), self.fixture() as f:
                calls=[]; failed=False
                def command(*args):
                    nonlocal failed
                    calls.append(args)
                    target={'start':('systemctl','start',p.SERVICE),'nginx-test':('nginx','-t'),'enable':('systemctl','enable',p.SERVICE),'unit-verify':('systemd-analyze','verify',str(p.UNIT))}.get(phase)
                    if args==target and not failed:
                        failed=True; raise subprocess.CalledProcessError(1,args,stderr=SECRET)
                    return SimpleNamespace(stdout='',returncode=0)
                def health(tls=False):
                    if phase=='backend' and not tls or phase=='TLS' and tls: raise RuntimeError(SECRET)
                original_write=p.atomic_write
                def write(path,data,mode=0o644):
                    nonlocal failed
                    if ((phase=='early-write' and path==p.ENV) or (phase=='unit-write' and path==p.UNIT)) and not failed:
                        failed=True; raise OSError(SECRET)
                    original_write(path,data,mode)
                with patch.object(p,'run',side_effect=command),patch.object(p,'wait_health',side_effect=health),patch.object(p,'atomic_write',side_effect=write):
                    with self.assertRaises(p.DeploymentError) as error: p.install('test',f.sha)
                self.assertNotIn(SECRET,str(error.exception)); self.assertIn('restored PHP',str(error.exception))
                self.assertEqual(f.vhost.read_bytes(),b'original PHP vhost\n'); self.assertEqual(stat.S_IMODE(f.vhost.stat().st_mode),0o640)
                self.assertEqual(f.pool.read_text(),POOL)
                for path in f.paths.values(): self.assertFalse(path.exists() or path.is_symlink(),path)
                self.assertFalse(p.ENV.parent.exists())
                if ('systemctl','stop',p.SERVICE) in calls:
                    self.assertLess(calls.index(('systemctl','reload','nginx')),calls.index(('systemctl','stop',p.SERVICE)))
                self.assertFalse(any('php' in ' '.join(command) for command in calls))

    def test_success_and_persistent_manual_rollback(self):
        with self.fixture() as f,patch.object(p,'run',return_value=SimpleNamespace(stdout='')),patch.object(p,'wait_health') as health:
            result=p.install('test',f.sha); backup=Path(result['backup'])
            self.assertEqual(health.call_args_list[0].args,()); self.assertEqual(health.call_args_list[1].kwargs,{'tls':True})
            self.assertEqual(stat.S_IMODE(p.ENV.stat().st_mode),0o600)
            self.assertEqual(stat.S_IMODE(backup.stat().st_mode),0o700)
            self.assertEqual(stat.S_IMODE((backup/'vhost').stat().st_mode),0o600)
            self.assertEqual(p.CURRENT.resolve(),f.release.resolve())
            self.assertNotIn('CONTACT_STATE_DIR',p.ENV.read_text())
            self.assertNotIn(SECRET,json.dumps(result))
            # Root ownership is required on actual server, simulated here on macOS.
            real_lstat=Path.lstat
            def lstat(path):
                info=real_lstat(path)
                if path in (backup,backup/'manifest.json'): return SimpleNamespace(st_uid=0,st_mode=info.st_mode)
                return info
            with patch.object(Path,'lstat',lstat): p.rollback(backup)
            self.assertEqual(f.vhost.read_bytes(),b'original PHP vhost\n')
            self.assertFalse(p.CURRENT.exists()); self.assertFalse(p.ENV.exists())

    def test_failed_rollback_reload_keeps_go_running_and_recoverable(self):
        with self.fixture() as f:
            calls=[]; reloads=0
            def command(*args):
                nonlocal reloads
                calls.append(args)
                if args==('systemctl','reload','nginx'):
                    reloads+=1
                    if reloads==2: raise subprocess.CalledProcessError(1,args,stderr=SECRET)
                return SimpleNamespace(stdout='')
            def health(tls=False):
                if tls: raise RuntimeError(SECRET)
            with patch.object(p,'run',side_effect=command),patch.object(p,'wait_health',side_effect=health):
                with self.assertRaises(p.DeploymentError) as error: p.install('test',f.sha)
            self.assertIn('rollback incomplete',str(error.exception))
            self.assertNotIn(('systemctl','stop',p.SERVICE),calls)
            self.assertTrue(p.ENV.exists()); self.assertTrue(p.CURRENT.is_symlink())
            self.assertEqual(f.vhost.read_bytes(),b'original PHP vhost\n')

    def test_preconditions_fail_before_credentials_or_mutation(self):
        with self.fixture() as f,patch.object(p,'credentials') as credential_reader:
            with self.assertRaises(p.DeploymentError): p.install('test','0'*64)
            credential_reader.assert_not_called(); self.assertFalse(p.BACKUPS.exists())
            p.UNIT.write_text('existing')
            with self.assertRaises(p.DeploymentError): p.install('test',f.sha)
            credential_reader.assert_not_called(); self.assertEqual(p.UNIT.read_text(),'existing')

    def test_release_escape_checksum_extra_and_permissions_rejected(self):
        for mode in ('escape','extra','checksum','writable','writable-root','symlink'):
            with self.subTest(mode=mode),self.fixture() as f:
                if mode=='escape': (f.release/'release-manifest.sha256').write_text('0'*64+'  ../escape\n')
                if mode=='extra': (f.release/'secret').write_text('unexpected')
                if mode=='checksum': (f.release/'bin/jackieleven').write_bytes(b'changed')
                if mode=='writable': (f.release/'bin/jackieleven').chmod(0o777)
                if mode=='writable-root': f.release.chmod(0o777)
                if mode=='symlink': (f.release/'link').symlink_to(f.pool)
                with self.assertRaises(p.DeploymentError): p.verify_release(f.release)

    def test_contact_contract_rejects_unready_or_insecure_response(self):
        body='<input name="token" value="'+'a'*48+'"><div class="cf-turnstile" data-sitekey="public"><button type="submit">Send</button>'
        headers={'Set-Cookie':'jackie_contact='+'a'*48+'; Secure; HttpOnly; SameSite=Lax; Path=/', 'Cache-Control':'no-store, no-cache, must-revalidate'}
        p.check_response('/de/mitmachen',headers,body)
        for variant in (body.replace('type="submit"','type="submit" disabled'),body.replace('public',''),body.replace('a'*48,'short')):
            with self.assertRaises(p.DeploymentError): p.check_response('/de/mitmachen',headers,variant)
        with self.assertRaises(p.DeploymentError): p.check_response('/de/mitmachen',dict(headers,**{'Set-Cookie':headers['Set-Cookie'].replace('Secure; ','')}),body)

    def test_concurrent_vhost_change_is_never_overwritten(self):
        with self.fixture() as f,patch.object(p,'run',return_value=SimpleNamespace(stdout='')):
            def health(tls=False): f.vhost.write_bytes(b'concurrent administrator change')
            with patch.object(p,'wait_health',side_effect=health):
                with self.assertRaises(p.DeploymentError) as error: p.install('test',f.sha)
            self.assertIn('rollback incomplete',str(error.exception))
            self.assertEqual(f.vhost.read_bytes(),b'concurrent administrator change')
            self.assertTrue(p.ENV.exists())

    def test_failed_worker_drain_never_stops_backend(self):
        with self.fixture() as f,patch.object(p,'run',return_value=SimpleNamespace(stdout='')) as command:
            def health(tls=False):
                if tls: raise RuntimeError('failed')
            with patch.object(p,'wait_health',side_effect=health),patch.object(p,'wait_worker_drain',side_effect=p.DeploymentError('waiting')):
                with self.assertRaises(p.DeploymentError): p.install('test',f.sha)
            self.assertNotIn(('systemctl','stop',p.SERVICE),[call.args for call in command.call_args_list])
            self.assertTrue(p.CURRENT.exists())
            self.assertEqual(f.vhost.read_bytes(),b'original PHP vhost\n')

    def test_worker_drain_waits_for_old_workers_and_is_bounded(self):
        with patch.object(Path,'read_bytes',side_effect=[b'nginx: worker process is shutting down',FileNotFoundError()]),patch.object(p.time,'sleep') as sleep:
            p.wait_worker_drain([123])
            self.assertEqual(sleep.call_count,1)
        with patch.object(Path,'read_bytes',return_value=b'nginx: worker process'),patch.object(p.time,'sleep') as sleep:
            with self.assertRaises(p.DeploymentError): p.wait_worker_drain([123])
            self.assertEqual(sleep.call_count,80)

    def test_cli_never_prints_subprocess_or_os_payload(self):
        for failure in (OSError(SECRET),subprocess.CalledProcessError(1,['private'],output=SECRET,stderr=SECRET)):
            output=io.StringIO()
            with patch.object(p,'install',side_effect=failure),contextlib.redirect_stderr(output):
                self.assertEqual(p.main(['--release','test','--expected-sha','0'*64]),1)
            self.assertNotIn(SECRET,output.getvalue())

if __name__=='__main__': unittest.main()
