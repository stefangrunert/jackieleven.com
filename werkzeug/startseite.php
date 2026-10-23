<?php
/** php werkzeug/startseite.php — Einstieg, Quellenbezug und getrennte Zeitreise. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function pruefe_start(bool $ok, string $fehler): void
{
    if (!$ok) throw new RuntimeException($fehler);
}

libxml_use_internal_errors(true);
foreach (SPRACHEN as $s) {
    sprache($s);
    route('start');
    $html = render('layout', ['inhalt' => render('start'), 'titel' => t('titel.start'), 'nav' => 'start', 'noindex' => false]);
    $dom = new DOMDocument();
    $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    libxml_clear_errors();
    $xp = new DOMXPath($dom);
    pruefe_start($xp->query('//h1')->length === 1, 'Startseite braucht einen eindeutigen Titel.');
    pruefe_start($xp->query('//section[contains(@class,"home-auftakt")]/following-sibling::*[1][self::section[contains(@class,"home-hoeren")]]')->length === 1, 'Hören steht nicht direkt unter dem Auftakt.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//*[@data-youtube-id="XLmSL2QBoy0"]//img[contains(@src,"main-travelled-roads-preview.webp")]')->length === 1, 'Eigenes Vorschaubild des Startseitenvideos fehlt.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//button[@data-youtube-id="3pcJw_Zjf94"]')->length === 1, 'Zweites Startseitenvideo fehlt.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//button[@data-youtube-id="3pcJw_Zjf94" and contains(@data-youtube-preview,"rockpalast-2004-preview.webp")]')->length === 1, 'Vorschaubild des zweiten Startseitenvideos fehlt.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//button[@data-youtube-id="J65SKEqdAWY" and contains(@data-youtube-preview,"jackie-leven-at-70-preview-v2.webp")]')->length === 1, 'Tribute als drittes Startseitenvideo fehlt.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//iframe')->length === 0, 'YouTube wird vor dem Klick geladen.');
    pruefe_start($xp->query('//section[contains(@class,"home-hoeren")]//ol/li')->length === 3, 'Startseiten-Playlist braucht drei Plätze.');
    pruefe_start(str_contains($html, '/assets/js/startseite.js'), 'Playlist-Steuerung der Startseite fehlt.');
    pruefe_start(!str_contains(file_get_contents(__DIR__ . '/../assets/js/startseite.js'), 'autoplay=1'), 'Startseitenvideos dürfen nicht automatisch abspielen.');
    pruefe_start(str_contains($html, e(t('fuss.hommage'))), 'Hinweis auf inoffizielle Hommage fehlt.');
    pruefe_start(!preg_match('/>home\.[a-z_.]+</', $html), 'Unübersetzter Startseitentext.');
    $hrefs = [];
    foreach ($xp->query('//a[@href]') as $link) $hrefs[] = $link->getAttribute('href');
    foreach (['zeitreise', 'diskografie', 'pool', 'biografie', 'ueber'] as $ziel) {
        pruefe_start(in_array(url($ziel), $hrefs, true), 'Rubrik fehlt: ' . $ziel);
    }
    foreach (['1950-kirkcaldy', '2011-november'] as $slug) {
        pruefe_start(in_array(url('station', ['slug' => $slug]), $hrefs, true), 'Anfang oder Ende des Lebensbogens fehlt.');
    }
    foreach ($xp->query('//img[starts-with(@src, "/assets/")]') as $img) {
        pruefe_start(is_file(__DIR__ . '/..' . $img->getAttribute('src')), 'Lokale Illustration fehlt.');
    }
    $daten = require APP_ROOT . '/data/startseite.php';
    $auszuege = $xp->query('//article[@class="home-auszug"]//blockquote');
    pruefe_start($auszuege->length === 2, 'Zwei belegte Textauszüge erwartet.');
    foreach (['pool', 'leben'] as $i => $key) {
        $quote = trim($auszuege->item($i)->textContent);
        $quelle = kolumnen()[kolumnen_index($daten[$key]['slug'])];
        $original = preg_replace('/\s+/', ' ', $quelle['text']);
        // Die fehlende Initiale im archivierten Ed-Text ist im Entwurf ergänzt.
        if ($key === 'leben') $original = str_replace('he death of my brother', 'The death of my brother', $original);
        foreach (explode('…', $quote) as $teil) {
            $teil = trim($teil, " .\t\n\r");
            if ($teil !== '') pruefe_start(str_contains($original, $teil), 'Auszug weicht vom Original ab: ' . $key);
        }
        pruefe_start($auszuege->item($i)->getAttribute('cite') === $quelle['archiv'], 'Zitatquelle fehlt: ' . $key);
    }
    pruefe_start($xp->query('//button[@aria-controls="home-menu"]')->length === 1, 'Mobiles Menü fehlt.');
    pruefe_start(!str_contains($xp->query('//footer')->item(0)->textContent, '1950'), 'Lebensdaten wieder im Footer.');
    pruefe_start(!str_contains($html, '↗'), 'Diagonale Linkpfeile wieder eingeführt.');
    foreach (SPRACHEN as $ziel) pruefe_start(alternativ_url($ziel) === url('start', [], $ziel), 'Startseiten-Sprachwechsel fehlerhaft.');
    route('zeitreise');
    foreach (SPRACHEN as $ziel) pruefe_start(alternativ_url($ziel) === url('zeitreise', [], $ziel), 'Zeitreise-Sprachwechsel führt zur Startseite.');
    pruefe_start(url('start') !== url('zeitreise'), 'Startseite und Zeitreise haben dieselbe Adresse.');
    pruefe_start(str_contains(render_lokal('biografie'), 'href="' . url('zeitreise') . '"'), 'Biografie-Link führt nicht zur Zeitreise.');
}

// Den echten Frontcontroller in getrennten Prozessen prüfen, einschließlich
// bestehender Stationsadressen und der bisherigen sprachlosen Zeitreise.
foreach ([
    '/' => 302, '/de' => 301, '/de/' => 200, '/en/' => 200,
    '/de/zeitreise' => 200, '/en/timeline' => 200, '/zeitreise' => 301,
    '/de/timeline' => 301, '/en/zeitreise' => 301,
    '/de/zeitreise/1950-kirkcaldy' => 200,
    '/en/timeline/2011-november' => 200,
    '/de/zeitreise/unbekannt' => 404,
    '/de/zeitreise/2011-ed' => 200, '/en/timeline/2011-ed' => 200,
    '/de/deep-pool/2009-12-home-specialnote' => 200,
    '/en/deep-pool/2009-12-home-specialnote' => 200,
    '/de/diskografie/1994-the-mystery-of-love-is-greater-than-the-mystery-of-death' => 200,
    '/en/discography/1994-the-mystery-of-love-is-greater-than-the-mystery-of-death' => 200,
] as $path => $status) {
    $code = '$_SERVER["REQUEST_URI"] = ' . var_export($path, true) . ';'
        . 'register_shutdown_function(function () { fwrite(STDERR, "STATUS:" . http_response_code()); });'
        . 'require ' . var_export(__DIR__ . '/../index.php', true) . ';';
    $prozess = proc_open([PHP_BINARY, '-d', 'display_errors=1', '-r', $code], [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    $ausgabe = stream_get_contents($pipes[1]);
    $fehler = stream_get_contents($pipes[2]);
    fclose($pipes[1]); fclose($pipes[2]);
    pruefe_start(proc_close($prozess) === 0 && $fehler === 'STATUS:' . $status, 'Route fehlgeschlagen: ' . $path . ' ' . $fehler);
    pruefe_start(!str_contains($ausgabe, 'Warning:') && !str_contains($ausgabe, 'Fatal error:'), 'PHP-Ausgabe fehlerhaft: ' . $path);
    if (in_array($path, ['/de/', '/en/'], true)) pruefe_start(str_contains($ausgabe, 'class="home"'), 'Startseite zeigt weiterhin die Zeitreise.');
    if (in_array($path, ['/de/zeitreise', '/en/timeline'], true)) pruefe_start(str_contains($ausgabe, 'id="stage"'), 'Zeitreise nicht erreichbar.');
}
echo "Startseite und Zeitreise: DE/EN, Lebensbogen, Hommage-Hinweis, Originalauszüge, Menü, Links und Routen geprüft.\n";
