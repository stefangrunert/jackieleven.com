<?php
/** Router für den eingebauten PHP-Entwicklungsserver. */
declare(strict_types=1);

$pfad = rawurldecode((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH));
$datei = dirname(__DIR__) . $pfad;

if ($pfad !== '/' && is_file($datei)) {
    return false;
}

require dirname(__DIR__) . '/index.php';
