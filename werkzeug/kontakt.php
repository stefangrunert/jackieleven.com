<?php
/** Contact validation, abuse limits, rendering and session/CSRF handling. No emails sent. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';
require APP_ROOT . '/kontakt.php';
function kontakt_test(bool $ok, string $text): void {
    if (!$ok) throw new RuntimeException($text);
}
$valid = ['name' => 'Anna', 'email' => 'anna@example.org', 'nachricht' => 'Eine Erinnerung an Jackie.'];
kontakt_test(kontakt_pruefen($valid) === [], 'Valid input rejected');
foreach ([
    ['email', "anna@example.org\r\nBcc: other@example.org"],
    ['name', "Anna\r\nOther"], ['name', str_repeat('x', 121)],
    ['nachricht', ''], ['nachricht', str_repeat('ä', 10001)],
] as [$key, $value]) {
    $input = array_replace($valid, [$key => $value]);
    kontakt_test(isset(kontakt_pruefen($input)[$key]), 'Invalid field accepted: ' . $key);
}
kontakt_test(kontakt_felder(['email' => ['x'], 'nachricht' => ['x']])['email'] === '', 'Array input accepted');
$config = kontakt_config();
$payload = kontakt_payload($valid, $config);
kontakt_test($payload['to'] === ['stefan@jackieleven.com'], 'Recipient changed');
kontakt_test($payload['reply_to'] === $valid['email'] && str_contains($payload['from'], '@unpubli.sh>'), 'Sender/reply address incorrect');
kontakt_test(!kontakt_senden($payload, '', 'test'), 'Empty key accepted');
$dir = sys_get_temp_dir() . '/jackie-contact-test-' . bin2hex(random_bytes(6));
mkdir($dir, 0700);
try {
    for ($i = 0; $i < 5; $i++) kontakt_test(kontakt_limit($dir, '192.0.2.1', time()), 'Rate limit too strict');
    kontakt_test(!kontakt_limit($dir, '192.0.2.1', time()), 'Rate limit bypassed');
    kontakt_test(kontakt_limit($dir, '192.0.2.2', time()), 'Other IP blocked');
    kontakt_test(kontakt_limit($dir, '192.0.2.1', time() + 3601), 'Rate limit did not expire');
    $sid = 'test' . bin2hex(random_bytes(12));
    $request = function(string $method, array $post = []) use ($dir, $sid): array {
        $code = 'ini_set("session.save_path", ' . var_export($dir, true) . ');'
            . 'session_id(' . var_export($sid, true) . ');'
            . 'putenv("JACKIE_RESEND_API_KEY=");'
            . 'require ' . var_export(APP_ROOT . '/bootstrap.php', true) . ';'
            . 'require APP_ROOT . "/kontakt.php"; sprache("de");'
            . '$_SERVER["REQUEST_METHOD"]=' . var_export($method, true) . ';'
            . '$_POST=' . var_export($post, true) . ';'
            . '$r=kontakt_bearbeiten(); echo json_encode($r);';
        $proc = proc_open([PHP_BINARY, '-r', $code], [1 => ['pipe','w'], 2 => ['pipe','w']], $pipes);
        $out = stream_get_contents($pipes[1]); $err = stream_get_contents($pipes[2]);
        fclose($pipes[1]); fclose($pipes[2]);
        kontakt_test(proc_close($proc) === 0 && $err === '', 'Contact request failed: ' . $err);
        return json_decode($out, true, 512, JSON_THROW_ON_ERROR);
    };
    file_put_contents($dir . '/sess_' . $sid, '');
    $get = $request('GET');
    kontakt_test(strlen($get['token']) === 48 && $get['status'] === 200, 'GET form missing');
    $bad = $request('POST', $valid + ['token' => 'invalid']);
    kontakt_test($bad['status'] === 400 && $bad['global'] === 'sitzung', 'CSRF bypassed');
    // Age the stored form to avoid timing-dependent sleeps in the test.
    $sessionFile = $dir . '/sess_' . $sid;
    $session = file_get_contents($sessionFile);
    $session = preg_replace_callback('/s:4:"zeit";i:(\d+);/', fn($m) => 's:4:"zeit";i:' . ((int) $m[1] - 10) . ';', $session);
    file_put_contents($sessionFile, $session);
    $post = $request('POST', $valid + ['token' => $get['token']]);
    kontakt_test($post['status'] === 503 && $post['global'] === 'konfiguration', 'Unconfigured send must fail clearly');
    kontakt_test($post['felder'] === $valid && $post['token'] === $get['token'], 'Failed send lost text or retry identity');
    foreach (SPRACHEN as $lang) {
        sprache($lang);
        $html = render('mitmachen', $get);
        kontakt_test(str_contains($html, 'mailto:stefan@jackieleven.com') && str_contains($html, 'method="post"'), 'Form missing');
        kontakt_test(!str_contains($html, '>mit.'), 'Missing translation');
        $evil = $get;
        $evil['felder']['nachricht'] = '</textarea><script>alert(1)</script>';
        kontakt_test(!str_contains(render('mitmachen', $evil), '<script>alert'), 'Message HTML not escaped');
    }
} finally {
    foreach (glob($dir . '/*') ?: [] as $file) unlink($file);
    rmdir($dir);
}
echo "Kontakt: Eingaben, CSRF, Rate-Limit, Fehlererhalt, sichere Ausgabe und DE/EN geprüft; keine E-Mails verschickt.\n";
