<?php
declare(strict_types=1);

/** Kuratierter Katalog; Quellen und Ausgaben sind pro Eintrag dokumentiert. */
function diskografie(): array
{
    static $daten = null;
    return $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/diskografie.json'), true, flags: JSON_THROW_ON_ERROR);
}

function diskografie_jahre(): array
{
    $jahre = [];
    foreach (diskografie()['releases'] as $platte) {
        $jahre[$platte['year']][] = $platte;
    }
    return $jahre;
}

function diskografie_projekte(): array
{
    return [
        'john-st-field' => 'John St. Field',
        'doll-by-doll' => 'Doll by Doll',
        'jackie-leven' => 'Jackie Leven',
        'sir-vincent-lone' => 'Sir Vincent Lone',
        'jackie-balfour' => 'Jackie Balfour',
        'concrete-bulletproof-invisible' => 'Concrete Bulletproof Invisible',
        'haunted-valley' => 'Haunted Valley',
        'collaborations' => t('disk.kooperationen'),
    ];
}

function diskografie_index(string $id): int
{
    foreach (diskografie()['releases'] as $i => $platte) {
        if ($platte['id'] === $id) return $i;
    }
    return -1;
}

function diskografie_details(string $id): array
{
    static $daten = null;
    $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/diskografie-details.json'), true, flags: JSON_THROW_ON_ERROR);
    return $daten[$id] ?? [];
}

/** Nur bekannte Filter und eine bestehende Ursprungsplatte in Links übernehmen. */
function diskografie_kontext(array $query): array
{
    $kontext = [];
    $werte = [
        'projekt' => array_keys(diskografie_projekte()),
        'format' => ['alben', 'kleine', 'reissue', 'video', 'unreleased'],
    ];
    foreach ($werte as $key => $erlaubt) {
        if (isset($query[$key]) && in_array($query[$key], $erlaubt, true)) $kontext[$key] = $query[$key];
    }
    if (isset($query['von']) && is_string($query['von']) && diskografie_index($query['von']) >= 0) $kontext['von'] = $query['von'];
    return $kontext;
}

function diskografie_passt(array $platte, array $kontext): bool
{
    if (isset($kontext['projekt']) && !in_array($kontext['projekt'], $platte['tags'], true)) return false;
    $format = $kontext['format'] ?? null;
    return match ($format) {
        null => true,
        'alben' => in_array($platte['kind'], ['album', 'live', 'compilation', 'spoken', 'tribute'], true),
        'kleine' => in_array($platte['kind'], ['single', 'ep'], true),
        default => $platte['kind'] === $format,
    };
}

function diskografie_link(string $id, array $kontext = []): string
{
    return url('platte', ['slug' => $id]) . ($kontext ? '?' . http_build_query($kontext) : '');
}

function diskografie_zurueck(string $id, array $kontext): string
{
    $anker = $kontext['von'] ?? $id;
    unset($kontext['von']);
    return url('diskografie') . ($kontext ? '?' . http_build_query($kontext) : '') . '#' . $anker;
}

/** Geprüfte externe Albumangebote; getrennt von historischen Ausgabedaten. */
function diskografie_hoerlinks(string $id): array
{
    static $daten = null;
    $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/diskografie-hoerlinks.json'), true, flags: JSON_THROW_ON_ERROR);
    return $daten[$id] ?? [];
}

function diskografie_musikdienste(): array
{
    return [
        'spotify' => ['name' => 'Spotify', 'hosts' => ['open.spotify.com'], 'tooltip' => 'Listen on Spotify'],
        'apple' => ['name' => 'Apple Music', 'hosts' => ['music.apple.com'], 'tooltip' => 'Listen on Apple Music'],
        'qobuz' => ['name' => 'Qobuz', 'hosts' => ['www.qobuz.com'], 'tooltip' => 'Listen or download on Qobuz'],
        'amazon' => ['name' => 'Amazon Music', 'hosts' => ['music.amazon.ca'], 'tooltip' => 'Listen on Amazon Music'],
        'bandcamp' => ['name' => 'Bandcamp', 'hosts' => ['jackieleven.bandcamp.com'], 'tooltip' => 'Listen or buy on Bandcamp'],
    ];
}

/** Liedidentität, unabhängig von Datenträger, Satzzeichen oder Live-/Edit-/Fassungszusatz. */
function diskografie_liedschluessel(string $titel): string
{
    $titel = preg_replace('/^\s*\(spoken\)\s*/iu', '', $titel);
    $titel = preg_replace('/\s*[\[(](?:live|edit|radio|remaster|bonus track|full version|beautiful version|from live show|etc\.)[^\])]*[\])]/iu', '', $titel);
    $titel = preg_replace('/\s*[-–—]\s*(?:live|radio edit|edit|remaster).*$/iu', '', $titel);
    $ascii = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $titel);
    $key = preg_replace('/[^a-z0-9]/', '', strtolower($ascii !== false ? $ascii : $titel));
    return [
        'shadowinmyeye' => 'shadowinmyeyes',
        'thebarsofdundee' => 'barsofdundee',
        'levenlament' => 'levenslament',
        'standinginanothermansrain' => 'anothermansrain',
        'theworkingmanslovesong' => 'workingmanslovesong',
        'isawmylovewalkintotheclouds' => 'isawmylovewalkintoclouds',
        'oliverblues' => 'olivierblues',
        'humanface' => 'thehumanface',
        'palaceoflove' => 'thepalaceoflove',
        'boxershitharderwhenwomanarearound' => 'boxershitharderwhenwomenarearound',
        'balladofanneredmond' => 'theballadofanneredmond',
        'kingsofinfinitespaceplusstoryofbasilandronnie' => 'kingsofinfinitespace',
        'loversatthegunclubplusstoryofshannondoyle' => 'loversatthegunclub',
        'stingsdeadstoryofthesaddeathofthewellknownsinger' => 'stingsdead',
        'sextouriststory' => 'sextourist',
        'whenamandieswithjoshaw' => 'whenamandies',
        'poortounlosingmyvoice' => 'poortoun',
        'jackiesbaddepressionafunnystory' => 'jackiesbaddepression',
        'jackietalksaboutkielandhismother' => 'kielandhismother',
        'jackietalksaboutnorwegianprisoners' => 'norwegianprisoners',
    ][$key] ?? $key;
}

/**
 * Kuratierte Aufnahmen pro Lied, auf jeder Ausgabe wiederverwendet: zuerst das
 * Hörbeispiel (Studio bevorzugt), danach Livefassungen mit Ort bzw. Konzert.
 */
function diskografie_youtube_fassungen(string $titel): array
{
    static $daten = null;
    $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/youtube-titel.json'), true, flags: JSON_THROW_ON_ERROR);
    $videos = $daten[diskografie_liedschluessel($titel)] ?? [];
    if ($videos === []) return [];
    return array_is_list($videos) ? $videos : [$videos];
}

/** Ein Hörbeispiel pro Lied, auf jeder Ausgabe wiederverwendet. */
function diskografie_youtube(string $titel): ?array
{
    return diskografie_youtube_fassungen($titel)[0] ?? null;
}

/** Ort bzw. Konzert einer Livefassung; Ortsnamen mit Exonym stehen zweisprachig. */
function diskografie_fassung_ort(array $fassung): string
{
    $ort = $fassung['label'] ?? '';
    return is_array($ort) ? ($ort[sprache()] ?? $ort['en']) : $ort;
}

/** Konzertvideos zum Einbetten; Freigabe und Vorschau pflegt werkzeug/livevideos.php. */
function diskografie_livevideos_daten(): array
{
    static $daten = null;
    return $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/live-videos.json'), true, flags: JSON_THROW_ON_ERROR);
}

/** Fan-Mitschnitte bettet die Seite nur ein, wenn sie ausdrücklich freigeschaltet sind. */
function diskografie_fanvideos_erlaubt(): bool
{
    static $erlaubt = null;
    if ($erlaubt === null) {
        $lokal = is_file(APP_ROOT . '/config.local.php') ? require APP_ROOT . '/config.local.php' : [];
        $env = getenv('JACKIE_FAN_VIDEOS');
        $erlaubt = $env !== false ? $env === '1' : (bool) ($lokal['fan_videos'] ?? false);
    }
    return $erlaubt;
}

/**
 * Konzerte mit einbettbaren Videos zu einer Ausgabe, chronologisch. Auf der Ausgabe
 * des Konzerts erscheinen alle Stücke, sonst nur die gemeinsamen Lieder.
 */
function diskografie_livevideos(string $id, ?bool $fan = null): array
{
    $fan ??= diskografie_fanvideos_erlaubt();
    $lieder = [];
    foreach (diskografie_details($id)['tracklists'] ?? [] as $liste) foreach ($liste['tracks'] as $track) $lieder[diskografie_liedschluessel($track['title'])] = true;
    $konzerte = [];
    foreach (diskografie_livevideos_daten() as $name => $konzert) {
        if ($konzert['source'] !== 'official' && !$fan) continue;
        $eigen = in_array($id, $konzert['releases'] ?? [], true);
        $stuecke = [];
        foreach ($konzert['videos'] as $video) {
            if (($video['embeddable'] ?? false) !== true || empty($video['checked'])) continue;
            foreach ($video['songs'] as $song) {
                if ($eigen || isset($lieder[diskografie_liedschluessel($song['title'])])) $stuecke[] = $song + ['video' => $video];
            }
        }
        if ($stuecke) $konzerte[] = ['name' => $name, 'stuecke' => $stuecke] + $konzert;
    }
    usort($konzerte, fn($a, $b) => strcmp($a['date'], $b['date']));
    return $konzerte;
}

/** Konzertdatum in der Genauigkeit der Quelle: Tag, Monat oder nur Jahr. */
function diskografie_konzertdatum(string $datum): string
{
    $teile = array_map('intval', explode('-', $datum));
    $monat = isset($teile[1]) ? (sprachdaten(sprache())['monate'] ?? sprachdaten(STANDARD_SPRACHE)['monate'])[$teile[1] - 1] : '';
    return match (count($teile)) {
        3 => $teile[2] . (sprache() === 'de' ? '. ' : ' ') . $monat . ' ' . $teile[0],
        2 => $monat . ' ' . $teile[0],
        default => (string) $teile[0],
    };
}

function diskografie_zeitmarke(int $sekunden): string
{
    $stunden = intdiv($sekunden, 3600);
    $rest = sprintf('%02d:%02d', intdiv($sekunden % 3600, 60), $sekunden % 60);
    return $stunden ? $stunden . ':' . $rest : ltrim(substr($rest, 0, 1), '0') . substr($rest, 1);
}

/** Tooltip mit tatsächlichem Video, Herkunftsalbum und Kanal. */
function diskografie_fassung_tooltip(array $fassung): string
{
    $teile = ['Listen on YouTube', $fassung['title']];
    if (!empty($fassung['album'])) $teile[] = $fassung['album'];
    if ($fassung['kind'] === 'live') $teile[] = 'Live' . (isset($fassung['label']) ? ', ' . (is_array($fassung['label']) ? $fassung['label']['en'] : $fassung['label']) : '');
    $teile[] = $fassung['channel'];
    return implode(' · ', $teile);
}

/** YouTube-ID aus den von uns kuratierten Watch-Adressen lesen. */
function youtube_video_id(string $url): string
{
    $host = strtolower((string) parse_url($url, PHP_URL_HOST));
    if (!in_array($host, ['youtube.com', 'www.youtube.com', 'youtu.be'], true)) return '';
    if ($host === 'youtu.be') return trim((string) parse_url($url, PHP_URL_PATH), '/');
    parse_str((string) parse_url($url, PHP_URL_QUERY), $query);
    return is_string($query['v'] ?? null) ? $query['v'] : '';
}
