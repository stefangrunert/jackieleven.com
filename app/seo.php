<?php
declare(strict_types=1);

/** Public identity is fixed; never build canonical URLs from an untrusted Host header. */
const SEO_ORIGIN = 'https://jackieleven.com';

function seo_live(): bool
{
    return strtolower($_SERVER['HTTP_HOST'] ?? '') === 'jackieleven.com';
}

function seo_kurz(string $text, int $max = 165): string
{
    $text = trim(preg_replace('/\s+/u', ' ', html_entity_decode(strip_tags(md_inline($text)), ENT_QUOTES | ENT_HTML5, 'UTF-8')));
    if (mb_strlen($text) <= $max) return $text;
    return preg_replace('/\s+\S*$/u', '', mb_substr($text, 0, $max - 1)) . '…';
}

function seo_daten(string $titel, ?array $r = null): array
{
    $r ??= route();
    $de = sprache() === 'de';
    $beschreibungen = [
        'start' => ['Jackie Leven (1950–2011): Musik, Lebensstationen und eigene Texte. Eine persönliche Hommage mit Hörbeispielen, Diskografie und Erinnerungen.', 'Jackie Leven (1950–2011): music, life and his own writing. A personal tribute with listening selections, a discography and memories.'],
        'hoeren' => ['Eine kurze Einführung in Jackie Levens Musik: ausgewählte Videos von Doll by Doll, Soloauftritte und Erinnerungen an ihn.', 'A short introduction to Jackie Leven’s music: selected videos of Doll by Doll, solo performances and tributes.'],
        'diskografie' => ['Jackie Levens Diskografie: Alben, Singles und Liveaufnahmen, auch von John St. Field und Doll by Doll. Mit Titellisten, Quellen und Hörlinks.', 'Jackie Leven’s discography: albums, singles and live recordings, including John St. Field and Doll by Doll. Track lists, sources and listening links.'],
        'zeitreise' => ['Stationen aus Jackie Levens Leben, von seiner Kindheit in Fife bis zu den letzten Aufnahmen. Mit Auszügen aus seinen eigenen Texten.', 'Moments in Jackie Leven’s life, from his childhood in Fife to his final recordings, with excerpts from his own writing.'],
        'biografie' => ['Jackie Levens Leben als Pastiche: eine literarische Annäherung auf Grundlage seiner Texte, mit erfundenen Szenen und Gesprächen.', 'Jackie Leven’s life as a pastiche: a literary interpretation drawing on his writing, with imagined scenes and conversations.'],
        'stimmen' => ['Texte und Erinnerungen an Jackie Leven. Interviews, Kritiken und Nachrufe mit Auszügen, Faksimiles und Links zu den Quellen.', 'Writing and memories about Jackie Leven. Interviews, reviews and obituaries with excerpts, facsimiles and links to the sources.'],
        'pool_archiv' => ['Jackie Levens eigene Texte: The Deep Pool, Blogeinträge und weitere Kolumnen aus den Jahren 2002 bis 2011 im Archiv.', 'Jackie Leven’s own writing: an archive of The Deep Pool, blog entries and other columns from 2002 to 2011.'],
        'ueber' => ['Warum diese persönliche Hommage an Jackie Leven entstanden ist. Über den Autor, die Geschichte der Adresse und die Arbeit an der Seite.', 'Why this personal tribute to Jackie Leven came about. About its author, the history of the address and the work on the site.'],
        'mitmachen' => ['Erinnerungen, Informationen und Ergänzungen zu Jackie Leven beitragen. Persönlicher Kontakt zur Arbeit an dieser unabhängigen Hommage.', 'Contribute memories, information and additions about Jackie Leven. Get in touch to help with this independent tribute.'],
        'impressum' => ['Impressum und Kontakt dieser unabhängigen Hommage an Jackie Leven. Hinweise zu Inhalten, Quellen und zum Einsatz von KI.', 'Legal notice and contact for this independent tribute to Jackie Leven. Information about content, sources and the use of AI.'],
    ];
    $beschreibung = $beschreibungen[$r['name']][$de ? 0 : 1] ?? t('meta.beschreibung');
    $slug = $r['p']['slug'] ?? '';
    if ($r['name'] === 'platte' && ($i = diskografie_index($slug)) >= 0) {
        $p = diskografie()['releases'][$i];
        $beschreibung = $p['artist'] . ': ' . $p['title'] . ' (' . $p['year'] . '). ' . ($de ? 'Titelliste, Veröffentlichungsangaben, Quellen und verfügbare Hörlinks.' : 'Track list, release information, sources and available listening links.');
    } elseif ($r['name'] === 'quelle' && ($i = stimme_index($slug)) >= 0) {
        $q = stimmen()[$i];
        $beschreibung = $q['medium'] . ' · ' . $q['datum'] . ': ' . ($q['kurz'][sprache()] ?? $q['kurz']['de'] ?? stimme_feld($q, 'titel'));
    } elseif ($r['name'] === 'station' && ($i = stations_index($slug)) >= 0) {
        [$text] = sfeld(stationen()[$i], 'text');
        $beschreibung = $text;
    } elseif ($r['name'] === 'kolumne' && ($i = kolumnen_index($slug)) >= 0) {
        $k = kolumnen()[$i];
        $beschreibung = kolumnen_rubrik($k) . ' · ' . kolumnen_datum($k) . '. ' . ($de ? 'Eine Kolumne von Jackie Leven, im englischen Original aus seiner damaligen Website.' : 'A column by Jackie Leven, in its original English, from his former website.');
    }
    if ($r['name'] === 'stimmen') $titel = t('nav.stimmen') . ' · Jackie Leven';
    if (!str_contains($titel, 'Jackie Leven')) $titel .= ' · Jackie Leven';
    return ['titel' => $titel, 'beschreibung' => seo_kurz($beschreibung),
        'url' => $r['name'] === null ? null : absolut(url($r['name'], $r['p'])),
        'bild' => absolut('/assets/bilder/startseite/portrait-graphic.png')];
}

/** Only public, indexable, canonical routes; no redirects, filters or fictional chapters. */
function seo_routen(): array
{
    $routen = [];
    foreach (['start', 'hoeren', 'diskografie', 'zeitreise', 'biografie', 'stimmen', 'pool_archiv', 'ueber', 'mitmachen', 'impressum'] as $name) $routen[] = [$name, []];
    foreach (stationen() as $s) $routen[] = ['station', ['slug' => $s['slug']]];
    foreach (kolumnen() as $k) $routen[] = ['kolumne', ['slug' => $k['slug']]];
    foreach (diskografie()['releases'] as $p) $routen[] = ['platte', ['slug' => $p['id']]];
    foreach (stimmen() as $q) if (stimme_mit_seite($q)) $routen[] = ['quelle', ['slug' => $q['id']]];
    return $routen;
}

function seo_sitemap(): string
{
    $xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n" . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">';
    foreach (seo_routen() as [$name, $p]) {
        foreach (SPRACHEN as $s) {
            $xml .= "\n<url><loc>" . e(absolut(url($name, $p, $s))) . '</loc>';
            foreach (SPRACHEN as $alt) $xml .= '<xhtml:link rel="alternate" hreflang="' . $alt . '" href="' . e(absolut(url($name, $p, $alt))) . '"/>';
            $xml .= '<xhtml:link rel="alternate" hreflang="x-default" href="' . e(absolut(url($name, $p, STANDARD_SPRACHE))) . '"/></url>';
        }
    }
    return $xml . "\n</urlset>\n";
}
