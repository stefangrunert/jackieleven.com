<?php
/** php werkzeug/hoeren.php — Auswahl, Einbettungen, Sprachen und Routen. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function pruefe_hoeren(bool $ok, string $fehler): void
{
    if (!$ok) throw new RuntimeException($fehler);
}

$daten = require APP_ROOT . '/data/hoeren.php';
$stuecke = array_merge(...array_column($daten, 'stuecke'));
pruefe_hoeren(count($stuecke) === 10, 'Die Auswahl braucht genau zehn Stücke.');
pruefe_hoeren(count(array_unique(array_column($stuecke, 'song'))) === 10, 'Ein Stück steht doppelt in der Auswahl.');

libxml_use_internal_errors(true);
foreach (SPRACHEN as $s) {
    sprache($s);
    route('hoeren');
    $inhalt = render('hoeren');
    $html = render('layout', ['inhalt' => $inhalt, 'titel' => t('titel.hoeren'), 'nav' => 'hoeren', 'noindex' => false]);
    $dom = new DOMDocument();
    $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    libxml_clear_errors();
    $xp = new DOMXPath($dom);
    pruefe_hoeren($xp->query('//main[contains(@class,"hoer-seite")]//h1')->length === 1, 'Der Seitentitel fehlt für Hilfsmittel.');
    pruefe_hoeren($xp->query('//p[contains(@class,"hoer-intro")]/a[@href="' . url('diskografie') . '"]')->length === 1, 'Der Hinweis auf die Diskographie fehlt in ' . $s);
    pruefe_hoeren($xp->query('//main[contains(@class,"hoer-seite")]//article')->length === 10, 'Stücke fehlen in ' . $s);
    pruefe_hoeren($xp->query('//main[contains(@class,"hoer-seite")]//iframe')->length === 0, 'YouTube wird vor dem Klick geladen.');
    pruefe_hoeren($xp->query('//button[contains(@class,"hoer-video-laden")]')->length === 10, 'Ladeknöpfe fehlen in ' . $s);
    pruefe_hoeren($xp->query('//a[@data-music-link and contains(@href,"youtube.com/watch")]')->length === 10, 'YouTube-Rückfalllinks fehlen.');
    pruefe_hoeren(str_contains($html, '/assets/js/hoeren.js'), 'Einbettungsskript fehlt.');
    foreach ($stuecke as $stueck) {
        pruefe_hoeren(diskografie_index($stueck['release']) >= 0, 'Unbekannte Ausgabe: ' . $stueck['release']);
        $video = diskografie_youtube($stueck['song']);
        pruefe_hoeren($video !== null && preg_match('/^[A-Za-z0-9_-]{11}$/', youtube_video_id($video['url'])) === 1, 'Kein gültiges Video für ' . $stueck['song']);
    }
    pruefe_hoeren(alternativ_url($s) === url('hoeren', [], $s), 'Sprachwechsel verliert die Hören-Seite.');
}

foreach (['/de/hoeren' => 200, '/en/listen' => 200, '/de/listen' => 301, '/en/hoeren' => 301] as $path => $status) {
    $code = '$_SERVER["REQUEST_URI"] = ' . var_export($path, true) . ';'
        . 'register_shutdown_function(function () { fwrite(STDERR, "STATUS:" . http_response_code()); });'
        . 'require ' . var_export(__DIR__ . '/../index.php', true) . ';';
    $prozess = proc_open([PHP_BINARY, '-d', 'display_errors=1', '-r', $code], [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    $ausgabe = stream_get_contents($pipes[1]);
    $fehler = stream_get_contents($pipes[2]);
    fclose($pipes[1]); fclose($pipes[2]);
    pruefe_hoeren(proc_close($prozess) === 0 && $fehler === 'STATUS:' . $status, 'Route fehlgeschlagen: ' . $path . ' ' . $fehler);
    pruefe_hoeren(!str_contains($ausgabe, 'Warning:') && !str_contains($ausgabe, 'Fatal error:'), 'PHP-Ausgabe fehlerhaft: ' . $path);
}

echo "Hören: zehn Stücke, DE/EN, Klick-Einbettungen und Routen geprüft.\n";
