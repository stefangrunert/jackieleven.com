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
    foreach ($q['beleg'] ?? [] as $beleg) pruefe_stimmen($beleg['original'] !== '' && $beleg['de'] !== '' && $beleg['en'] !== '', 'Beleg ohne Übersetzung: ' . $q['id']);
    pruefe_stimmen(($q['korrektur'] ?? null) === null || (($q['korrektur']['de'] ?? '') !== '' && ($q['korrektur']['en'] ?? '') !== ''), 'Korrektur unvollständig: ' . $q['id']);
    if (stimme_mit_seite($q)) {
        pruefe_stimmen(($q['kurz']['en'] ?? '') !== '' && count($q['inhalt']['en'] ?? []) === count($q['inhalt']['de']), 'Englische Fassung fehlt oder ist veraltet (werkzeug/quellen.php): ' . $q['id']);
        foreach ($q['zitate'] as $zitat) pruefe_stimmen($zitat['kontext'] === '' || ($zitat['kontext_en'] ?? '') !== '', 'Zitathinweis ohne Übersetzung: ' . $q['id']);
    }
    $klammer = preg_match('/^\[([^\]]*)\]/u', $q['titel'], $m) ? $m[1] : '';
    pruefe_stimmen(isset($q['en']['titel']) || !preg_match('/\b(und|mit|vor|nach|über|ohne|Konzert\w*|Vorbericht|Bericht|Kurzkritik|Rezension|Kommentare|Gästebuch|Sammeldatei|Ausgabe)\b/u', $klammer), 'Beschreibender Titel ohne Übersetzung: ' . $q['id']);
}
pruefe_stimmen(count(array_filter($quellen, fn($q) => $q['stufe'] === 'auswahl')) >= 20, 'Zu wenige ausgewählte Quellen.');
pruefe_stimmen(stimmen_filter(['art' => 'interviews', 'sprache' => ['x'], 'zugang' => 'gibtsnicht', 'fremd' => 1]) === ['auswahl' => '1', 'art' => 'interviews'], 'Filter übernimmt unbekannte Werte.');
$norwegisch = array_filter($quellen, fn($q) => stimme_passt($q, ['sprache' => 'no']));
pruefe_stimmen($norwegisch !== [] && array_filter($norwegisch, fn($q) => !in_array($q['sprache'], ['no', 'nn'], true)) === [], 'Sprachfilter Norwegisch falsch.');
foreach ([['2'], '-1', '3', '1.5'] as $wert) {
    pruefe_stimmen(stimmen_filter(['auswahl' => $wert]) === ['auswahl' => '1'], 'Ungültige Auswahl übernommen.');
}
pruefe_stimmen(stimmen_filter([]) === ['auswahl' => '1'], 'Mittlere Auswahl ist nicht Standard.');
pruefe_stimmen(stimmen_filter(['auswahl' => '0']) === ['auswahl' => '0'], 'Alle Quellen nicht explizit wählbar.');
foreach (['1', '2'] as $wert) {
    $filter = stimmen_filter(['auswahl' => $wert, 'sprache' => 'no']);
    $gefiltert = array_merge(...array_values(stimmen_jahre($filter)));
    $erwartet = array_values(array_filter($norwegisch, fn($q) => $wert === '2' ? $q['stufe'] === 'auswahl' : $q['stufe'] !== 'weitere'));
    pruefe_stimmen($gefiltert === $erwartet && $gefiltert !== [], 'Auswahl und Sprachfilter greifen nicht zusammen.');
}

libxml_use_internal_errors(true);
$seiten = 0;
foreach (SPRACHEN as $s) {
    sprache($s);
    $dom = new DOMDocument();
    route('stimmen');
    $html = render('layout', ['inhalt' => render('stimmen', ['filter' => []]), 'titel' => t('titel.stimmen'), 'nav' => 'stimmen', 'noindex' => false]);
    $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
    $xp = new DOMXPath($dom);
    pruefe_stimmen($xp->query('//header[@class="disk-kopf"]/p[@class="disk-intro"]')->length === 1, 'Übersicht ohne Einleitung.');
    pruefe_stimmen($xp->query('//article[contains(@class,"stimme ")]')->length === count(array_filter($quellen, 'stimme_mit_seite')), 'Quellen fehlen in der Übersicht (' . $s . ').');
    pruefe_stimmen($xp->query('//details[@class="stimmen-weitere"]//li')->length === count(array_filter($quellen, fn($q) => !stimme_mit_seite($q))), 'Weitere Quellen fehlen (' . $s . ').');
    pruefe_stimmen($xp->query('//iframe')->length === 0, 'Unerwarteter Player auf der Übersicht.');
    pruefe_stimmen($xp->query('//aside')->length === 0, 'Redaktionelle Einordnung in der Quellenübersicht.');
    foreach (['1971-11-06-sounds-take-off-your-head-and-listen', '1972-10-28-nme-john-st-field-folkclubs'] as $id) {
        pruefe_stimmen($xp->query('//article[@id="' . $id . '" and not(@hidden)]')->length === 1, 'Frühe Quelle fehlt in der Standardansicht: ' . $id);
    }
    foreach ($xp->query('//div[@class="quellen-faksimiles"]//img') as $bild) {
        pruefe_stimmen(str_starts_with($bild->getAttribute('src'), 'https://www.nb.no/services/image/resolver/') && $bild->getAttribute('loading') === 'lazy', 'Unbekanntes oder vorab geladenes Faksimile.');
    }
    pruefe_stimmen($xp->query('//nav//a[@aria-current="page" and @href="' . url('stimmen') . '"]')->length === 1, 'Navigation markiert die Seite nicht.');
    pruefe_stimmen(!preg_match('/>stimmen\.[a-z_.-]+</', $html), 'Unübersetzter Text auf der Übersicht.');
    if ($s !== 'de') pruefe_stimmen($xp->query('//p[@lang="de"] | //div[@lang="de"] | //figcaption[@lang="de"] | //li[@lang="de"]')->length === 0, 'Deutscher Text auf der englischen Übersicht.');
    pruefe_stimmen(alternativ_url($s === 'de' ? 'en' : 'de') === url('stimmen', [], $s === 'de' ? 'en' : 'de'), 'Sprachwechsel verliert die Übersicht.');

    $dom->loadHTML('<?xml encoding="UTF-8">' . render('stimmen', ['filter' => ['auswahl' => '2']]));
    $xp = new DOMXPath($dom);
    pruefe_stimmen($xp->query('//article[not(@hidden)]')->length === count(array_filter($quellen, fn($q) => $q['stufe'] === 'auswahl')), 'Auswahl ohne JavaScript falsch.');
    pruefe_stimmen($xp->query('//details[not(@hidden)]')->length === 0, 'Weitere Quellen trotz engster Auswahl sichtbar.');
    pruefe_stimmen($xp->query('//input[@type="range" and @value="2" and @aria-valuetext]')->length === 1, 'Reglerzustand fehlt.');

    foreach ($quellen as $i => $q) {
        if (!stimme_mit_seite($q)) continue;
        route('quelle', ['slug' => $q['id']]);
        $html = render('quelle', ['i' => $i]);
        $dom = new DOMDocument();
        $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
        $xp = new DOMXPath($dom);
        pruefe_stimmen($xp->query('//h1[@lang]')->length === 1, 'Detailseite ohne Titel: ' . $q['id']);
        pruefe_stimmen($xp->query('//section[@class="stimme-quelle"]//a[@target="_blank"]')->length >= ($q['zugang'] === 'verloren' ? 0 : 1), 'Detailseite ohne Quellenlink: ' . $q['id']);
        $bilder = $xp->query('//div[@class="quellen-faksimiles"]//img');
        $auszuege = $xp->query('//div[@class="quellen-auszuege"]//img');
        pruefe_stimmen($auszuege->length === count($q['auszuege']), 'Faksimile-Ausschnitt fehlt: ' . $q['id']);
        pruefe_stimmen($xp->query('//*[@src]')->length === $bilder->length + $auszuege->length, 'Unerwartete externe Ressource: ' . $q['id']);
        foreach ($auszuege as $bild) {
            $src = $bild->getAttribute('src');
            pruefe_stimmen(preg_match('~^/assets/images/voices/[a-z0-9-]+\.webp$~', $src) === 1, 'Unbekannter lokaler Bildpfad: ' . $q['id']);
            $datei = PUBLIC_ROOT . $src;
            $masse = is_file($datei) ? getimagesize($datei) : false;
            pruefe_stimmen($masse && $masse[0] === (int) $bild->getAttribute('width') && $masse[1] === (int) $bild->getAttribute('height'), 'Bild fehlt oder Maße falsch: ' . $src);
            pruefe_stimmen(filesize($datei) < 300000 && max($masse[0], $masse[1]) <= 1800, 'Faksimile nicht für das Web skaliert: ' . $src);
            pruefe_stimmen($bild->getAttribute('loading') === 'lazy' && $bild->getAttribute('alt') !== '', 'Faksimile ohne verzögertes Laden oder Bildbeschreibung: ' . $src);
        }
        if ($bilder->length) pruefe_stimmen(in_array($q['scan']['license'], ['ccbync', 'ccbyncnd'], true) && !empty($q['scan']['manifest']), 'Faksimile ohne belegte Lizenz: ' . $q['id']);
        if ($q['lizenz']) {
            $lizenz = $xp->query('//p[@class="stimme-lizenz" or @class="quellen-scan-credit"]//a[contains(@rel,"license")]');
            pruefe_stimmen($lizenz->length === 1 && str_starts_with($lizenz[0]->getAttribute('href'), 'https://creativecommons.org/licenses/by-nc'), 'Namensnennung oder Lizenz fehlt: ' . $q['id']);
            pruefe_stimmen(str_contains($html, e(stimme_feld($q, 'medium'))), 'Medium fehlt in der Namensnennung: ' . $q['id']);
        }
        if ($s !== 'de') pruefe_stimmen($xp->query('//p[@lang="de"] | //div[@lang="de"] | //figcaption[@lang="de"] | //li[@lang="de"]')->length === 0 && !str_contains($html, 'Zusammenfassung'), 'Deutscher Text auf der englischen Seite: ' . $q['id']);
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
