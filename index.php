<?php
declare(strict_types=1);

require __DIR__ . '/app/bootstrap.php';

/** Seiten mit übersetzten Pfadstücken (pfad.<name> in app/lang/<sprache>.php). */
const SEITEN = ['station', 'biografie', 'pool', 'diskografie', 'stimmen', 'hoeren', 'ueber', 'mitmachen', 'impressum'];

function nicht_gefunden(): never
{
    seite(render('404'), t('titel.404'), '', 404);
    exit;
}

$roh   = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$teile = array_values(array_filter(explode('/', $roh), fn($t) => $t !== ''));

// Machine-readable discovery endpoints also work in the packaged release.
if ($roh === '/robots.txt') {
    http_response_code(200);
    header('Content-Type: text/plain; charset=utf-8');
    echo seo_live()
        ? "User-agent: *\nAllow: /\nSitemap: " . SEO_ORIGIN . "/sitemap.xml\n"
        : "User-agent: *\nDisallow: /\n";
    exit;
}
if ($roh === '/sitemap.xml') {
    http_response_code(200);
    header('Content-Type: application/xml; charset=utf-8');
    if (!seo_live()) header('X-Robots-Tag: noindex');
    echo seo_sitemap();
    exit;
}


// "/" → die Sprache, die der Browser bevorzugt
if ($teile === []) {
    header('Vary: Accept-Language');
    weiter(url('start', [], bevorzugte_sprache()), 302);
}

// Adressen ohne Sprachpräfix, wie sie bis September 2026 galten → deutsche Fassung
if (!in_array($teile[0], SPRACHEN, true)) {
    sprache(bevorzugte_sprache());   // nur für eine etwaige 404-Seite
    [$alt, $rest] = [$teile[0], count($teile)];
    if ($alt === 'zeitreise' && $rest === 1) {
        weiter(url('zeitreise', [], STANDARD_SPRACHE));
    }
    if ($alt === 'station' && $rest === 2) {
        weiter(url('station', ['slug' => SLUG_ALIAS[$teile[1]] ?? $teile[1]], STANDARD_SPRACHE));
    }
    if (in_array($alt, ['biografie', 'ueber'], true) && $rest === 1) {
        weiter(url($alt, [], STANDARD_SPRACHE));
    }
    nicht_gefunden();
}

sprache(array_shift($teile));

// Startseite: /de/  (und /de ohne Schrägstrich dorthin)
if ($teile === []) {
    if (!str_ends_with($roh, '/')) {
        weiter(url('start'));
    }
    route('start');
    seite(render('start'), t('titel.start'), 'start');
    exit;
}

// Welche Seite meint das Pfadstück? Auch in einer anderen Sprache geschrieben
// wird es erkannt und auf die Form der aktuellen Sprache umgeleitet.
$seite = null;
foreach (SEITEN as $kandidat) {
    foreach (SPRACHEN as $s) {
        if (t("pfad.$kandidat", [], $s) === $teile[0]) {
            $seite = $kandidat;
            break 2;
        }
    }
}
if ($seite === null) {
    nicht_gefunden();
}
$richtig = $teile[0] === t("pfad.$seite");

if ($seite === 'station') {
    if (count($teile) === 1) {
        if (!$richtig) weiter(url('zeitreise'));
        route('zeitreise');
        seite(render('zeitreise', ['aktiv' => 0]), t('titel.zeitreise'), 'zeitreise');
        exit;
    }
    if (count($teile) !== 2) {
        nicht_gefunden();
    }
    $slug = $teile[1];
    if (isset(SLUG_ALIAS[$slug])) {
        weiter(url('station', ['slug' => SLUG_ALIAS[$slug]]));
    }
    $i = stations_index($slug);
    if ($i < 0) {
        nicht_gefunden();
    }
    if (!$richtig) {
        weiter(url('station', ['slug' => $slug]));
    }
    $st = stationen()[$i];

    // Teilantwort für den Stationswechsel ohne Seitenwechsel (zeitgraph.js)
    if (($_GET['fragment'] ?? '') === '1') {
        header('Content-Type: text/html; charset=utf-8');
        header('Content-Language: ' . sprache());
        header('X-Robots-Tag: noindex');
        header('Link: <' . absolut(url('station', ['slug' => $slug])) . '>; rel="canonical"');
        echo render('buehne', ['st' => $st]);
        exit;
    }

    route('station', ['slug' => $slug]);
    [$titel] = sfeld($st, 'titel');
    seite(
        render('zeitreise', ['aktiv' => $i]),
        t('titel.station', ['jahr' => $st['jahr'], 'titel' => $titel]),
        'zeitreise'
    );
    exit;
}

// Die Rubrik beginnt mit dem ersten Text; das Archiv bleibt separat erreichbar.
if ($seite === 'pool') {
    if (count($teile) === 1) {
        weiter(url('kolumne', ['slug' => kolumnen()[0]['slug']]), 302);
    }
    if (count($teile) === 2 && in_array($teile[1], array_map(fn($s) => t('pfad.pool_archiv', [], $s), SPRACHEN), true)) {
        if ($teile[1] !== t('pfad.pool_archiv')) {
            weiter(url('pool_archiv'));
        }
        route('pool_archiv');
        seite(render('pool'), t('titel.pool_archiv'), 'pool');
        exit;
    }
    if (count($teile) !== 2 || ($i = kolumnen_index($teile[1])) < 0) {
        nicht_gefunden();
    }
    $k = kolumnen()[$i];
    route('kolumne', ['slug' => $k['slug']]);
    seite(render('kolumne', ['i' => $i]), t('titel.kolumne', [
        'datum' => kolumnen_datum($k), 'rubrik' => kolumnen_rubrik($k),
    ]), 'pool');
    exit;
}

// Jede im Katalog geführte Ausgabe hat ihre eigene Detailseite.
if ($seite === 'diskografie' && count($teile) === 2) {
    $i = diskografie_index($teile[1]);
    if ($i < 0) nicht_gefunden();
    $kontext = diskografie_kontext($_GET);
    if (!$richtig) weiter(diskografie_link($teile[1], $kontext));
    $platte = diskografie()['releases'][$i];
    route('platte', ['slug' => $platte['id']]);
    seite(render('platte', ['platte' => $platte, 'kontext' => $kontext]),
        $platte['title'] . ' · ' . $platte['year'] . ' · ' . t('nav.diskografie'), 'diskografie');
    exit;
}

// Jede Quelle mit eigener Seite: /de/stimmen/1998-03-06-nordlys-live-med-leven
if ($seite === 'stimmen' && count($teile) === 2) {
    $i = stimme_index($teile[1]);
    if ($i < 0) nicht_gefunden();
    if (!$richtig) weiter(stimme_link($teile[1]));
    route('quelle', ['slug' => $teile[1]]);
    seite(render('quelle', ['i' => $i]), stimme_feld(stimmen()[$i], 'titel') . ' · ' . t('nav.stimmen'), 'stimmen');
    exit;
}

// Kapitel der Pastiche: /de/biografie/07-electric-fur
if ($seite === 'biografie' && count($teile) === 2) {
    $i = kapitel_index($teile[1]);
    if ($i < 0) {
        nicht_gefunden();
    }
    if (!$richtig) {
        weiter(url('kapitel', ['slug' => $teile[1]]));
    }
    $k = kapitelliste()[$i];
    route('kapitel', ['slug' => $k['slug']]);
    seite(
        render('kapitel', ['i' => $i]),
        t('titel.kapitel', ['titel' => $k['titel'], 'nr' => $i + 1]),
        'biografie',
        200,
        noindex: true
    );
    exit;
}

if (count($teile) !== 1) {
    nicht_gefunden();
}
if (!$richtig) {
    weiter(url($seite));
}
route($seite);
if ($seite === 'mitmachen') {
    require APP_ROOT . '/kontakt.php';
    $formular = kontakt_bearbeiten();
    seite(render('mitmachen', $formular), t('titel.mitmachen'), 'mitmachen', $formular['status']);
    exit;
}
if ($seite === 'diskografie') {
    seite(render('diskografie'), t('titel.diskografie'), 'diskografie');
    exit;
}
if ($seite === 'stimmen') {
    seite(render('stimmen', ['filter' => stimmen_filter($_GET)]), t('titel.stimmen'), 'stimmen');
    exit;
}
if ($seite === 'hoeren') {
    seite(render('hoeren'), t('titel.hoeren'), 'hoeren');
    exit;
}
seite(render_lokal($seite), t("titel.$seite"), $seite);
