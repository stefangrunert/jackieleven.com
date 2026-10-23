<?php
declare(strict_types=1);

/** Öffentliche Lesefassung; die Quelldateien in research/ bleiben unverändert. */
function kolumnen(): array
{
    static $liste = null;
    if ($liste !== null) {
        return $liste;
    }
    $bestand = require APP_ROOT . '/data/kolumnen.php';
    $liste = [];
    foreach ($bestand['dateien'] as $datei) {
        $roh = str_replace("\r\n", "\n", file_get_contents(APP_ROOT . '/../research/columns/' . $datei));
        if (!preg_match('/\A---\n(.*?)\n---\n(.*)\z/s', $roh, $m)) {
            throw new RuntimeException('Kolumnenkopf fehlt: ' . $datei);
        }
        $meta = [];
        preg_match_all('/^([a-z_]+):\s*"([^"\n]*)"\s*$/m', $m[1], $felder, PREG_SET_ORDER);
        foreach ($felder as $feld) {
            $meta[$feld[1]] = $feld[2];
        }
        $art = explode('_', $datei)[1];
        $datum = $meta['datum'];
        $datierung = $art === 'deep-pool' ? 'ausgabe' : 'archivdatum';
        // Die ersten Blog-/Rubrikenarchive nennen den Erscheinungsmonat in ihrer URL.
        if (preg_match('/-(june|aug)-08\.php$/', $meta['quelle'], $monat)) {
            $datum = '2008-' . ($monat[1] === 'june' ? '06' : '08');
            $datierung = 'ausgabe';
        }
        $text = trim(preg_replace('/\A\s*# [^\n]*\n/', '', $m[2], 1));
        $titel = $meta['titel'];
        // Echte Überschriften, die beim Import im Markdown-Kopf stehen, erhalten.
        if ($art !== 'deep-pool' && $art !== 'ankuendigung' && $titel !== '.' && !str_ends_with($titel, '…')) {
            $anfang = preg_replace('/\s+/', ' ', $text);
            if (!str_starts_with($anfang, $titel)) {
                $text = $titel . "\n\n" . $text;
            }
        }
        // Zwei mitkopierte Navigationsreste, keine Bestandteile der September-Kolumne.
        if ($datei === '2007-09_deep-pool_september-2007.md') {
            $text = preg_replace('/\AA\nugust 2006\n\nMarch 2003a\n\n/', '', $text, 1);
        }
        // Kopfgrafiken und wiederholte Seitenleisten-Cover gehören nicht zum Text.
        $text = trim(preg_replace('/^!\[[^\]]*\]\(bilder\/[^)]+\)\s*$/m', '', $text));
        preg_match('/^\d{4}-\d{2}(?:-([a-z0-9]+))?_/', $datei, $folge);
        $liste[] = [
            'slug' => str_replace('_', '-', basename($datei, '.md')),
            'datei' => $datei,
            'datum' => $datum,
            'datierung' => $datierung,
            'art' => $art,
            'autor' => $meta['autor'],
            'archiv' => $meta['archiv'],
            'quelle' => $meta['quelle'],
            'capture' => $meta['capture'],
            'website' => str_contains($meta['quelle'], 'home.xnet.it') ? 'jackieleven.com' : 'jackieleven.co.uk',
            'text' => $text,
            'folge' => $folge[1] ?? '',
        ];
    }
    usort($liste, function ($a, $b) {
        return [$a['datum'], $a['art'], $a['folge'], $a['capture'], $a['datei']]
            <=> [$b['datum'], $b['art'], $b['folge'], $b['capture'], $b['datei']];
    });
    $gruppen = [];
    foreach ($liste as $i => $k) {
        $gruppen[$k['datum'] . '/' . $k['art']][] = $i;
    }
    foreach ($gruppen as $indizes) {
        foreach ($indizes as $n => $i) {
            $liste[$i]['nummer'] = count($indizes) > 1 ? $n + 1 : null;
        }
    }
    return $liste;
}

function kolumnen_index(string $slug): int
{
    foreach (kolumnen() as $i => $k) {
        if ($k['slug'] === $slug) {
            return $i;
        }
    }
    return -1;
}

/** Die öffentlich eingebundene Lesefassung zu einer Quelldatei. */
function kolumne_nach_datei(string $datei): ?array
{
    foreach (kolumnen() as $k) {
        if ($k['datei'] === $datei) {
            return $k;
        }
    }
    return null;
}

function kolumnen_datum(array $k): string
{
    [$jahr, $monat] = explode('-', $k['datum']);
    $monate = sprachdaten(sprache())['monate'];
    return $monate[(int) $monat - 1] . ' ' . $jahr;
}

function kolumnen_rubrik(array $k): string
{
    return t('pool.art.' . $k['art']) . ($k['nummer'] !== null ? ' · ' . $k['nummer'] : '');
}

/** Rubrik und Datum stehen im Lesekopf; alte doppelte Kopfzeilen entfallen dort. */
function kolumnen_lesetext(array $k): string
{
    $text = $k['text'];
    if ($k['art'] !== 'deep-pool') {
        return $text;
    }
    do {
        $vorher = $text;
        $text = preg_replace('/\A(?:Monthly column - [A-Za-z]+ \d{4}|THE DEEP POOL(?: - [A-Z]+ \d{4}(?: - no\.\d+)?)?)\n\s*\n/', '', $text);
    } while ($text !== $vorher);
    return $text;
}

/**
 * Englischer Originalwortlaut: kein Markdown-Interpreter, der Sternchen,
 * Dialogstriche oder Zeichenfolgen in der Prosa versehentlich verändert.
 * Alte harte Zeilenumbrüche in Prosa fließen, kurze Verszeilen bleiben stehen.
 */
function kolumnen_html(string $text): string
{
    $text = preg_replace('/^(-{3,})[ \t]*$/m', "\n$1\n", $text);
    $html = [];
    foreach (preg_split('/\n\s*\n/', trim($text)) as $block) {
        $block = trim($block);
        if ($block === '') {
            continue;
        }
        if (preg_match('/\A-{3,}\z/', $block)) {
            $html[] = '<hr>';
            continue;
        }
        if ($block === 'jl') {
            $html[] = '<p class="pool-signatur">jl</p>';
            continue;
        }
        if (strlen($block) < 120 && preg_match('/[A-Z]/', $block) && !preg_match('/[a-z]/', $block)) {
            $html[] = '<h2>' . e(preg_replace('/\s+/', ' ', $block)) . '</h2>';
            continue;
        }
        $zeilen = explode("\n", $block);
        $max = max(array_map('strlen', $zeilen));
        $verse = count($zeilen) > 2 && $max < 68;
        $html[] = $verse
            ? '<p class="pool-vers">' . nl2br(e($block), false) . '</p>'
            : '<p>' . e(preg_replace('/\s*\n\s*/', ' ', $block)) . '</p>';
    }
    return implode("\n", $html);
}
