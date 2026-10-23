<?php
declare(strict_types=1);

/** Secrets come from the PHP environment or an ignored, access-protected local file. */
function kontakt_config(): array
{
    $local = is_file(APP_ROOT . '/config.local.php') ? require APP_ROOT . '/config.local.php' : [];
    return [
        'key' => getenv('JACKIE_RESEND_API_KEY') !== false ? getenv('JACKIE_RESEND_API_KEY') : ($local['resend_api_key'] ?? ''),
        'from' => 'Jackie Leven · Hommage <jackieleven@unpubli.sh>',
        'to' => 'stefan@jackieleven.com',
        'state' => getenv('JACKIE_CONTACT_STATE_DIR') ?: sys_get_temp_dir() . '/jackieleven-contact-' . substr(hash('sha256', APP_ROOT), 0, 12),
    ];
}

function kontakt_felder(array $post): array
{
    $felder = [];
    foreach (['name', 'email', 'nachricht'] as $key) {
        $felder[$key] = is_string($post[$key] ?? null) ? trim($post[$key]) : '';
    }
    return $felder;
}

function kontakt_pruefen(array $felder): array
{
    $fehler = [];
    if (mb_strlen($felder['name']) > 120 || preg_match('/[\r\n\x00-\x1f]/', $felder['name'])) $fehler['name'] = 'name';
    if (strlen($felder['email']) > 254 || !filter_var($felder['email'], FILTER_VALIDATE_EMAIL)) $fehler['email'] = 'email';
    if ($felder['nachricht'] === '' || mb_strlen($felder['nachricht']) > 10000 || !mb_check_encoding($felder['nachricht'], 'UTF-8') || str_contains($felder['nachricht'], "\0")) $fehler['nachricht'] = 'nachricht';
    return $fehler;
}

/** Shared, locked limiter: max. five attempts per hour and IP, no message storage. */
function kontakt_limit(string $ordner, string $ip, int $jetzt): bool
{
    if (!is_dir($ordner) && !@mkdir($ordner, 0700, true) && !is_dir($ordner)) throw new RuntimeException('Contact state unavailable');
    // Daily rotating filenames avoid permanent IP identifiers; old files expire.
    $datei = $ordner . '/' . hash('sha256', gmdate('Y-m-d', $jetzt) . ':' . $ip) . '.json';
    $handle = @fopen($datei, 'c+');
    if (!$handle) throw new RuntimeException('Contact limiter unavailable');
    @chmod($datei, 0600);
    try {
        if (!flock($handle, LOCK_EX)) throw new RuntimeException('Contact limiter lock failed');
        $zeiten = json_decode(stream_get_contents($handle), true);
        $zeiten = array_values(array_filter(is_array($zeiten) ? $zeiten : [], fn($t) => is_int($t) && $t > $jetzt - 3600));
        if (count($zeiten) >= 5) return false;
        $zeiten[] = $jetzt;
        ftruncate($handle, 0);
        rewind($handle);
        if (fwrite($handle, json_encode($zeiten)) === false) throw new RuntimeException('Contact limiter write failed');
    } finally {
        flock($handle, LOCK_UN);
        fclose($handle);
    }
    foreach (glob($ordner . '/*.json') ?: [] as $alt) {
        if (filemtime($alt) < $jetzt - 172800) @unlink($alt);
    }
    return true;
}

function kontakt_payload(array $felder, array $config): array
{
    return [
        'from' => $config['from'],
        'to' => [$config['to']],
        'reply_to' => $felder['email'],
        'subject' => 'Nachricht zur Jackie-Leven-Hommage',
        'text' => "Nachricht über das Mitmachen-Formular\n\nName: " . ($felder['name'] ?: '—')
            . "\nE-Mail: " . $felder['email'] . "\n\n" . $felder['nachricht'],
    ];
}

/** True only when Resend confirms acceptance with a message ID. No visitor auto-replies. */
function kontakt_senden(array $payload, string $key, string $token): bool
{
    if ($key === '' || !function_exists('curl_init')) return false;
    $curl = curl_init('https://api.resend.com/emails');
    curl_setopt_array($curl, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_HTTPHEADER => [
            'Authorization: Bearer ' . $key,
            'Content-Type: application/json',
            'Idempotency-Key: jackie-contact-' . $token,
        ],
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE),
    ]);
    $body = curl_exec($curl);
    $status = curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    curl_close($curl);
    $result = is_string($body) ? json_decode($body, true) : null;
    return $status >= 200 && $status < 300 && is_string($result['id'] ?? null) && $result['id'] !== '';
}

function kontakt_bearbeiten(): array
{
    header('Cache-Control: no-store');
    header('X-Robots-Tag: noindex');
    session_name('jackie_contact');
    session_start([
        'use_strict_mode' => 1,
        'cookie_httponly' => true,
        'cookie_secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'cookie_samesite' => 'Lax',
        'cookie_path' => '/',
    ]);
    $jetzt = time();
    $config = kontakt_config();
    $felder = ['name' => '', 'email' => '', 'nachricht' => ''];
    $fehler = [];
    $global = null;
    $status = 200;
    $erfolg = !empty($_SESSION['kontakt_erfolg']);
    unset($_SESSION['kontakt_erfolg']);
    if (($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST') {
        $erfolg = false;
        $felder = kontakt_felder($_POST);
        $token = is_string($_POST['token'] ?? null) ? $_POST['token'] : '';
        $formular = $_SESSION['kontakt_formulare'][$token] ?? null;
        if (!$formular || $formular['zeit'] < $jetzt - 7200) {
            $global = 'sitzung'; $status = 400;
        } elseif (!empty($_POST['website']) || $jetzt - $formular['zeit'] < 2 || $jetzt - ($_SESSION['kontakt_letzter_versand'] ?? 0) < 60) {
            $global = 'warten'; $status = 429;
        } elseif (($fehler = kontakt_pruefen($felder)) !== []) {
            $status = 422;
        } elseif ($config['key'] === '') {
            $global = 'konfiguration'; $status = 503;
        } else {
            try {
                if (!kontakt_limit($config['state'], $_SERVER['REMOTE_ADDR'] ?? 'unknown', $jetzt)) {
                    $global = 'warten'; $status = 429;
                } else {
                    // Keep one idempotency key for identical retries after a timeout.
                    $hash = hash('sha256', json_encode($felder, JSON_THROW_ON_ERROR));
                    $versand = $_SESSION['kontakt_formulare'][$token]['versand'][$hash] ?? bin2hex(random_bytes(16));
                    $_SESSION['kontakt_formulare'][$token]['versand'][$hash] = $versand;
                    if (!kontakt_senden(kontakt_payload($felder, $config), $config['key'], $versand)) {
                        $global = 'versand'; $status = 502;
                    } else {
                        unset($_SESSION['kontakt_formulare'][$token]);
                        $_SESSION['kontakt_letzter_versand'] = $jetzt;
                        $_SESSION['kontakt_erfolg'] = true;
                        session_write_close();
                        weiter(url('mitmachen') . '#nachricht', 303);
                    }
                }
            } catch (Throwable $e) {
                // Do not log message text, email addresses or API keys.
                error_log('Jackie contact: sending unavailable');
                $global = 'versand'; $status = 503;
            }
        }
    }
    // Keep a few independent forms for multiple browser tabs, with expiry.
    $formulare = array_filter($_SESSION['kontakt_formulare'] ?? [], fn($f) => $f['zeit'] >= $jetzt - 7200);
    $formulare = array_slice($formulare, -7, null, true);
    if (!isset($token) || !isset($formulare[$token])) $token = bin2hex(random_bytes(24));
    $formulare[$token] ??= ['zeit' => $jetzt];
    $_SESSION['kontakt_formulare'] = $formulare;
    session_write_close();
    if ($status === 429) header('Retry-After: 60');
    return compact('felder', 'fehler', 'global', 'status', 'erfolg', 'token') + ['bereit' => $config['key'] !== ''];
}
