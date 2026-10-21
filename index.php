<?php
declare(strict_types=1);

require __DIR__ . '/app/bootstrap.php';

/** Seiten mit übersetzten Pfadstücken (pfad.<name> in app/lang/<sprache>.php). */
const SEITEN = ['station', 'biografie', 'ueber'];

function nicht_gefunden(): never
{
    seite(render('404'), t('titel.404'), '', 404);
    exit;
}

$roh   = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$teile = array_values(array_filter(explode('/', $roh), fn($t) => $t !== ''));

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
        weiter(url('start', [], STANDARD_SPRACHE));
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
    seite(render('zeitreise', ['aktiv' => 0]), t('titel.start'), 'zeitreise');
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
        weiter(url('start'));                    // /de/zeitreise → /de/
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
seite(render_lokal($seite), t("titel.$seite"), $seite);
