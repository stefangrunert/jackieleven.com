<?php
/**
 * Prüft, dass jedes Zitat der Website wortgetreu in seiner Quelle steht.
 *
 *     php werkzeug/zitate.php                 # app/data/stationen.php
 *     php werkzeug/zitate.php andere.php      # eine andere Stationsdatei
 *
 * Verglichen wird Zeichen für Zeichen — nur Zeilenumbrüche und mehrfache
 * Leerzeichen werden vorher zusammengefasst, weil die Quellen aus HTML stammen.
 * Anführungszeichen, Gedankenstriche, Groß- und Kleinschreibung und Levens
 * Tippfehler müssen stimmen. Exit-Code 1 bei jeder Abweichung.
 */

$wurzel = dirname(__DIR__);
$stationen = require ($argv[1] ?? $wurzel . '/app/data/stationen.php');
$norm = fn(string $s): string => trim(preg_replace('/\s+/u', ' ', $s));

$fehler = 0;
$geprueft = 0;
foreach ($stationen as $st) {
    if ($st['zitat'] === '') {
        if ($st['quelle'] !== null) {
            echo "✗ {$st['slug']}: Quelle ohne Zitat\n";
            $fehler++;
        }
        continue;
    }
    $datei = $wurzel . '/research/columns/' . ($st['quelle']['datei'] ?? '');
    if (!is_file($datei)) {
        echo "✗ {$st['slug']}: Quelldatei fehlt ({$st['quelle']['datei']})\n";
        $fehler++;
        continue;
    }
    $geprueft++;
    if (!str_contains($norm(file_get_contents($datei)), $norm($st['zitat']))) {
        echo "✗ {$st['slug']}: Zitat steht nicht wortgetreu in {$st['quelle']['datei']}\n";
        $fehler++;
    }
}

echo $fehler === 0
    ? "✓ alle {$geprueft} Zitate stehen wortgetreu in ihren Quellen\n"
    : "\n{$fehler} Abweichung(en)\n";
exit($fehler === 0 ? 0 : 1);
