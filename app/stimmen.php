<?php
declare(strict_types=1);

/** Externe Quellen über Jackie Leven; erzeugt von werkzeug/quellen.php aus research/quellen/. */
function stimmen(): array
{
    static $daten = null;
    if ($daten !== null) return $daten;
    $daten = json_decode(file_get_contents(APP_ROOT . '/data/quellen.json'), true, flags: JSON_THROW_ON_ERROR);
    $scans = json_decode(file_get_contents(APP_ROOT . '/data/quellen-scans.json'), true, flags: JSON_THROW_ON_ERROR);
    foreach ($daten as &$q) {
        $q['scan'] = $scans[$q['id']] ?? ['pages' => '', 'facsimiles' => []];
        if (!empty($q['scan']['manifest'])) {
            $q['url'] = $q['scan']['url'];
            $q['lizenz'] = $q['scan']['license'] && !empty($q['scan']['public_access']) ? ['name' => $q['scan']['license'], 'checked' => $q['scan']['checked']] : null;
            if ($q['lizenz'] !== null) $q['zugang'] = 'frei';
            if ($q['lizenz'] === null && $q['zugang'] === 'frei') $q['zugang'] = 'online';
        }
    }
    unset($q);
    return $daten;
}

/** Ausgewählte und Verzeichnis-Quellen haben eine eigene Seite, weitere verweisen direkt aufs Original. */
function stimme_mit_seite(array $q): bool
{
    return $q['stufe'] !== 'weitere';
}

/** Vorhandene redaktionelle Stufen, keine automatisch berechnete Qualitätsnote. */
function stimme_gewicht(array $q): int
{
    return ['weitere' => 0, 'verzeichnis' => 1, 'auswahl' => 2][$q['stufe']];
}

function stimme_index(string $id): int
{
    foreach (stimmen() as $i => $q) {
        if ($q['id'] === $id && stimme_mit_seite($q)) return $i;
    }
    return -1;
}

function stimme_link(string $id): string
{
    return url('quelle', ['slug' => $id]);
}

/** Ziel für Quellen ohne eigene Seite: Original, sonst Archiv, sonst die Übersicht. */
function stimme_ziel(array $q): string
{
    if (stimme_mit_seite($q)) return stimme_link($q['id']);
    if ($q['zugang'] === 'archiv' && $q['archiv'] !== '') return $q['archiv'];
    return $q['url'] !== '' ? $q['url'] : ($q['archiv'] !== '' ? $q['archiv'] : url('stimmen') . '#' . $q['id']);
}

function stimmen_kategorien(): array
{
    return ['interviews', 'portraets', 'rezensionen', 'konzertberichte', 'nachrufe', 'erinnerungen', 'radio-tv', 'foren', 'buecher', 'nachschlagewerke', 'meldungen'];
}

function stimmen_zugaenge(): array
{
    return ['frei', 'online', 'archiv', 'abo', 'verloren'];
}

/** Sprachen mit eigener Auswahl im Filter; alle übrigen unter „weitere“. */
function stimmen_sprachen(): array
{
    return ['en', 'no', 'de'];
}

function stimme_sprache(string $code): string
{
    $namen = sprachdaten(sprache())['stimmen.sprachen'] ?? [];
    return $namen[$code] ?? strtoupper($code);
}

/** Nur bekannte Filterwerte übernehmen. */
function stimmen_filter(array $query): array
{
    $filter = ['auswahl' => '1'];
    $erlaubt = ['art' => stimmen_kategorien(), 'sprache' => [...stimmen_sprachen(), 'andere'], 'zugang' => stimmen_zugaenge()];
    foreach ($erlaubt as $key => $werte) {
        if (isset($query[$key]) && is_string($query[$key]) && in_array($query[$key], $werte, true)) $filter[$key] = $query[$key];
    }
    if (isset($query['auswahl']) && is_string($query['auswahl']) && in_array($query['auswahl'], ['0', '1', '2'], true)) $filter['auswahl'] = $query['auswahl'];
    return $filter;
}

function stimme_passt(array $q, array $filter): bool
{
    if (stimme_gewicht($q) < (int) ($filter['auswahl'] ?? 0)) return false;
    if (isset($filter['art']) && $q['kategorie'] !== $filter['art']) return false;
    if (isset($filter['zugang']) && $q['zugang'] !== $filter['zugang']) return false;
    if (isset($filter['sprache'])) {
        $sprache = $q['sprache'] === 'nn' ? 'no' : $q['sprache'];
        return $filter['sprache'] === 'andere' ? !in_array($sprache, stimmen_sprachen(), true) : $sprache === $filter['sprache'];
    }
    return true;
}

/** Quellen je Jahr; undatierte unter dem Schlüssel '' am Ende. */
function stimmen_jahre(array $filter = []): array
{
    $jahre = [];
    foreach (stimmen() as $q) {
        if (stimme_passt($q, $filter)) $jahre[substr($q['datum'], 0, 4)][] = $q;
    }
    return $jahre;
}

/** Datum in der Genauigkeit der Quelle. */
function stimme_datum(string $datum): string
{
    return $datum === '' ? t('stimmen.undatiert') : diskografie_konzertdatum($datum);
}

/** Titel, Medium oder Autor; auf Englisch die übersetzte Fassung, wo es eine gibt. */
function stimme_feld(array $q, string $feld): string
{
    $text = sprache() === 'en' && isset($q['en'][$feld]) ? $q['en'][$feld] : $q[$feld];
    return $feld === 'titel' ? str_replace(['[', ']'], '', $text) : $text;
}

/** Sprache des angezeigten Titels: übersetzte Beschreibungen stehen in der Seitensprache. */
function stimme_titelsprache(array $q): string
{
    return sprache() === 'en' && isset($q['en']['titel']) ? 'en' : (str_starts_with($q['titel'], '[') ? 'de' : $q['sprache']);
}

/** Text in der Seitensprache, sonst Deutsch mit Sprachauszeichnung. */
function stimme_text(array $texte): array
{
    return isset($texte[sprache()]) && $texte[sprache()] !== [] && $texte[sprache()] !== ''
        ? [$texte[sprache()], sprache()] : [$texte['de'], 'de'];
}

/** Rezensionen und andere Quellen mit eigener Seite zu einer Ausgabe der Diskographie. */
function stimmen_zur_ausgabe(string $id): array
{
    return array_values(array_filter(stimmen(), fn($q) => stimme_mit_seite($q) && in_array($id, $q['ausgaben'], true)));
}

function stimme_lizenz(array $lizenz): array
{
    $kurz = ['ccbyncnd' => ['CC BY-NC-ND 4.0', 'by-nc-nd'], 'ccbync' => ['CC BY-NC 4.0', 'by-nc']][$lizenz['name']];
    return ['name' => $kurz[0], 'url' => 'https://creativecommons.org/licenses/' . $kurz[1] . '/4.0/deed.' . sprache()];
}
