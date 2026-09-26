<?php
declare(strict_types=1);

require __DIR__ . '/app/bootstrap.php';

$pfad = pfad();

// /station/<slug> — eine einzelne Station, direkt verlinkbar
if (preg_match('#^/station/([a-z0-9\-]+)$#', $pfad, $m)) {
    $i = stations_index($m[1]);
    if ($i < 0) {
        seite('404', ['titel' => 'Nicht gefunden'], 404);
        exit;
    }
    // Teilantwort für das Nachladen ohne Seitenwechsel
    if (($_GET['fragment'] ?? '') === '1') {
        header('Content-Type: text/html; charset=utf-8');
        echo render('buehne', ['st' => stationen()[$i], 'i' => $i]);
        exit;
    }
    seite('zeitreise', [
        'aktiv'  => $i,
        'nav'    => 'zeitreise',
        'titel'  => stationen()[$i]['jahr'] . ' — ' . stationen()[$i]['titel'] . ' · ' . SITE_NAME,
    ]);
    exit;
}

switch ($pfad) {
    case '/':
    case '/zeitreise':
        seite('zeitreise', ['aktiv' => 0, 'nav' => 'zeitreise', 'titel' => SITE_NAME . ' — Zeitreise']);
        break;

    case '/biografie':
        seite('biografie', ['nav' => 'biografie', 'titel' => 'Biografie · ' . SITE_NAME]);
        break;

    case '/ueber':
        seite('ueber', ['nav' => 'ueber', 'titel' => 'Über diese Seite · ' . SITE_NAME]);
        break;

    default:
        seite('404', ['titel' => 'Nicht gefunden'], 404);
}
