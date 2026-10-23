<?php
/**
 * php werkzeug/livevideos.php [--vorschau]
 *
 * Prüft für jedes Video in app/data/live-videos.json, ob es eingebettet werden darf,
 * und speichert Ergebnis und Prüfdatum. Mit JACKIE_YOUTUBE_API_KEY (oder youtube_api_key
 * in app/config.local.php) über die YouTube Data API: Einbettfreigabe, öffentlich,
 * nicht altersbeschränkt, nicht in Deutschland gesperrt. Ohne Schlüssel über oEmbed,
 * das gesperrte Einbettungen mit 401 beantwortet.
 *
 * Legt fehlende Vorschaubilder lokal als WebP an (480×270), damit die Seite vor dem
 * Klick nichts von YouTube lädt; --vorschau erneuert alle. Der einzige Ort, an dem
 * das Projekt YouTube abfragt – nie beim Seitenaufruf.
 */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

const VORSCHAU_ORDNER = APP_ROOT . '/../assets/bilder/live';

function abruf(string $url): array
{
    $kontext = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 20, 'header' => "User-Agent: jackieleven-werkzeug\r\n"]]);
    $inhalt = @file_get_contents($url, false, $kontext);
    $status = 0;
    foreach ($http_response_header ?? [] as $zeile) {
        if (preg_match('~^HTTP/\S+ (\d{3})~', $zeile, $m)) $status = (int) $m[1];
    }
    return [$status, $inhalt === false ? '' : $inhalt];
}

function freigabe_api(array $ids, string $schluessel): array
{
    $ergebnis = array_fill_keys($ids, ['embeddable' => false, 'grund' => 'nicht gefunden']);
    foreach (array_chunk($ids, 50) as $teil) {
        [$status, $json] = abruf('https://www.googleapis.com/youtube/v3/videos?' . http_build_query(['part' => 'status,contentDetails', 'id' => implode(',', $teil), 'key' => $schluessel]));
        if ($status !== 200) throw new RuntimeException('YouTube Data API antwortet mit ' . $status);
        foreach (json_decode($json, true, flags: JSON_THROW_ON_ERROR)['items'] as $video) {
            $gesperrt = $video['contentDetails']['regionRestriction']['blocked'] ?? [];
            $erlaubt = $video['contentDetails']['regionRestriction']['allowed'] ?? null;
            $grund = match (true) {
                !($video['status']['embeddable'] ?? false) => 'Einbetten gesperrt',
                ($video['status']['privacyStatus'] ?? '') !== 'public' => 'nicht öffentlich',
                ($video['contentDetails']['contentRating']['ytRating'] ?? '') === 'ytAgeRestricted' => 'altersbeschränkt',
                in_array('DE', $gesperrt, true) || ($erlaubt !== null && !in_array('DE', $erlaubt, true)) => 'in Deutschland gesperrt',
                default => '',
            };
            $ergebnis[$video['id']] = ['embeddable' => $grund === '', 'grund' => $grund];
        }
    }
    return $ergebnis;
}

function freigabe_oembed(string $id): array
{
    [$status] = abruf('https://www.youtube.com/oembed?' . http_build_query(['url' => 'https://www.youtube.com/watch?v=' . $id, 'format' => 'json']));
    return match ($status) {
        200 => ['embeddable' => true, 'grund' => ''],
        401, 403 => ['embeddable' => false, 'grund' => 'Einbetten gesperrt'],
        404 => ['embeddable' => false, 'grund' => 'entfernt oder privat'],
        default => throw new RuntimeException('oEmbed antwortet für ' . $id . ' mit ' . $status),
    };
}

/** Mittelausschnitt im Format 16:9, damit auch 4:3-Mitschnitte ohne Balken erscheinen. */
function vorschau(string $id): int
{
    [$status, $bild] = abruf('https://i.ytimg.com/vi/' . $id . '/hqdefault.jpg');
    if ($status !== 200) throw new RuntimeException('Kein Vorschaubild für ' . $id);
    $quelle = imagecreatefromstring($bild);
    $breite = imagesx($quelle);
    $hoehe = (int) round($breite * 9 / 16);
    $ziel = imagecreatetruecolor(480, 270);
    imagecopyresampled($ziel, $quelle, 0, 0, 0, intdiv(imagesy($quelle) - $hoehe, 2), 480, 270, $breite, $hoehe);
    if (!is_dir(VORSCHAU_ORDNER)) mkdir(VORSCHAU_ORDNER, 0755, true);
    $datei = VORSCHAU_ORDNER . '/' . $id . '.webp';
    imagewebp($ziel, $datei, 62);
    return filesize($datei);
}

$pfad = APP_ROOT . '/data/live-videos.json';
$daten = json_decode(file_get_contents($pfad), true, flags: JSON_THROW_ON_ERROR);
$lokal = is_file(APP_ROOT . '/config.local.php') ? require APP_ROOT . '/config.local.php' : [];
$schluessel = getenv('JACKIE_YOUTUBE_API_KEY') ?: ($lokal['youtube_api_key'] ?? '');
$ids = [];
foreach ($daten as $konzert) foreach ($konzert['videos'] as $video) $ids[] = $video['id'];
$freigaben = $schluessel !== '' ? freigabe_api(array_values(array_unique($ids)), $schluessel) : [];
$heute = date('Y-m-d');
$neu = in_array('--vorschau', $argv, true);

foreach ($daten as $name => &$konzert) {
    foreach ($konzert['videos'] as &$video) {
        $f = $freigaben[$video['id']] ?? freigabe_oembed($video['id']);
        $video['embeddable'] = $f['embeddable'];
        $video['checked'] = $heute;
        $groesse = '';
        if ($f['embeddable'] && ($neu || !is_file(VORSCHAU_ORDNER . '/' . $video['id'] . '.webp'))) $groesse = ' · Vorschau ' . round(vorschau($video['id']) / 1024, 1) . ' KB';
        echo str_pad($name, 18) . $video['id'] . ($f['embeddable'] ? ' einbettbar' : ' NICHT einbettbar (' . $f['grund'] . ')') . $groesse . "\n";
        if (!$schluessel) usleep(250000);
    }
}
unset($konzert, $video);
$json = json_encode($daten, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
file_put_contents($pfad, preg_replace_callback('/^ +/m', fn($m) => substr($m[0], 0, intdiv(strlen($m[0]), 2)), $json) . "\n");
echo ($schluessel !== '' ? 'Geprüft über die YouTube Data API.' : 'Geprüft über oEmbed (ohne API-Schlüssel: Länder- und Alterssperren nicht erfasst).') . "\n";
