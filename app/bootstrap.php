<?php
declare(strict_types=1);

const APP_ROOT  = __DIR__;
const SITE_NAME = 'Jackie Leven';

/** HTML-sicher ausgeben. */
function e(?string $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Alle Stationen, einmal geladen. */
function stationen(): array
{
    static $s = null;
    return $s ??= require APP_ROOT . '/data/stationen.php';
}

/** Index einer Station anhand ihres Slugs; -1 wenn unbekannt. */
function stations_index(string $slug): int
{
    foreach (stationen() as $i => $st) {
        if ($st['slug'] === $slug) {
            return $i;
        }
    }
    return -1;
}

/** Eine View rendern und als String zurückgeben. */
function render(string $view, array $vars = []): string
{
    extract($vars, EXTR_SKIP);
    ob_start();
    require APP_ROOT . '/views/' . $view . '.php';
    return (string) ob_get_clean();
}

/** Seite mit Layout ausgeben. */
function seite(string $view, array $vars = [], int $status = 200): void
{
    http_response_code($status);
    $inhalt = render($view, $vars);
    echo render('layout', $vars + [
        'inhalt' => $inhalt,
        'titel'  => $vars['titel'] ?? SITE_NAME,
        'nav'    => $vars['nav'] ?? '',
    ]);
}

/** Navigation: Pfad der aktuellen Anfrage, ohne Query. */
function pfad(): string
{
    $p = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
    return '/' . trim($p, '/');
}
