<?php
/**
 * php werkzeug/quellen.php [--lizenzen]
 *
 * Erzeugt app/data/quellen.json aus der Recherche in research/quellen/ (index.json und
 * die Markdown-Dateien). Öffentlich werden nur Kopfdaten, die eigene Inhaltsangabe und die
 * Zitate; Fundweg, Sicherheit, Widersprüche und interne Verweise bleiben in research/.
 *
 * Stufen: ausgewählt (Liste unten), Verzeichnis, weitere, intern – nach der Regel in
 * stufe(); ein Feld `stufe:` im YAML-Kopf einer Quelle geht immer vor.
 *
 * --lizenzen fragt für jede Quelle mit Permalink der Nationalbibliothek die Lizenz der
 * Zeitungsausgabe ab (api.nb.no) und speichert sie in app/data/quellen-lizenzen.json.
 */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';

const RECHERCHE = APP_ROOT . '/../research/quellen';

/** Die aufschlussreichsten Quellen über alle Jahrzehnte, Sprachen und Arten. */
const AUSGEWAEHLT = [
    'interviews/1978-11-18_record-mirror_chris-westwood-doll-by-doll.md',
    'interviews/1979-03_zigzag_night-of-the-psychotic-woodsmen.md',
    'interviews/1995-11-03_rolling-stone-de_auf-den-spuren-von-iron-john.md',
    'portraets/1996-04-26_the-independent_man-trouble.md',
    'konzertberichte/1997-06_q_bawdy-jackie-leven-shocks-scandinavia.md',
    'portraets/1998-03-06_nordlys_live-med-leven.md',
    'interviews/1998-10-26_bergensavisen_spirituell-bergensvenn.md',
    'portraets/2000-02-03_the-daily-telegraph_the-lost-star-of-british-pop.md',
    'interviews/2001-06-28_the-independent_always-look-on-the-dark-side-of-life.md',
    'interviews/2001-07-19_gaesteliste_das-leben-ist-ein-langer-dunkler-whisky.md',
    'interviews/2001-07-26_the-guardian_i-am-an-abject-failure.md',
    'interviews/2003-03-01_bergensavisen_leven-gar-i-fengsel.md',
    'interviews/2004-04_the-word_ian-rankin-and-jackie-leven-interview.md',
    'interviews/2008-07-23_whiskyfun_music-and-whisky-interview-jackie-leven.md',
    'portraets/2010-02-24_telegraph-blogs_the-rock-star-and-the-prime-minister.md',
    'portraets/2010-04-22_chicago-reader_a-cult-artists-cult-artist.md',
    'radio-tv/2010-12-01_bbc-radio-scotland_stark-talk-jackie-leven.md',
    'interviews/2011-08-28_pennyblackmusic_jackie-leven-interview.md',
    'nachrufe/2011-11-15_the-guardian_jackie-leven-obituary.md',
    'nachrufe/2011-11-16_herald-scotland_jackie-leven-obituary.md',
    'nachrufe/2011-11-16_louder-than-war_jackie-leven-obituary-by-kevin-hewick.md',
    'nachrufe/2012-03_the-word_the-jackie-leven-obituary.md',
    'portraets/2015-06-16_the-guardian_cult-heroes-jackie-leven.md',
    'erinnerungen/2019-04-10_norman-lamont_drinking-with-jackie-leven.md',
    'erinnerungen/2021-07-20_the-guardian_ian-rankin-jackie-leven-should-be-revered.md',
    'portraets/2023-01-17_the-sunday-post_he-just-soaked-up-life-he-ate-up-life-th.md',
    'radio-tv/undatiert_stv_artery-jackie-leven-dokumentation.md',
];

/** Satzgrenze, aber nicht nach Abkürzungen wie „St.“, „Nr.“, „ca.“ oder Initialen. */
const SATZENDE = '/(?<=[.!?…])(?<!\\bSt\.)(?<!\\bNr\.)(?<!\\bDr\.)(?<!\\bMr\.)(?<!\\bca\.)(?<!\\bvs\.)(?<!\\bvgl\.)(?<!\\b[A-Za-z]\.)(?<!\\d\.)\\s+(?=[A-ZÄÖÜ0-9„"*(])/u';

const AUSFUEHRLICHE_ARTEN = ['interviews', 'portraets', 'nachrufe', 'erinnerungen', 'konzertberichte', 'rezensionen', 'radio-tv', 'foren'];

function stufe(array $q, ?string $vorgabe): string
{
    if ($vorgabe !== null) return $vorgabe;
    if (in_array($q['datei'], AUSGEWAEHLT, true)) return 'auswahl';
    if ($q['sicherheit'] === 'indirekt') return 'intern';
    $sammlung = str_contains(mb_strtolower($q['art']), 'sammeldatei');
    if (!$sammlung && in_array($q['kategorie'], AUSFUEHRLICHE_ARTEN, true)
        && ($q['sicherheit'] === 'belegt' || $q['umfang'] === 'ausfuehrlich')) return 'verzeichnis';
    return 'weitere';
}

/** Abschnitte einer Quelldatei: Kopf (nur `stufe`) und Text nach Überschrift. */
function quelldatei(string $pfad): array
{
    $text = file_get_contents(RECHERCHE . '/' . $pfad);
    preg_match('/\A---\n(.*?)\n---\n(.*)\z/s', $text, $m);
    $stufe = preg_match('/^stufe:\s*"?(auswahl|verzeichnis|weitere|intern)"?\s*$/m', $m[1], $s) ? $s[1] : null;
    $teile = [];
    foreach (preg_split('/^## /m', $m[2]) as $block) {
        if (trim($block) === '') continue;
        [$titel, $rest] = array_pad(explode("\n", $block, 2), 2, '');
        $teile[trim($titel)] = trim($rest);
    }
    return [$stufe, $teile];
}

/** Absätze ohne Sätze, die auf interne Arbeitsdateien verweisen (research/, *.md). */
function absaetze(string $text): array
{
    $absaetze = [];
    foreach (preg_split('/\n\s*\n/', $text) as $absatz) {
        // Klammern mit Dateiverweisen entfallen; bleibt ein Verweis im Satz, entfällt der Satz.
        $absatz = preg_replace('~\\s*\\([^()]*(?:research/|\\.md\\b)[^()]*\\)~', '', $absatz);
        $saetze = preg_split(SATZENDE, trim($absatz));
        $absatz = implode(' ', array_filter($saetze, fn($s) => !preg_match('~research/|\.md\b|README~', $s)));
        if (trim($absatz) !== '') $absaetze[] = trim($absatz);
    }
    return $absaetze;
}

/** Zitate stehen als `> "…" – Kontext.` im Abschnitt Zitate. */
function zitate(string $text): array
{
    $zitate = [];
    foreach (preg_split('/\n(?=>)/', $text) as $block) {
        if (!str_starts_with(ltrim($block), '>')) continue;
        $zeile = trim(preg_replace('/^>\s?/m', '', $block));
        if (preg_match('/^[„"“«»](.+?)[“"”«»]\s*(?:[–—-]\s*(.+))?$/su', $zeile, $m)) {
            $zitate[] = ['text' => trim($m[1]), 'kontext' => trim($m[2] ?? '')];
        } elseif ($zeile !== '') {
            $zitate[] = ['text' => $zeile, 'kontext' => ''];
        }
    }
    return $zitate;
}

/** Ein bis zwei Sätze für Listen, an Satzgrenzen gekürzt. */
function kurztext(string $absatz): string
{
    $saetze = preg_split(SATZENDE, $absatz);
    $kurz = $saetze[0];
    if (mb_strlen($kurz) < 90 && isset($saetze[1])) $kurz .= ' ' . $saetze[1];
    return mb_strlen($kurz) > 320 ? mb_substr($kurz, 0, 300) . '…' : $kurz;
}

function liedfrei(string $s): string
{
    return preg_replace('/[^a-z0-9]/', '', strtolower(iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $s) ?: $s));
}

/** Diskographie-Ausgaben, deren Titel im Feld `thema` vorkommt: das Original vor Neuauflagen. */
function ausgaben(array $thema, string $datum): array
{
    $treffer = [];
    $jahr = (int) substr($datum, 0, 4) ?: 9999;
    $projekte = array_map('liedfrei', diskografie_projekte());
    foreach ($thema as $t) {
        // „Doll by Doll“ ist Band und Albumtitel: als Album nur bei Kritiken aus der Erscheinungszeit.
        if (in_array(liedfrei($t), $projekte, true) && !($jahr >= 1980 && $jahr <= 1982)) continue;
        $kandidaten = array_filter(diskografie()['releases'], fn($p) => liedfrei($p['title']) === liedfrei($t) && $p['year'] <= $jahr + 1);
        if (!$kandidaten) continue;
        usort($kandidaten, fn($a, $b) => [in_array($a['kind'], ['single', 'ep', 'reissue'], true), -$a['year']] <=> [in_array($b['kind'], ['single', 'ep', 'reissue'], true), -$b['year']]);
        $treffer[] = $kandidaten[0]['id'];
    }
    return array_values(array_unique($treffer));
}

function nb_urn(string $url): ?string
{
    return preg_match('~(URN:NBN:no-nb_[A-Za-z0-9_]+)~', $url, $m) ? $m[1] : null;
}

$index = json_decode(file_get_contents(RECHERCHE . '/index.json'), true, flags: JSON_THROW_ON_ERROR);
$lizenzdatei = APP_ROOT . '/data/quellen-lizenzen.json';
$lizenzen = is_file($lizenzdatei) ? json_decode(file_get_contents($lizenzdatei), true, flags: JSON_THROW_ON_ERROR) : [];

if (in_array('--lizenzen', $argv, true)) {
    $kontext = stream_context_create(['http' => ['timeout' => 20, 'ignore_errors' => true]]);
    foreach ($index as $q) {
        if (!($urn = nb_urn($q['url']))) continue;
        $antwort = json_decode((string) @file_get_contents('https://api.nb.no/catalog/v1/items?' . http_build_query(['q' => $urn, 'searchType' => 'FULL_TEXT_SEARCH']), false, $kontext), true);
        $info = $antwort['_embedded']['items'][0]['accessInfo'] ?? null;
        if ($info === null) { echo "ohne Antwort: $urn\n"; continue; }
        $lizenzen[$urn] = ['license' => $info['license'] ?? '', 'access' => $info['accessAllowedFrom'] ?? '', 'checked' => date('Y-m-d')];
        usleep(150000);
    }
    ksort($lizenzen);
    file_put_contents($lizenzdatei, json_encode($lizenzen, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n");
    echo count($lizenzen) . " Lizenzen der Nationalbibliothek gespeichert.\n";
}

// Englische Fassung: gilt nur, solange der deutsche Text unverändert ist (Prüfsumme `quelle`).
$englisch = is_file(APP_ROOT . '/data/quellen-en.json') ? json_decode(file_get_contents(APP_ROOT . '/data/quellen-en.json'), true, flags: JSON_THROW_ON_ERROR) : [];
$veraltet = 0;

$quellen = [];
foreach ($index as $q) {
    [$vorgabe, $teile] = quelldatei($q['datei']);
    $stufe = stufe($q, $vorgabe);
    if ($stufe === 'intern') continue;
    $inhalt = absaetze($teile['Inhalt'] ?? '');
    $urn = nb_urn($q['url']);
    $lizenz = $urn && in_array($lizenzen[$urn]['license'] ?? '', ['ccbyncnd', 'ccbync'], true) && ($lizenzen[$urn]['access'] ?? '') === 'EVERYWHERE'
        ? ['name' => $lizenzen[$urn]['license'], 'checked' => $lizenzen[$urn]['checked']] : null;
    $zugang = match (true) {
        $lizenz !== null => 'frei',
        $q['erreichbarkeit'] === 'live' => 'online',
        $q['erreichbarkeit'] === 'archiv' => 'archiv',
        $q['erreichbarkeit'] === 'paywall' => 'abo',
        default => 'verloren',
    };
    $id = str_replace('_', '-', basename($q['datei'], '.md'));
    $kurz = $inhalt ? kurztext($inhalt[0]) : '';
    $zitate = zitate($teile['Zitate'] ?? '');
    $en = $englisch[$id] ?? null;
    if ($en !== null && $en['quelle'] !== sha1(implode("\n", $inhalt) . $kurz)) { $en = null; $veraltet++; }
    if ($en !== null) foreach ($zitate as $n => &$zitat) $zitat['kontext_en'] = $en['zitate_kontext'][$n] ?? '';
    unset($zitat);
    $quellen[] = [
        'id' => $id,
        'titel' => $q['titel'],
        'autor' => $q['autor'],
        'medium' => $q['medium'],
        'datum' => $q['datum'],
        'kategorie' => $q['kategorie'],
        'art' => $q['art'],
        'sprache' => $q['sprache'],
        'stufe' => $stufe,
        'zugang' => $zugang,
        'url' => $q['url'],
        'archiv' => $q['archiv'],
        'lizenz' => $lizenz,
        'kurz' => ['de' => $kurz] + (isset($en['kurz']) ? ['en' => $en['kurz']] : []),
        'inhalt' => ['de' => $inhalt] + (isset($en['inhalt']) ? ['en' => $en['inhalt']] : []),
        'zitate' => $zitate,
        // Übersetzte Angaben in eckigen Klammern (eigene Beschreibungen) und deutsche Medien-/Autorangaben.
        'en' => array_filter(['titel' => $en['titel'] ?? null, 'medium' => $en['medium'] ?? null, 'autor' => $en['autor'] ?? null]),
        // Nur Rezensionen: In anderen Arten nennt `thema` auch Whisky, Lieder oder Ereignisse gleichen Namens.
        'ausgaben' => $q['kategorie'] === 'rezensionen' ? ausgaben($q['thema'], $q['datum']) : [],
    ];
}
// Undatierte Quellen stehen am Ende; sonst chronologisch, gleiches Datum nach Stufe.
$rang = ['auswahl' => 0, 'verzeichnis' => 1, 'weitere' => 2];
usort($quellen, fn($a, $b) => [$a['datum'] === '', $a['datum'], $rang[$a['stufe']], $a['id']] <=> [$b['datum'] === '', $b['datum'], $rang[$b['stufe']], $b['id']]);

file_put_contents(APP_ROOT . '/data/quellen.json', json_encode($quellen, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n");
$zahl = array_count_values(array_column($quellen, 'stufe'));
echo ($veraltet ? "$veraltet englische Fassungen veraltet (deutscher Text geändert).\n" : '') . count($quellen) . ' öffentliche Quellen (' . ($zahl['auswahl'] ?? 0) . ' ausgewählt, ' . ($zahl['verzeichnis'] ?? 0) . ' Verzeichnis, ' . ($zahl['weitere'] ?? 0) . ' weitere), '
    . (count($index) - count($quellen)) . " intern.\n";
