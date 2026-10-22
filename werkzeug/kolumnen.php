<?php
/** php werkzeug/kolumnen.php — Bestand, Texttreue und Navigation der Lesefassung. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function pruefe(bool $ok, string $fehler): void
{
    if (!$ok) {
        throw new RuntimeException($fehler);
    }
}

function schlicht(string $text): string
{
    return trim(preg_replace('/\s+/u', ' ', $text));
}

$liste = kolumnen();
$dateien = glob(APP_ROOT . '/../research/columns/*.md');
$dateien = array_filter($dateien, fn($f) => basename($f) !== 'README.md');
$bisTodesanzeige = array_filter($dateien, fn($f) => substr(basename($f), 0, 7) <= '2011-11');
pruefe(count($liste) === count($bisTodesanzeige), 'Der Katalog muss alle Texte bis zur Todesanzeige enthalten.');
pruefe(end($liste)['slug'] === '2011-11-home-the-great-scottish-singer-and-song-writer-jackie-leven', 'Die Sammlung muss mit der Todesanzeige vom November 2011 enden.');
foreach (array_diff($dateien, $bisTodesanzeige) as $datei) {
    $slug = str_replace('_', '-', basename($datei, '.md'));
    pruefe(kolumnen_index($slug) === -1, 'Spätere Texte dürfen auch über direkte Adressen nicht erreichbar sein.');
}
pruefe(count(array_unique(array_column($liste, 'slug'))) === count($liste), 'Doppelte Artikeladresse.');
$daten = array_column($liste, 'datum');
$sortiert = $daten;
sort($sortiert);
pruefe($daten === $sortiert, 'Die Texte sind nicht chronologisch sortiert.');
pruefe(kolumnen_index('../../README') === -1, 'Unbekannte Slugs müssen abgewiesen werden.');
pruefe(str_starts_with(kolumnen_lesetext($liste[0]), "I've been down in the deep pool"), 'Der erste Text soll direkt mit der Prosa beginnen.');

foreach ($liste as $i => $k) {
    pruefe(kolumnen_index($k['slug']) === $i, 'Slug nicht auflösbar: ' . $k['datei']);
    pruefe(str_starts_with($k['archiv'], 'https://web.archive.org/web/'), 'Archivlink fehlt: ' . $k['datei']);
    $html = kolumnen_html($k['text']);
    $original = preg_replace('/^-{3,}\s*$/m', '', $k['text']);
    $sichtbar = html_entity_decode(strip_tags($html), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    pruefe(schlicht($sichtbar) === schlicht($original), 'Wortlaut beim Rendern verändert: ' . $k['datei']);
    // Die Lesefassung entfernt nur führende Kopfzeilen; die Prosa bleibt vollständig.
    pruefe(str_ends_with($k['text'], kolumnen_lesetext($k)), 'Im Textkörper wurde etwas verändert.');
    foreach (SPRACHEN as $s) {
        sprache($s);
        $seite = render('kolumne', ['i' => $i]);
        pruefe(str_contains($seite, 'class="pool-intro"') === ($i === 0), 'Die Einführung darf nur über dem ersten Artikel stehen.');
        pruefe(substr_count($seite, 'class="g-marker pool-marker') === count($liste), 'Im Zeitstrahl fehlen Artikel.');
        pruefe(substr_count($seite, 'aria-current="page"') === 1, 'Der Zeitstrahl muss genau einen aktuellen Artikel anzeigen.');
        preg_match('/<a class="g-marker pool-marker[^"]* active"\s+href="([^"]+)"/', $seite, $aktiveMarke);
        pruefe(($aktiveMarke[1] ?? '') === e(url('kolumne', ['slug' => $k['slug']])), 'Der Zeitstrahl markiert bei gleichem Datum den falschen Beitrag.');
        pruefe(str_contains($seite, e(t('pool.intro'))) === ($i === 0), 'Einführung fehlt oder steht beim falschen Artikel.');
        pruefe(str_contains($seite, 'class="pool-original" lang="en"'), 'Originalsprache fehlt.');
        pruefe(str_contains($seite, e($k['archiv'])), 'Quellenlink fehlt.');
        pruefe(!preg_match('/\bpool\.(?:art|datum|archiv|original|hinweis)/', $seite), 'Oberflächentext fehlt.');
        if ($i > 0) {
            pruefe(str_contains($seite, e(url('kolumne', ['slug' => $liste[$i - 1]['slug']])) . '" rel="prev"'), 'Vorheriger Text falsch.');
        } else {
            pruefe(!str_contains($seite, 'rel="prev"'), 'Erster Text hat einen Vorgänger.');
        }
        if ($i < count($liste) - 1) {
            pruefe(str_contains($seite, e(url('kolumne', ['slug' => $liste[$i + 1]['slug']])) . '" rel="next"'), 'Nächster Text falsch.');
        } else {
            pruefe(!str_contains($seite, 'rel="next"'), 'Letzter Text hat einen Nachfolger.');
        }
        if ($k['autor'] !== 'Jackie Leven') {
            pruefe(str_contains($seite, e(t('pool.webmaster'))), 'Mitteilung falsch zugeschrieben.');
        }
    }
}

foreach (SPRACHEN as $s) {
    sprache($s);
    $zeitstrahl = render('pool-zeitstrahl', ['liste' => $liste, 'aktiv' => 0]);
    preg_match_all('/href="([^"]+)"/', $zeitstrahl, $ziele);
    pruefe($ziele[1] === array_map(fn($k) => e(url('kolumne', ['slug' => $k['slug']])), $liste), 'Zeitstrahl muss jeden Beitrag über seine eigene Adresse verlinken.');
    preg_match_all('/aria-label="([^"]+)"/', $zeitstrahl, $namen);
    pruefe(count($namen[1]) === count(array_unique($namen[1])), 'Auch gleich datierte Beiträge brauchen eindeutige Navigationsnamen.');
    $html = render('pool');
    pruefe(!str_contains($html, 'pool-auswahl'), 'Die redaktionelle Auswahl wurde entfernt.');
    pruefe(str_contains(render('kolumne', ['i' => 0]), e(url('pool_archiv')) . '#jahr-2002'), 'Das Archiv ist vom ersten Text aus nicht erreichbar.');
    foreach ($liste as $k) {
        pruefe(str_contains($html, e(url('kolumne', ['slug' => $k['slug']]))), 'Text fehlt in der Übersicht.');
    }
}
pruefe(str_contains(kolumnen_html('<script>alert("x")</script>'), '&lt;script&gt;'), 'Originaltext wird als HTML ausgeführt.');
echo count($liste) . " Texte: Wortlaut, Chronologie, Quellen, Übersicht und Navigation in DE/EN geprüft.\n";
