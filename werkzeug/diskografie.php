<?php
/** php werkzeug/diskografie.php — Katalog, Identitäten, Quellen und Sprachfassungen. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function pruefe_disk(bool $ok, string $fehler): void
{
    if (!$ok) throw new RuntimeException($fehler);
}

$daten = diskografie();
$platten = $daten['releases'];
$ids = array_column($platten, 'id');
pruefe_disk(count($ids) === count(array_unique($ids)), 'Doppelte Plattenadresse.');
$jahre = array_column($platten, 'year');
$sortiert = $jahre;
sort($sortiert);
pruefe_disk($jahre === $sortiert, 'Der Katalog ist nicht chronologisch.');
$projekte = array_keys(diskografie_projekte());
$vorhanden = [];
foreach ($platten as $platte) {
    pruefe_disk(preg_match('/^\d{4}-[a-z0-9-]+$/', $platte['id']) === 1, 'Ungültige Plattenadresse.');
    pruefe_disk($platte['sources'] !== [], 'Quellen fehlen: ' . $platte['id']);
    foreach ($platte['sources'] as $quelle) {
        pruefe_disk(isset($daten['sources'][$quelle]), 'Unbekannte Quelle: ' . $quelle);
        pruefe_disk(filter_var($daten['sources'][$quelle]['url'], FILTER_VALIDATE_URL) !== false, 'Ungültige Quellenadresse.');
    }
    foreach ($platte['tags'] as $projekt) {
        pruefe_disk(in_array($projekt, $projekte, true), 'Unbekanntes Projekt: ' . $projekt);
        $vorhanden[$projekt] = true;
    }
    foreach (SPRACHEN as $s) {
        pruefe_disk(isset($platte['notes'][$s]), 'Sprachfassung der Anmerkung fehlt.');
        pruefe_disk(t('disk.type.' . $platte['kind'], [], $s) !== 'disk.type.' . $platte['kind'], 'Ausgabenart fehlt.');
    }
}
pruefe_disk(count($vorhanden) === count($projekte), 'Ein Alias oder Projekt fehlt im Katalog.');

foreach (SPRACHEN as $s) {
    sprache($s);
    $html = render('diskografie');
    libxml_use_internal_errors(true);
    $dom = new DOMDocument();
    $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    libxml_clear_errors();
    $xpath = new DOMXPath($dom);
    pruefe_disk($xpath->query('//article')->length === count($platten), 'Einträge fehlen in ' . $s);
    $alleIds = [];
    foreach ($xpath->query('//*[@id]') as $element) $alleIds[] = $element->getAttribute('id');
    pruefe_disk(count($alleIds) === count(array_unique($alleIds)), 'Doppelte HTML-ID in ' . $s);
    foreach ($xpath->query('//a[starts-with(@href, "#")]') as $link) {
        pruefe_disk(in_array(substr($link->getAttribute('href'), 1), $alleIds, true), 'Sprungziel fehlt.');
    }
    foreach ($ids as $id) {
        pruefe_disk($xpath->query('//article[@id="' . $id . '"]')->length === 1, 'Platte nicht eindeutig erreichbar: ' . $id);
    }
    pruefe_disk(!preg_match('/>disk\.[a-z_]+</', $html), 'Unübersetzter Oberflächentext.');
    route('diskografie');
    pruefe_disk(alternativ_url($s) === url('diskografie', [], $s), 'Sprachwechsel verliert die Route.');
}
echo count($platten) . " Einträge: Chronologie, Aliasse, Quellen, Sprungziele und DE/EN geprüft.\n";
