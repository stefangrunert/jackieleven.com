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
$details = json_decode(file_get_contents(APP_ROOT . '/data/diskografie-details.json'), true, flags: JSON_THROW_ON_ERROR);
foreach ($details as $id => $detail) {
    pruefe_disk(in_array($id, $ids, true), 'Details ohne Katalogeintrag: ' . $id);
    pruefe_disk(!empty($detail['sources']), 'Detailquelle fehlt: ' . $id);
    foreach ($detail['sources'] as $quelle) {
        pruefe_disk(filter_var($quelle['url'], FILTER_VALIDATE_URL) !== false && $quelle['label'] !== '', 'Ungültige Detailquelle: ' . $id);
    }
    foreach ($detail['tracklists'] ?? [] as $liste) {
        pruefe_disk($liste['tracks'] !== [], 'Leere Titelliste: ' . $id);
        foreach ($liste['tracks'] as $track) {
            pruefe_disk(is_string($track['number']) && $track['number'] !== '' && $track['title'] !== '', 'Unvollständiger Track: ' . $id);
        }
        foreach (SPRACHEN as $s) pruefe_disk(!isset($liste['label']) || isset($liste['label'][$s]), 'Datenträgerbezeichnung fehlt: ' . $id);
    }
    foreach (SPRACHEN as $s) {
        foreach ($detail['credits'] ?? [] as $credit) pruefe_disk(isset($credit['role'][$s]) && $credit['name'] !== '', 'Unvollständige Credits: ' . $id);
        foreach ($detail['facts'] ?? [] as $fakt) pruefe_disk(isset($fakt['label'][$s], $fakt['value'][$s]), 'Unvollständige Fakten: ' . $id);
    }
}
$angebote = json_decode(file_get_contents(APP_ROOT . '/data/diskografie-hoerlinks.json'), true, flags: JSON_THROW_ON_ERROR);
foreach ($angebote as $id => $angebot) {
    pruefe_disk(in_array($id, $ids, true), 'Hörangebot ohne Ausgabe.');
    pruefe_disk(preg_match('/^\d{4}-\d{2}-\d{2}$/', $angebot['checked']) === 1, 'Prüfdatum fehlt.');
    pruefe_disk($angebot['digitalTitle'] !== '' && $angebot['links'] !== [], 'Unvollständiges Hörangebot.');
    $dienste = [];
    foreach ($angebot['links'] as $link) {
        $host = ['spotify' => 'open.spotify.com', 'apple' => 'music.apple.com'][$link['service']] ?? null;
        pruefe_disk($host !== null && parse_url($link['url'], PHP_URL_SCHEME) === 'https'
            && parse_url($link['url'], PHP_URL_HOST) === $host && str_contains(parse_url($link['url'], PHP_URL_PATH), '/album/'), 'Kein direkter Albumlink.');
        $dienste[] = $link['service'];
    }
    pruefe_disk(count($dienste) === count(array_unique($dienste)), 'Doppelter Dienst.');
    $anzahl = array_sum(array_map(fn($liste) => count($liste['tracks']), $details[$id]['tracklists'] ?? []));
    if ($anzahl !== $angebot['trackCount']) foreach (SPRACHEN as $s) pruefe_disk(!empty($angebot['note'][$s]), 'Abweichende digitale Titelliste ohne Hinweis.');
}
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
        $links = $xpath->query('//article[@id="' . $id . '"]//a[@data-release-link]');
        pruefe_disk($links->length > 0, 'Detailverlinkung fehlt: ' . $id);
        foreach ($links as $link) pruefe_disk(in_array($link->getAttribute('href'), [url('platte', ['slug' => $id]), url('platte', ['slug' => $id]) . '#hoeren'], true), 'Titel, Cover oder Hörlink führen nicht zur Detailseite.');
    }
    pruefe_disk(!preg_match('/>disk\.[a-z_]+</', $html), 'Unübersetzter Oberflächentext.');
    route('diskografie');
    pruefe_disk(alternativ_url($s) === url('diskografie', [], $s), 'Sprachwechsel verliert die Route.');

    foreach ($platten as $i => $platte) {
        $html = render('platte', ['platte' => $platte, 'kontext' => []]);
        $dom->loadHTML('<?xml encoding="UTF-8">' . $html);
        libxml_clear_errors();
        $xp = new DOMXPath($dom);
        pruefe_disk($xp->query('//h1')->length === 1, 'Detailtitel fehlt.');
        $aktiv = $xp->query('//a[@aria-current="page"]');
        pruefe_disk($aktiv->length === 1 && $aktiv[0]->getAttribute('href') === diskografie_link($platte['id']), 'Falscher aktiver Zeitstrahleintrag: ' . $platte['id']);
        foreach (['prev' => $i - 1, 'next' => $i + 1] as $rel => $nachbar) {
            $links = $xp->query('//a[@rel="' . $rel . '"]');
            pruefe_disk($links->length === (isset($platten[$nachbar]) ? 2 : 0), 'Fehler am Rand der Navigation.');
            foreach ($links as $link) pruefe_disk($link->getAttribute('href') === diskografie_link($platten[$nachbar]['id']), 'Falsche chronologische Nachbarplatte.');
        }
        $n = array_sum(array_map(fn($liste) => count($liste['tracks']), $details[$platte['id']]['tracklists'] ?? []));
        pruefe_disk($xp->query('//ol[@class="disk-tracks"]/li')->length === $n, 'Tracks fehlen auf der Detailseite.');
        pruefe_disk(!str_contains($html, 'class="disk-notiz"'), 'Redaktionelle Beschreibung auf der Detailseite.');
        $hoerlinks = $xp->query('//section[@id="hoeren"]//a');
        pruefe_disk($hoerlinks->length === count($angebote[$platte['id']]['links'] ?? []), 'Hörlinks fehlen oder stehen bei einer falschen Ausgabe.');
        foreach ($hoerlinks as $j => $link) {
            pruefe_disk($link->getAttribute('href') === $angebote[$platte['id']]['links'][$j]['url'], 'Falsches Albumangebot.');
            pruefe_disk($link->getAttribute('title') !== '' && $link->getAttribute('aria-label') !== '', 'Dienstsymbol ohne Beschriftung.');
            pruefe_disk($xp->query('.//*[local-name()="svg"]', $link)->length === 1, 'Dienstsymbol fehlt.');
        }
        pruefe_disk(!str_contains($html, '<iframe'), 'Ungefragter eingebetteter Player.');

        pruefe_disk(!preg_match('/>disk\.[a-z_]+</', $html), 'Unübersetzter Detailtext.');
        route('platte', ['slug' => $platte['id']]);
        foreach (SPRACHEN as $ziel) pruefe_disk(alternativ_url($ziel) === url('platte', ['slug' => $platte['id']], $ziel), 'Sprachwechsel verliert die Ausgabe.');
    }
}

$kontext = diskografie_kontext(['projekt' => 'haunted-valley', 'format' => 'alben', 'von' => '1999-greek-notebook', 'fremd' => 'ignorieren']);
pruefe_disk(count($kontext) === 3, 'Unbekannte Query übernommen.');
pruefe_disk(diskografie_kontext(['projekt' => ['x'], 'format' => 'x', 'von' => ['x']]) === [], 'Ungültige Query nicht abgefangen.');
pruefe_disk(diskografie_index('fehlt') === -1, 'Unbekannte Ausgabe gefunden.');
$html = render('platte', ['platte' => $platten[diskografie_index('1999-greek-notebook')], 'kontext' => $kontext]);
pruefe_disk(str_contains($html, e(diskografie_link('2000-munich-blues', $kontext))), 'Filterkontext geht beim Blättern verloren.');
pruefe_disk(!str_contains($html, 'href="' . url('platte', ['slug' => '2000-defending-ancient-springs'])), 'Gefilterte Navigation enthält andere Projekte.');
pruefe_disk(str_contains($html, e(diskografie_zurueck('1999-greek-notebook', $kontext))), 'Rückweg verliert Filter oder Ursprung.');
echo count($platten) . " Einträge: Details, Titellisten, Quellen, DE/EN, chronologische Navigation und Filterkontext geprüft.\n";
