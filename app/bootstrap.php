<?php
declare(strict_types=1);

const APP_ROOT = __DIR__;

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

function seite(string $inhalt, string $titel, string $nav = '', int $status = 200): void
{
    http_response_code($status);
    header('Content-Language: ' . sprache());
    echo render('layout', ['inhalt' => $inhalt, 'titel' => $titel, 'nav' => $nav]);
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
        'station' => "/$s/" . t('pfad.station', [], $s) . '/' . rawurlencode($p['slug']),
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
