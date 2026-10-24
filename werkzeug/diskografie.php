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
        $dienst = diskografie_musikdienste()[$link['service']] ?? null;
        $host = parse_url($link['url'], PHP_URL_HOST);
        pruefe_disk($dienst !== null && in_array($host, $dienst['hosts'], true) && parse_url($link['url'], PHP_URL_SCHEME) === 'https'
            && str_contains(parse_url($link['url'], PHP_URL_PATH), $link['service'] === 'amazon' ? '/albums/' : '/album/'), 'Kein direkter Albumlink.');
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
        foreach ($xp->query('//a[@data-music-link]') as $link) {
            pruefe_disk($link->getAttribute('target') === '_blank' && $link->getAttribute('rel') === 'noopener noreferrer', 'Musiklink verlässt die Hommage oder erlaubt Zugriff auf das Ursprungsfenster.');
        }
        $liveLinks = $xp->query('//small[@class="disk-track-live"]/a');
        pruefe_disk($xp->query('//a[@data-music-link]')->length === $hoerlinks->length + $xp->query('//a[@class="disk-track-youtube"]')->length + $liveLinks->length, 'Musiklink ohne separates Zielfenster.');
        $ytSoll = $liveSoll = 0;
        foreach ($details[$platte['id']]['tracklists'] ?? [] as $liste) foreach ($liste['tracks'] as $track) {
            $videos = diskografie_youtube_fassungen($track['title']);
            if ($videos) $ytSoll++;
            $liveSoll += max(0, count($videos) - 1);
        }
        pruefe_disk($xp->query('//a[@class="disk-track-youtube"]')->length === $ytSoll, 'YouTube-Beispiele fehlen auf einer Ausgabe.');
        pruefe_disk($liveLinks->length === $liveSoll, 'Livefassungen fehlen auf einer Ausgabe.');
        foreach ([...$xp->query('//a[@class="disk-track-youtube"]'), ...$liveLinks] as $link) {
            pruefe_disk(str_starts_with($link->getAttribute('href'), 'https://www.youtube.com/watch?v=') && $link->getAttribute('title') !== '' && $link->getAttribute('aria-label') !== '', 'YouTube-Link ohne Ziel oder Beschriftung.');
        }

        // Live-Videos: vor dem Klick keine Anfrage an YouTube, Vorschauen lokal und lazy.
        $konzerte = diskografie_livevideos($platte['id']);
        $bereich = $xp->query('//section[@id="live-videos"]');
        pruefe_disk($bereich->length === ($konzerte ? 1 : 0), 'Live-Videos fehlen oder stehen bei einer falschen Ausgabe: ' . $platte['id']);
        foreach ($xp->query('//*[@src]') as $element) {
            pruefe_disk(!preg_match('~youtube|ytimg|googleapis~i', $element->getAttribute('src')), 'Externe YouTube-Ressource vor dem Klick: ' . $platte['id']);
        }
        $skripte = $xp->query('//script[contains(@src, "/assets/js/livevideos.js")]');
        pruefe_disk($skripte->length === ($konzerte ? 1 : 0) && ($konzerte === [] || $skripte[0]->hasAttribute('defer')), 'Live-Video-Skript fehlt, steht doppelt oder blockiert.');
        $vorschauen = $xp->query('//section[@id="live-videos"]//img');
        pruefe_disk($vorschauen->length === count($konzerte), 'Konzert ohne Vorschau.');
        foreach ($vorschauen as $bild) {
            $datei = APP_ROOT . '/..' . $bild->getAttribute('src');
            pruefe_disk($bild->getAttribute('loading') === 'lazy' && $bild->getAttribute('decoding') === 'async' && $bild->getAttribute('width') !== '' && $bild->getAttribute('height') !== '', 'Vorschau wird nicht verzögert geladen.');
            pruefe_disk(str_starts_with($bild->getAttribute('src'), '/assets/bilder/live/') && is_file($datei) && filesize($datei) <= 24 * 1024, 'Vorschau fehlt oder ist zu groß: ' . $bild->getAttribute('src'));
        }
        $videolinks = $xp->query('//a[@data-livevideo]');
        pruefe_disk($videolinks->length === count($konzerte) + array_sum(array_map(fn($k) => count($k['stuecke']), $konzerte)), 'Konzertstücke fehlen.');
        foreach ($videolinks as $link) {
            pruefe_disk(str_starts_with($link->getAttribute('href'), 'https://www.youtube.com/watch?v=' . $link->getAttribute('data-livevideo')) && $link->getAttribute('target') === '_blank', 'Live-Video ohne Rückfalllink.');
        }

        pruefe_disk(!preg_match('/>disk\.[a-z_]+</', $html), 'Unübersetzter Detailtext.');
        route('platte', ['slug' => $platte['id']]);
        foreach (SPRACHEN as $ziel) pruefe_disk(alternativ_url($ziel) === url('platte', ['slug' => $platte['id']], $ziel), 'Sprachwechsel verliert die Ausgabe.');
    }
}

$kontext = diskografie_kontext(['projekt' => 'haunted-valley', 'format' => 'alben', 'von' => '1999-greek-notebook', 'fremd' => 'ignorieren']);
pruefe_disk(count($kontext) === 3, 'Unbekannte Query übernommen.');
pruefe_disk(diskografie_kontext(['projekt' => ['x'], 'format' => 'x', 'von' => ['x']]) === [], 'Ungültige Query nicht abgefangen.');
pruefe_disk(diskografie_index('fehlt') === -1, 'Unbekannte Ausgabe gefunden.');
pruefe_disk(diskografie_alias('1973-control') === '1975-control' && diskografie_index('1975-control') === 0 && diskografie()['releases'][0]['year'] === 1975, 'Control nicht auf Ende 1975 korrigiert oder alte Adresse ohne Weiterleitung.');
$html = render('platte', ['platte' => $platten[diskografie_index('1999-greek-notebook')], 'kontext' => $kontext]);
pruefe_disk(str_contains($html, e(diskografie_link('2000-munich-blues', $kontext))), 'Filterkontext geht beim Blättern verloren.');
pruefe_disk(!str_contains($html, 'href="' . url('platte', ['slug' => '2000-defending-ancient-springs'])), 'Gefilterte Navigation enthält andere Projekte.');
pruefe_disk(str_contains($html, e(diskografie_zurueck('1999-greek-notebook', $kontext))), 'Rückweg verliert Filter oder Ursprung.');
echo count($platten) . " Einträge: Details, Titellisten, Quellen, DE/EN, chronologische Navigation und Filterkontext geprüft.\n";

$youtube = json_decode(file_get_contents(APP_ROOT . '/data/youtube-titel.json'), true, flags: JSON_THROW_ON_ERROR);
$bekannteLieder = [];
foreach ($details as $detail) foreach ($detail['tracklists'] ?? [] as $liste) foreach ($liste['tracks'] as $track) $bekannteLieder[diskografie_liedschluessel($track['title'])] = true;
$fassungen = 0;
foreach ($youtube as $key => $videos) {
    pruefe_disk(isset($bekannteLieder[$key]), 'YouTube-Beispiel ohne bekannten Liedtitel: ' . $key);
    $videos = array_is_list($videos) ? $videos : [$videos];
    pruefe_disk($videos !== [], 'Aufnahmen eines Liedes fehlen: ' . $key);
    $adressen = [];
    foreach ($videos as $j => $video) {
        pruefe_disk(preg_match('~^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}(?:&t=\d+s)?$~', $video['url']) === 1, 'Ungültige Video-Adresse: ' . $key);
        pruefe_disk(in_array($video['kind'], ['audio', 'video', 'live'], true) && $video['title'] !== '' && $video['channel'] !== '', 'Aufnahme ohne Art, Titel oder Kanal: ' . $key);
        $ort = $video['label'] ?? null;
        pruefe_disk($ort === null || (is_string($ort) && $ort !== '') || (is_array($ort) && ($ort['de'] ?? '') !== '' && ($ort['en'] ?? '') !== ''), 'Ortsangabe unvollständig: ' . $key);
        pruefe_disk($j === 0 || ($video['kind'] === 'live' && $ort !== null), 'Weitere Fassung ohne Live-Kennzeichnung: ' . $key);
        $adressen[] = $video['url'];
    }
    pruefe_disk(count(array_unique($adressen)) === count($adressen), 'Doppelte Aufnahme bei ' . $key);
    $fassungen += count($videos) - 1;
}
pruefe_disk(diskografie_youtube('Call Mother A Lonely Field') === diskografie_youtube('Call Mother a Lonely Field (Live, Bremen, 2004)'), 'Live-Zusatz verhindert gemeinsame Liedzuordnung.');
pruefe_disk(diskografie_youtube('Shadow In My Eye') === diskografie_youtube('Shadow in My Eyes'), 'Abweichende Schreibweise nicht zugeordnet.');
pruefe_disk(diskografie_liedschluessel('(Spoken) The Butterfly Story') === diskografie_liedschluessel('The Butterfly Story'), 'Gesprochene Zwischenstücke nicht gemeinsam zugeordnet.');
pruefe_disk(diskografie_youtube('Unbekanntes Lied') === null && diskografie_youtube_fassungen('Unbekanntes Lied') === [], 'Fremder Titel erhält falschen Link.');
pruefe_disk(diskografie_youtube('Call Mother A Lonely Field') === diskografie_youtube_fassungen('Call Mother A Lonely Field')[0], 'Hörbeispiel ist nicht die erste Aufnahme.');
foreach (['1975-control', '1997-control', '2023-control', '1979-remember', '1979-gypsy-blood-album', '1981-doll-by-doll', '1982-grand-passion', '2006-revenge-of-memory-live-at-the-sheffield-limits-club', '2007-remember-reissue', '2007-gypsy-blood-reissue', '2007-doll-by-doll-reissue', '2007-grand-passion-reissue'] as $id) {
    pruefe_disk(in_array('spotify', array_column(diskografie_hoerlinks($id)['links'] ?? [], 'service'), true), 'Spotify-Angebot fehlt: ' . $id);
    foreach ($details[$id]['tracklists'] as $liste) foreach ($liste['tracks'] as $track) {
        pruefe_disk(diskografie_youtube($track['title']) !== null, 'Frühwerk ohne YouTube-Beispiel: ' . $id . ' / ' . $track['title']);
    }
}
echo count($youtube) . " Lieder mit YouTube-Beispiel und {$fassungen} Livefassungen: zentrale Zuordnung, alle Ausgaben und Beschriftungen geprüft.\n";

$konzertdaten = diskografie_livevideos_daten();
foreach ($konzertdaten as $name => $konzert) {
    pruefe_disk(preg_match('/^[a-z0-9-]+$/', $name) === 1 && $konzert['title'] !== '' && preg_match('/^\d{4}(-\d{2}(-\d{2})?)?$/', $konzert['date']) === 1, 'Konzert unvollständig: ' . $name);
    pruefe_disk(in_array($konzert['source'], ['official', 'fan'], true), 'Herkunft offen: ' . $name);
    foreach ($konzert['releases'] ?? [] as $id) pruefe_disk(in_array($id, $ids, true), 'Konzert verweist auf unbekannte Ausgabe: ' . $name);
    foreach ($konzert['videos'] as $video) {
        pruefe_disk(preg_match('/^[A-Za-z0-9_-]{11}$/', $video['id']) === 1 && $video['title'] !== '' && $video['channel'] !== '', 'Konzertvideo unvollständig: ' . $name);
        pruefe_disk(is_bool($video['embeddable'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $video['checked'] ?? '') === 1, 'Einbettfreigabe nicht geprüft (werkzeug/livevideos.php): ' . $video['id']);
        foreach ($video['songs'] as $song) {
            pruefe_disk(isset($bekannteLieder[diskografie_liedschluessel($song['title'])]) && is_int($song['start']) && $song['start'] >= 0, 'Konzertstück ohne Liedtitel der Diskographie: ' . $song['title']);
        }
    }
}
$alle = fn(bool $fan) => array_merge(...array_map(fn($p) => diskografie_livevideos($p['id'], $fan), $platten));
pruefe_disk(array_filter($alle(false), fn($k) => $k['source'] !== 'official') === [], 'Fan-Mitschnitt ohne Freischaltung eingebettet.');
foreach ($alle(true) as $konzert) foreach ($konzert['stuecke'] as $stueck) pruefe_disk($stueck['video']['embeddable'] === true, 'Nicht einbettbares Video in der Auswahl.');
pruefe_disk(count(diskografie_livevideos('2011-live-at-rockpalast', false)[0]['stuecke'] ?? []) === 13, 'Konzertausgabe zeigt nicht das ganze Konzert.');
pruefe_disk(array_column(diskografie_livevideos('2010-gothic-road', true), 'name') === ['manchester-2009', 'essen-2010'] && diskografie_livevideos('2010-gothic-road', false) === [], 'Konzertauswahl oder Fan-Schalter wirkt nicht.');
pruefe_disk(diskografie_zeitmarke(95) === '1:35' && diskografie_zeitmarke(3888) === '1:04:48', 'Zeitmarke falsch.');
foreach (['de' => '26. März 2004', 'en' => '26 March 2004'] as $s => $soll) { sprache($s); pruefe_disk(diskografie_konzertdatum('2004-03-26') === $soll, 'Konzertdatum falsch formatiert.'); }
echo count($konzertdaten) . " Konzerte mit Videos: Einbettfreigabe, lokale Vorschauen, Lazy Load und Fan-Schalter geprüft.\n";
