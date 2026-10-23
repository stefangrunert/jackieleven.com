<?php
/** php werkzeug/stimmen.php — Stimmen: öffentliche Daten, Übersicht, Detailseiten, Lizenzen, DE/EN. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

function pruefe_stimmen(bool $ok, string $fehler): void
{
    if (!$ok) throw new RuntimeException($fehler);
}

$quellen = stimmen();
$ids = array_column($quellen, 'id');
pruefe_stimmen(count($ids) === count(array_unique($ids)), 'Doppelte Quellen-ID.');
$releases = array_column(diskografie()['releases'], 'id');
foreach ($quellen as $q) {
    pruefe_stimmen(preg_match('/^[a-z0-9-]+$/', $q['id']) === 1 && $q['titel'] !== '' && $q['medium'] !== '', 'Quelle unvollständig: ' . $q['id']);
    pruefe_stimmen(in_array($q['stufe'], ['auswahl', 'verzeichnis', 'weitere'], true), 'Interne oder unbekannte Stufe öffentlich: ' . $q['id']);
    pruefe_stimmen(in_array($q['kategorie'], stimmen_kategorien(), true) && in_array($q['zugang'], stimmen_zugaenge(), true), 'Unbekannte Art oder Zugang: ' . $q['id']);
    pruefe_stimmen($q['datum'] === '' || preg_match('/^\d{4}(-\d{2}(-\d{2})?)?$/', $q['datum']) === 1, 'Datum ungültig: ' . $q['id']);
    pruefe_stimmen($q['url'] !== '' || $q['archiv'] !== '' || $q['zugang'] === 'verloren', 'Quelle ohne Link: ' . $q['id']);
    pruefe_stimmen($q['lizenz'] === null || (str_contains($q['url'], 'nb.no') && $q['zugang'] === 'frei'), 'Freie Lizenz ohne Nationalbibliothek: ' . $q['id']);
    pruefe_stimmen($q['kurz']['de'] !== '' && $q['inhalt']['de'] !== [], 'Inhaltsangabe fehlt: ' . $q['id']);
    $text = json_encode([$q['kurz'], $q['inhalt'], $q['zitate']], JSON_UNESCAPED_UNICODE);
    pruefe_stimmen(!preg_match('~research/|\.md\b|gefunden_ueber|\bsicherheit:~', $text), 'Interner Verweis im öffentlichen Text: ' . $q['id']);
    foreach ($q['ausgaben'] as $id) pruefe_stimmen(in_array($id, $releases, true), 'Unbekannte Ausgabe bei ' . $q['id']);
    if (stimme_mit_seite($q)) {
        pruefe_stimmen(($q['kurz']['en'] ?? '') !== '' && count($q['inhalt']['en'] ?? []) === count($q['inhalt']['de']), 'Englische Fassung fehlt oder ist veraltet (werkzeug/quellen.php): ' . $q['id']);
        foreach ($q['zitate'] as $zitat) pruefe_stimmen($zitat['kontext'] === '' || ($zitat['kontext_en'] ?? '') !== '', 'Zitathinweis ohne Übersetzung: ' . $q['id']);
    }
    $klammer = preg_match('/^\[([^\]]*)\]/u', $q['titel'], $m) ? $m[1] : '';
    pruefe_stimmen(isset($q['en']['titel']) || !preg_match('/\b(und|mit|vor|nach|über|ohne|Konzert\w*|Vorbericht|Bericht|Kurzkritik|Rezension|Kommentare|Gästebuch|Sammeldatei|Ausgabe)\b/u', $klammer), 'Beschreibender Titel ohne Übersetzung: ' . $q['id']);
}
pruefe_stimmen(count(array_filter($quellen, fn($q) => $q['stufe'] === 'auswahl')) >= 20, 'Zu wenige ausgewählte Quellen.');
pruefe_stimmen(stimmen_filter(['art' => 'interviews', 'sprache' => ['x'], 'zugang' => 'gibtsnicht', 'fremd' => 1]) === ['art' => 'interviews'], 'Filter übernimmt unbekannte Werte.');
$norwegisch = array_filter($quellen, fn($q) => stimme_passt($q, ['sprache' => 'no']));
pruefe_stimmen($norwegisch !== [] && array_filter($norwegisch, fn($q) => !in_array($q['sprache'], ['no', 'nn'], true)) === [], 'Sprachfilter Norwegisch falsch.');

libxml_use_internal_errors(true);
$seiten = 0;
foreach (SPRACHEN as $s) {
    sprache($s);
    $dom = new DOMDocument();
    route('stimmen');
    $html = render('layout', ['inhalt' => render('stimmen', ['filter' => []]), 'titel' => t('titel.stimmen'), 'nav' => 'stimmen', 'noindex' => false]);
    $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    $xp = new DOMXPath($dom);
    pruefe_stimmen($xp->query('//h1')->length === 1, 'Übersicht ohne Titel.');
    pruefe_stimmen($xp->query('//article[contains(@class,"stimme ")]')->length === count(array_filter($quellen, 'stimme_mit_seite')), 'Quellen fehlen in der Übersicht (' . $s . ').');
    pruefe_stimmen($xp->query('//details[@class="stimmen-weitere"]//li')->length === count(array_filter($quellen, fn($q) => !stimme_mit_seite($q))), 'Weitere Quellen fehlen (' . $s . ').');
    pruefe_stimmen($xp->query('//img | //iframe')->length === 1, 'Bilder oder Player auf der Übersicht.'); // nur das Logo
    pruefe_stimmen($xp->query('//nav//a[@aria-current="page" and @href="' . url('stimmen') . '"]')->length === 1, 'Navigation markiert die Seite nicht.');
    pruefe_stimmen(!preg_match('/>stimmen\.[a-z_.-]+</', $html), 'Unübersetzter Text auf der Übersicht.');
    pruefe_stimmen(alternativ_url($s === 'de' ? 'en' : 'de') === url('stimmen', [], $s === 'de' ? 'en' : 'de'), 'Sprachwechsel verliert die Übersicht.');

    foreach ($quellen as $i => $q) {
        if (!stimme_mit_seite($q)) continue;
        route('quelle', ['slug' => $q['id']]);
        $html = render('quelle', ['i' => $i]);
        $dom = new DOMDocument();
        $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
        $xp = new DOMXPath($dom);
        pruefe_stimmen($xp->query('//h1[@lang]')->length === 1, 'Detailseite ohne Titel: ' . $q['id']);
        pruefe_stimmen($xp->query('//section[@class="stimme-quelle"]//a[@target="_blank"]')->length >= ($q['zugang'] === 'verloren' ? 0 : 1), 'Detailseite ohne Quellenlink: ' . $q['id']);
        pruefe_stimmen($xp->query('//*[@src]')->length === 0, 'Externe Ressource auf der Detailseite: ' . $q['id']);
        if ($q['lizenz']) {
            $lizenz = $xp->query('//p[@class="stimme-lizenz"]//a[contains(@rel,"license")]');
            pruefe_stimmen($lizenz->length === 1 && str_starts_with($lizenz[0]->getAttribute('href'), 'https://creativecommons.org/licenses/by-nc'), 'Namensnennung oder Lizenz fehlt: ' . $q['id']);
            pruefe_stimmen(str_contains($html, e($q['medium'])), 'Medium fehlt in der Namensnennung: ' . $q['id']);
        }
        if ($s === 'en') pruefe_stimmen(!str_contains($html, e(t('stimmen.nur_deutsch'))) && $xp->query('//div[@lang="de"]')->length === 0, 'Englische Seite zeigt die deutsche Zusammenfassung: ' . $q['id']);
        pruefe_stimmen(alternativ_url('de') === stimme_link($q['id']) || $s === 'en', 'Sprachwechsel verliert die Quelle.');
        $seiten++;
    }
}
sprache('de');
$platte = diskografie()['releases'][diskografie_index('1998-night-lilies-album')];
pruefe_stimmen(substr_count(render('platte', ['platte' => $platte, 'kontext' => []]), 'href="/de/stimmen/') === count(stimmen_zur_ausgabe('1998-night-lilies-album')), 'Pressestimmen fehlen auf der Ausgabenseite.');

foreach (['/de/stimmen' => 200, '/en/voices' => 200, '/en/stimmen' => 301, '/de/stimmen/' . stimmen()[stimme_index('1998-03-06-nordlys-live-med-leven')]['id'] => 200, '/de/stimmen/gibt-es-nicht' => 404] as $path => $status) {
    $code = '$_SERVER["REQUEST_URI"] = ' . var_export($path, true) . ';'
        . 'register_shutdown_function(function () { fwrite(STDERR, "STATUS:" . http_response_code()); });'
        . 'require ' . var_export(__DIR__ . '/../index.php', true) . ';';
    $prozess = proc_open([PHP_BINARY, '-d', 'display_errors=1', '-r', $code], [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
    stream_get_contents($pipes[1]);
    $fehler = stream_get_contents($pipes[2]);
    proc_close($prozess);
    pruefe_stimmen(str_contains($fehler, 'STATUS:' . $status), 'Falscher Status für ' . $path . ': ' . $fehler);
}
echo count($quellen) . " Stimmen, {$seiten} Detailseiten (DE/EN), Lizenzen, Filter, Pressestimmen und Routen geprüft.\n";
