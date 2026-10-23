<?php
/** Build and verify a complete release without uploading or sending mail. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function release_pruefe(bool $ok, string $nachricht): void
{
    if (!$ok) throw new RuntimeException($nachricht);
}

function release_prozess(array $befehl): string
{
    $prozess = proc_open($befehl, [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    $ausgabe = stream_get_contents($pipes[1]);
    $fehler = stream_get_contents($pipes[2]);
    fclose($pipes[1]); fclose($pipes[2]);
    release_pruefe(proc_close($prozess) === 0 && $fehler === '', 'Release-Prüfung fehlgeschlagen: ' . $fehler);
    return $ausgabe;
}

$temp = sys_get_temp_dir() . '/jackie-release-test-' . bin2hex(random_bytes(8));
mkdir($temp, 0700);
$paket = $temp . '/release';
try {
    release_prozess([PHP_BINARY, __DIR__ . '/../ops/prepare-release.php', $paket]);
    $manifest = [];
    foreach (file($paket . '/release-manifest.sha256', FILE_IGNORE_NEW_LINES) as $zeile) {
        [$hash, $pfad] = explode('  ', $zeile, 2);
        release_pruefe(hash_file('sha256', $paket . '/' . $pfad) === $hash, 'Prüfsumme falsch: ' . $pfad);
        $manifest[$pfad] = true;
        release_pruefe(!preg_match('~(^|/)(\.git|\.dev|ops|werkzeug|sketches|config\.local\.php|grafik-entwuerfe|grafik-vorlagen)(/|$)~', $pfad), 'Arbeitsdatei im Release: ' . $pfad);
        if (str_starts_with($pfad, 'public/')) {
            release_pruefe(in_array($pfad, ['public/index.php', 'public/.htaccess'], true) || str_starts_with($pfad, 'public/assets/'), 'Private Datei im Webroot: ' . $pfad);
        }
    }
    foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($paket, FilesystemIterator::SKIP_DOTS)) as $datei) {
        $relativ = substr($datei->getPathname(), strlen($paket) + 1);
        release_pruefe(!$datei->isLink() && (isset($manifest[$relativ]) || $relativ === 'release-manifest.sha256'), 'Unerwartete Datei im Paket: ' . $relativ);
    }
    $bestand = require APP_ROOT . '/data/kolumnen.php';
    $kolumnen = glob($paket . '/research/columns/*.md');
    release_pruefe(count($kolumnen) === count($bestand['dateien']), 'Nicht freigegebene oder fehlende Kolumne im Release');
    release_pruefe(!is_dir($paket . '/research/quellen') && !is_file($paket . '/autobiografie/00-rahmen.md'), 'Recherche oder Buchplanung im Release');
    release_pruefe(!is_file($paket . '/app/config.local.php'), 'Lokale Zugangsdaten im Release');

    foreach (SPRACHEN as $s) {
        $pfade = [url('start', [], $s), url('zeitreise', [], $s), url('pool_archiv', [], $s),
            url('kolumne', ['slug' => kolumnen()[0]['slug']], $s),
            url('kolumne', ['slug' => kolumnen()[count(kolumnen()) - 1]['slug']], $s),
            url('diskografie', [], $s), url('hoeren', [], $s), url('biografie', [], $s),
            url('ueber', [], $s), url('impressum', [], $s), url('mitmachen', [], $s)];
        foreach (stationen() as $station) $pfade[] = url('station', ['slug' => $station['slug']], $s);
        foreach (kapitelliste() as $kapitel) $pfade[] = url('kapitel', ['slug' => $kapitel['slug']], $s);
        foreach (diskografie()['releases'] as $platte) $pfade[] = url('platte', ['slug' => $platte['id']], $s);
        foreach ($pfade as $pfad) {
            $code = 'ini_set("session.save_path", ' . var_export($temp, true) . ');'
                . 'putenv("JACKIE_RESEND_API_KEY=");'
                . '$_SERVER["REQUEST_URI"]=' . var_export($pfad, true) . ';'
                . 'register_shutdown_function(function () { if (http_response_code() !== 200) exit(1); });'
                . 'require ' . var_export($paket . '/public/index.php', true) . ';';
            $html = release_prozess([PHP_BINARY, '-d', 'display_errors=stderr', '-r', $code]);
            release_pruefe(!str_contains($html, 'Warning:') && !str_contains($html, 'Fatal error:'), 'Fehler in Release-Route: ' . $pfad);
            preg_match_all('~(?:src|href)="(/assets/[^"?]+)~', $html, $assets);
            foreach ($assets[1] as $asset) release_pruefe(isset($manifest['public' . $asset]), 'Asset fehlt: ' . $asset);
        }
    }
    // The same CLI checks all rendering with fan videos enabled as well.
    $code = 'putenv("JACKIE_FAN_VIDEOS=1"); define("PUBLIC_ROOT", ' . var_export($paket . '/public', true) . ');'
        . 'require ' . var_export($paket . '/app/bootstrap.php', true) . ';'
        . 'foreach (diskografie()["releases"] as $platte) echo render("platte", ["platte"=>$platte, "kontext"=>[]]);';
    $html = release_prozess([PHP_BINARY, '-d', 'display_errors=stderr', '-r', $code]);
    preg_match_all('~src="(/assets/[^"?]+)~', $html, $assets);
    foreach ($assets[1] as $asset) release_pruefe(isset($manifest['public' . $asset]), 'Fan-Vorschau fehlt: ' . $asset);
    echo count($manifest) . " Release-Dateien: Prüfsummen, private Inhalte, alle Seiten und lokale Assets in DE/EN geprüft; kein Upload.\n";
} finally {
    $dateien = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($temp, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($dateien as $datei) {
        if ($datei->isDir() && !$datei->isLink()) rmdir($datei->getPathname());
        else unlink($datei->getPathname());
    }
    rmdir($temp);
}
