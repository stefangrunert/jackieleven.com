<?php
declare(strict_types=1);

const APP_ROOT = __DIR__;

require APP_ROOT . '/columns.php';
require APP_ROOT . '/discography.php';

/** Das Buch (die Pastiche) liegt außerhalb von app/, als eigenes Arbeitsverzeichnis. */
const BUCH_ROOT = __DIR__ . '/../autobiografie';

/**
 * Sprachen der Website. Eine neue Sprache braucht:
 *   app/lang/<code>.php         Pflicht: Oberfläche, Pfade, Monatsnamen
 *   app/data/texte/<code>.php   Stationstexte (fehlende fallen auf die Standardsprache zurück)
 *   app/views/<code>/           Fließtextseiten (dito)
 * und erst dann ihren Code hier. Eine vorhandene Datei allein schaltet nichts frei.
 */
const SPRACHEN = ['de', 'en'];
const STANDARD_SPRACHE = 'de';

/** Umbenannte Stations-Slugs: alt => neu. Alte Links bekommen eine 301. */
const SLUG_ALIAS = ['1983-der-ueberfall' => '1983-caledonian-road'];

/* ---------------------------------------------------------------------- */
/*  Ausgabe                                                               */
/* ---------------------------------------------------------------------- */

function e(?string $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function render(string $view, array $vars = []): string
{
    extract($vars, EXTR_SKIP);
    ob_start();
    require APP_ROOT . '/views/' . $view . '.php';
    return (string) ob_get_clean();
}

/**
 * Sprachabhängige View aus views/<sprache>/. Fehlt sie, wird die der
 * Standardsprache genommen und als solche ausgezeichnet.
 */
function render_lokal(string $view, array $vars = []): string
{
    foreach ([sprache(), STANDARD_SPRACHE] as $s) {
        if (is_file(APP_ROOT . "/views/$s/$view.php")) {
            $html = render("$s/$view", $vars);
            return $s === sprache() ? $html : '<div lang="' . e($s) . '">' . $html . '</div>';
        }
    }
    throw new RuntimeException("View fehlt: $view");
}

/** $noindex: Seite nicht in Suchmaschinen — für die Pastiche, deren Sätze ohne Kontext wie Zitate aussähen. */
function seite(string $inhalt, string $titel, string $nav = '', int $status = 200, bool $noindex = false): void
{
    http_response_code($status);
    header('Content-Language: ' . sprache());
    if ($noindex) {
        header('X-Robots-Tag: noindex');
    }
    echo render('layout', ['inhalt' => $inhalt, 'titel' => $titel, 'nav' => $nav, 'noindex' => $noindex]);
}

function weiter(string $ziel, int $status = 301): never
{
    header('Location: ' . $ziel, true, $status);
    exit;
}

/* ---------------------------------------------------------------------- */
/*  Sprache                                                               */
/* ---------------------------------------------------------------------- */

/** Die Sprache der aktuellen Anfrage; mit Argument wird sie gesetzt. */
function sprache(?string $neu = null): string
{
    static $s = STANDARD_SPRACHE;
    if ($neu !== null) {
        $s = $neu;
    }
    return $s;
}

/** Erste unterstützte Sprache aus Accept-Language, sonst die Standardsprache. */
function bevorzugte_sprache(): string
{
    $wuensche = [];
    foreach (explode(',', $_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '') as $teil) {
        $stuecke = explode(';', trim($teil));
        $code = strtolower(substr(trim($stuecke[0]), 0, 2));
        $q = preg_match('/q=([0-9.]+)/', $stuecke[1] ?? '', $m) ? (float) $m[1] : 1.0;
        if ($code !== '') {
            $wuensche[] = [$code, $q];
        }
    }
    usort($wuensche, fn($a, $b) => $b[1] <=> $a[1]);
    foreach ($wuensche as [$code]) {
        if (in_array($code, SPRACHEN, true)) {
            return $code;
        }
    }
    return STANDARD_SPRACHE;
}

function sprachdaten(string $s): array
{
    static $cache = [];
    if (!isset($cache[$s])) {
        $datei = APP_ROOT . "/lang/$s.php";
        $cache[$s] = is_file($datei) ? require $datei : [];
    }
    return $cache[$s];
}

/**
 * Übersetzter Oberflächentext. {name} wird aus $ersetze gefüllt.
 * Fehlt der Schlüssel, gilt die Standardsprache, dann der Schlüssel selbst.
 */
function t(string $schluessel, array $ersetze = [], ?string $s = null): string
{
    $s ??= sprache();
    $wert = sprachdaten($s)[$schluessel] ?? sprachdaten(STANDARD_SPRACHE)[$schluessel] ?? $schluessel;
    foreach ($ersetze as $k => $v) {
        $wert = str_replace('{' . $k . '}', (string) $v, $wert);
    }
    return $wert;
}

/* ---------------------------------------------------------------------- */
/*  Stationen                                                             */
/* ---------------------------------------------------------------------- */

function stationen(): array
{
    static $s = null;
    return $s ??= require APP_ROOT . '/data/stationen.php';
}

function stations_index(string $slug): int
{
    foreach (stationen() as $i => $st) {
        if ($st['slug'] === $slug) {
            return $i;
        }
    }
    return -1;
}

function stationstexte(string $s): array
{
    static $cache = [];
    if (!isset($cache[$s])) {
        $datei = APP_ROOT . "/data/texte/$s.php";
        $cache[$s] = is_file($datei) ? require $datei : [];
    }
    return $cache[$s];
}

/** Ein übersetzbares Feld einer Station als [Wert, Sprache des Werts]. */
function sfeld(array $st, string $feld): array
{
    $eigen = stationstexte(sprache())[$st['slug']][$feld] ?? null;
    if ($eigen !== null) {
        return [$eigen, sprache()];
    }
    return [stationstexte(STANDARD_SPRACHE)[$st['slug']][$feld] ?? '', STANDARD_SPRACHE];
}

/** Dasselbe als HTML; ein Rückfall auf die Standardsprache trägt deren lang. */
function sfeld_html(array $st, string $feld): string
{
    [$wert, $s] = sfeld($st, $feld);
    return $s === sprache() ? e($wert) : '<span lang="' . e($s) . '">' . e($wert) . '</span>';
}

/** „The Deep Pool, Mai 2003" — Rubrik und Monat in der Sprache der Seite. */
function quelle_text(array $q): string
{
    [$jahr, $monat] = array_map('intval', explode('-', $q['datum']));
    $monate = sprachdaten(sprache())['monate'] ?? sprachdaten(STANDARD_SPRACHE)['monate'];
    return t('rubrik.' . $q['rubrik']) . ', ' . $monate[$monat - 1] . ' ' . $jahr;
}

/* ---------------------------------------------------------------------- */
/*  Adressen                                                              */
/* ---------------------------------------------------------------------- */

/** Pfad der aktuellen Anfrage ohne Query und ohne abschließenden Schrägstrich. */
function pfad(): string
{
    $p = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
    return '/' . trim($p, '/');
}

/** Adresse einer Route in einer Sprache. Die Pfadstücke stehen in lang/<sprache>.php. */
function url(string $route, array $p = [], ?string $s = null): string
{
    $s ??= sprache();
    return match ($route) {
        'start'   => "/$s/",
        'zeitreise' => "/$s/" . t('pfad.station', [], $s),
        'station' => "/$s/" . t('pfad.station', [], $s) . '/' . rawurlencode($p['slug']),
        'kapitel' => "/$s/" . t('pfad.biografie', [], $s) . '/' . rawurlencode($p['slug']),
        'kolumne' => "/$s/" . t('pfad.pool', [], $s) . '/' . rawurlencode($p['slug']),
        'platte' => "/$s/" . t('pfad.diskografie', [], $s) . '/' . rawurlencode($p['slug']),
        'pool_archiv' => "/$s/" . t('pfad.pool', [], $s) . '/' . t('pfad.pool_archiv', [], $s),
        default   => "/$s/" . t('pfad.' . $route, [], $s),
    };
}

/** Die aktuelle Route (für Sprachwechsel und hreflang); mit Argumenten wird sie gesetzt. */
function route(?string $name = null, array $p = []): array
{
    static $r = ['name' => null, 'p' => []];
    if ($name !== null) {
        $r = ['name' => $name, 'p' => $p];
    }
    return $r;
}

/** Dieselbe Seite in einer anderen Sprache; ohne Route die Startseite. */
function alternativ_url(string $s): string
{
    $r = route();
    return $r['name'] !== null ? url($r['name'], $r['p'], $s) : url('start', [], $s);
}

function absolut(string $pfad): string
{
    $https = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    return ($https ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? 'localhost') . $pfad;
}

/* ---------------------------------------------------------------------- */
/*  Pastiche                                                              */
/* ---------------------------------------------------------------------- */

function kapitelliste(): array
{
    static $k = null;
    return $k ??= require APP_ROOT . '/data/pastiche.php';
}

function kapitel_index(string $slug): int
{
    foreach (kapitelliste() as $i => $k) {
        if ($k['slug'] === $slug) {
            return $i;
        }
    }
    return -1;
}

/**
 * Zerlegt eine Kapiteldatei in Anmerkung, Text und Nachweis (Markdown).
 * Der Standardhinweis „Dieser Text stammt nicht von Jackie Leven" wird entfernt,
 * weil die Website ihn selbst setzt; weitere Absätze im Kopf bleiben als Anmerkung.
 */
function kapitel_teile(string $datei): array
{
    $teile = ['anmerkung' => '', 'text' => '', 'apparat' => ''];
    if (!is_file($datei)) {
        return $teile;
    }
    $roh = str_replace("\r\n", "\n", file_get_contents($datei));
    $roh = preg_replace('/\A---\n.*?\n---\n/s', '', $roh);

    [$vorn, $apparat] = array_pad(preg_split('/^(?=## )/m', $roh, 2), 2, '');
    $teile['apparat'] = trim($apparat);

    if (preg_match('/\A\s*((?:>.*(?:\n|$))+)/', $vorn, $m)) {
        $kopf = preg_split('/\n\s*\n/', trim(preg_replace('/^> ?/m', '', $m[1])));
        $kopf = array_filter($kopf, fn($a) => !preg_match('/^\*\*(Hinweis|Note):\*\*/', trim($a)));
        $teile['anmerkung'] = trim(implode("\n\n", $kopf));
        $vorn = substr($vorn, strlen($m[0]));
    }
    $vorn = preg_replace('/^#\s+.*$/m', '', $vorn, 1);          // Kapitelüberschrift
    $teile['text'] = trim(preg_replace('/\n-{3,}\s*\z/', '', rtrim($vorn)));
    return $teile;
}

/**
 * Ein Kapitel in der aktuellen Sprache: jeder Teil als [Markdown, Sprache].
 * Text im englischen Original, Anmerkung und Nachweis auf Deutsch — außer eine
 * Übersetzung in autobiografie/<sprache>/ liefert den Teil.
 */
function kapitel(array $k): array
{
    $quelle = kapitel_teile(BUCH_ROOT . '/' . $k['slug'] . '.md');
    $uebers = kapitel_teile(BUCH_ROOT . '/' . sprache() . '/' . $k['slug'] . '.md');
    $ursprung = ['anmerkung' => 'de', 'text' => 'en', 'apparat' => 'de'];
    $aus = [];
    foreach ($ursprung as $teil => $s) {
        $aus[$teil] = $uebers[$teil] !== '' ? [$uebers[$teil], sprache()] : [$quelle[$teil], $s];
    }
    return $aus;
}

/* ---------------------------------------------------------------------- */
/*  Markdown — nur was das Buch braucht: Absätze, ##, >, **, *, Links     */
/* ---------------------------------------------------------------------- */

function md(string $text): string
{
    $html = [];
    foreach (preg_split('/\n\s*\n/', trim($text)) as $block) {
        $block = trim($block);
        if ($block === '' || preg_match('/\A-{3,}\z/', $block)) {
            continue;
        }
        if (preg_match('/\A(#{2,6})\s+(.*)\z/s', $block, $m)) {
            $n = strlen($m[1]);
            $html[] = "<h$n>" . md_inline($m[2]) . "</h$n>";
        } elseif (str_starts_with($block, '>')) {
            $html[] = '<blockquote>' . md(preg_replace('/^> ?/m', '', $block)) . '</blockquote>';
        } else {
            $html[] = '<p>' . md_inline(preg_replace('/\s*\n\s*/', ' ', $block)) . '</p>';
        }
    }
    return implode("\n", $html);
}

function md_inline(string $s): string
{
    $s = e($s);
    $s = preg_replace('/\*\*(.+?)\*\*/s', '<strong>$1</strong>', $s);
    $s = preg_replace('/(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])/s', '<em>$1</em>', $s);
    // Links nach außen bleiben Links; Verweise auf Arbeitsdateien (.md) verlieren den Link, behalten den Text
    return preg_replace_callback('/\[([^\]]+)\]\(([^)\s]+)\)/', function ($m) {
        return preg_match('#^https?://#', html_entity_decode($m[2]))
            ? '<a href="' . $m[2] . '" rel="noopener noreferrer">' . $m[1] . '</a>'
            : $m[1];
    }, $s);
}
