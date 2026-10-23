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

/** Liedidentität, unabhängig von Datenträger, Satzzeichen oder Live-/Edit-Zusatz. */
function diskografie_liedschluessel(string $titel): string
{
    $titel = preg_replace('/\s*[\[(](?:live|edit|radio|remaster)[^\])]*[\])]/iu', '', $titel);
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
    ][$key] ?? $key;
}

/** Ein kuratiertes Hörbeispiel pro Lied, auf jeder Ausgabe wiederverwendet. */
function diskografie_youtube(string $titel): ?array
{
    static $daten = null;
    $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/youtube-titel.json'), true, flags: JSON_THROW_ON_ERROR);
    return $daten[diskografie_liedschluessel($titel)] ?? null;
}
