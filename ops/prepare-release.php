<?php
/** Build an allowlisted release. Only public/ is a document root. No network access. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

if ($argc !== 2 || file_exists($argv[1]) || is_link($argv[1])) {
    fwrite(STDERR, "Usage: php ops/prepare-release.php NEW_DIRECTORY\n");
    exit(2);
}
$quelle = dirname(__DIR__);
$ziel = $argv[1];
if (!is_dir(dirname($ziel))) throw new RuntimeException('Destination parent is missing');
if (!mkdir($ziel, 0755)) throw new RuntimeException('Cannot create release directory');
$manifest = [];

function kopiere(string $relativ, ?string $nach = null): void
{
    global $quelle, $ziel, $manifest;
    if (str_starts_with($relativ, '/') || preg_match('~(^|/)\.{1,2}(/|$)~', $relativ)) {
        throw new RuntimeException('Invalid release path: ' . $relativ);
    }
    $pfad = $quelle;
    foreach (explode('/', $relativ) as $teil) {
        $pfad .= '/' . $teil;
        if (is_link($pfad)) throw new RuntimeException('Symlink in release source: ' . $relativ);
    }
    if (!is_file($pfad)) throw new RuntimeException('Missing release file: ' . $relativ);
    $nach ??= str_starts_with($relativ, 'assets/') ? 'public/' . $relativ : $relativ;
    $ausgabe = $ziel . '/' . $nach;
    if (!is_dir(dirname($ausgabe))) mkdir(dirname($ausgabe), 0755, true);
    if (!copy($pfad, $ausgabe) || !chmod($ausgabe, 0644)) throw new RuntimeException('Cannot copy: ' . $relativ);
    $manifest[$nach] = hash_file('sha256', $ausgabe);
}

$dateien = json_decode(file_get_contents(__DIR__ . '/release-files.json'), true, flags: JSON_THROW_ON_ERROR);
foreach ($dateien as $datei) kopiere($datei);

// Only the published corpus and the chapters used by the app, never the research tree.
$bestand = require APP_ROOT . '/data/kolumnen.php';
foreach ($bestand['dateien'] as $datei) {
    if (basename($datei) !== $datei || !str_ends_with($datei, '.md')) throw new RuntimeException('Invalid column filename');
    kopiere('research/columns/' . $datei);
}
foreach (kapitelliste() as $kapitel) {
    if (!preg_match('/^[a-z0-9-]+$/', $kapitel['slug'])) throw new RuntimeException('Invalid chapter slug');
    $name = $kapitel['slug'] . '.md';
    kopiere('autobiografie/' . $name);
    foreach (SPRACHEN as $s) {
        if (is_file(BUCH_ROOT . '/' . $s . '/' . $name)) kopiere('autobiografie/' . $s . '/' . $name);
    }
}

// Only images selected by the public app, excluding drafts, unused photos and references.
$bilder = ['assets/bilder/jackie-leven-logo-originalnah.png',
    'assets/bilder/startseite/portrait-graphic.png', 'assets/bilder/startseite/cover-mystery-of-love.png'];
foreach (stationen() as $station) $bilder[] = 'assets/bilder/' . $station['bild'];
$start = require APP_ROOT . '/data/startseite.php';
foreach ($start['hoeren'] as $video) $bilder[] = ltrim($video['preview'], '/');
foreach (diskografie()['releases'] as $platte) {
    if (isset($platte['cover']) && str_starts_with($platte['cover'], '/assets/')) $bilder[] = ltrim($platte['cover'], '/');
}
foreach (diskografie_livevideos_daten() as $konzert) {
    foreach ($konzert['videos'] as $video) {
        if ($video['embeddable']) $bilder[] = 'assets/bilder/live/' . $video['id'] . '.webp';
    }
}
foreach (array_unique($bilder) as $bild) {
    if (!preg_match('~^assets/bilder/[a-zA-Z0-9/_-]+\.(png|jpe?g|webp)$~', $bild)) throw new RuntimeException('Invalid image path');
    kopiere($bild);
}
kopiere('.htaccess', 'public/.htaccess');
$einstieg = "<?php\ndeclare(strict_types=1);\ndefine('PUBLIC_ROOT', __DIR__);\nrequire dirname(__DIR__) . '/index.php';\n";
if (file_put_contents($ziel . '/public/index.php', $einstieg) === false) throw new RuntimeException('Cannot write public entry point');
chmod($ziel . '/public/index.php', 0644);
$manifest['public/index.php'] = hash('sha256', $einstieg);
ksort($manifest);
$pruefsummen = '';
foreach ($manifest as $pfad => $hash) $pruefsummen .= $hash . '  ' . $pfad . "\n";
if (file_put_contents($ziel . '/release-manifest.sha256', $pruefsummen) === false) throw new RuntimeException('Cannot write manifest');
echo count($manifest) . " Dateien vorbereitet: $ziel\nDocumentRoot: $ziel/public\n";
