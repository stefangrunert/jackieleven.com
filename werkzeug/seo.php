<?php
/** Technical SEO checks, without network requests or changes to production. */
declare(strict_types=1);
require __DIR__ . '/../app/bootstrap.php';
function seo_pruefe(bool $ok, string $message): void {
    if (!$ok) throw new RuntimeException($message);
}
function seo_anfrage(string $path, string $host = 'jackieleven.com'): array {
    $code = '$_SERVER["REQUEST_URI"]=' . var_export($path, true) . ';'
        . '$_SERVER["HTTP_HOST"]=' . var_export($host, true) . ';'
        . 'parse_str(parse_url($_SERVER["REQUEST_URI"], PHP_URL_QUERY) ?? "", $_GET);'
        . 'register_shutdown_function(function(){fwrite(STDERR,"STATUS=".(http_response_code() ?: 200));});'
        . 'require ' . var_export(dirname(__DIR__) . '/index.php', true) . ';';
    $proc = proc_open([PHP_BINARY, '-d', 'display_errors=stderr', '-r', $code], [1 => ['pipe','w'], 2 => ['pipe','w']], $pipes);
    $body = stream_get_contents($pipes[1]); $error = stream_get_contents($pipes[2]);
    fclose($pipes[1]); fclose($pipes[2]);
    seo_pruefe(proc_close($proc) === 0 && preg_match('/^STATUS=(\d+)$/', $error, $match) === 1, $path . ': ' . $error);
    return [$body, (int) $match[1]];
}
libxml_use_internal_errors(true);
$xml = simplexml_load_string(seo_anfrage('/sitemap.xml')[0]);
seo_pruefe($xml !== false, 'Sitemap is not valid XML');
$urls = [];
foreach ($xml->url as $entry) {
    $loc = (string) $entry->loc;
    seo_pruefe(str_starts_with($loc, SEO_ORIGIN . '/') && !str_contains($loc, '?'), 'Noncanonical sitemap URL');
    seo_pruefe(count($entry->children('http://www.w3.org/1999/xhtml')) === 3, 'Missing sitemap language variants');
    $urls[] = $loc;
}
seo_pruefe(count($urls) === count(array_unique($urls)) && count($urls) === count(seo_routen()) * 2, 'Missing or duplicated sitemap URLs');
// Check metadata generation and route identity for every sitemap page in both languages.
foreach (seo_routen() as [$name, $p]) foreach (SPRACHEN as $lang) {
    sprache($lang);
    $seo = seo_daten('Test', ['name' => $name, 'p' => $p]);
    seo_pruefe(mb_strlen($seo['beschreibung']) > 30 && mb_strlen($seo['beschreibung']) <= 165, 'Empty/oversize description: ' . $seo['url']);
    seo_pruefe(in_array($seo['url'], $urls, true), 'Metadata/sitemap disagree');
}
$paths = ['/de/', '/en/', '/de/stimmen?auswahl=2', '/en/discography/1975-control?von=1975-control', '/en/biography', '/de/zeitreise/1950-kirkcaldy',
    url('kolumne', ['slug'=>kolumnen()[0]['slug']], 'en'), url('quelle', ['slug'=>stimmen()[0]['id']], 'de')];
foreach ($paths as $path) {
    [$html, $status] = seo_anfrage($path);
    seo_pruefe($status === 200, 'Wrong status: ' . $path);
    $dom = new DOMDocument(); $dom->loadHTML($html); $xp = new DOMXPath($dom);
    seo_pruefe($xp->query('//title')->length === 1, 'Missing/duplicate title');
    seo_pruefe($xp->query('//meta[@name="description"]')->length === 1, 'Missing/duplicate description');
    $canonical = $xp->query('//link[@rel="canonical"]');
    seo_pruefe($canonical->length === 1 && $canonical[0]->getAttribute('href') === SEO_ORIGIN . parse_url($path, PHP_URL_PATH), 'Wrong canonical: ' . $path);
    seo_pruefe($xp->query('//link[@rel="alternate"]')->length === 3, 'Missing languages');
    seo_pruefe(!str_contains($xp->query('//meta[@name="robots"]')[0]->getAttribute('content'), 'noindex'), 'Live page unexpectedly noindex');
    $data = json_decode($xp->query('//script[@type="application/ld+json"]')[0]->textContent, true, flags: JSON_THROW_ON_ERROR);
    seo_pruefe($data['@graph'][2]['url'] === $canonical[0]->getAttribute('href'), 'Structured data URL mismatch');
}
[$html, $status] = seo_anfrage('/de/does-not-exist');
seo_pruefe($status === 404 && str_contains($html, 'noindex') && !str_contains($html, 'rel="canonical"'), '404 indexing wrong');
foreach (['localhost:8765', 'jackieleven.localhost', 'untrusted.example'] as $host) {
    seo_pruefe(str_contains(seo_anfrage('/en/', $host)[0], 'noindex'), 'Dev/staging page indexable');
    seo_pruefe(str_contains(seo_anfrage('/robots.txt', $host)[0], 'Disallow: /'), 'Dev robots missing');
}
seo_pruefe(str_contains(seo_anfrage('/robots.txt')[0], 'Sitemap: ' . SEO_ORIGIN . '/sitemap.xml'), 'Live robots lacks sitemap');
$chapter = url('kapitel', ['slug'=>kapitelliste()[0]['slug']], 'en');
seo_pruefe(!in_array(SEO_ORIGIN . $chapter, $urls, true) && str_contains(seo_anfrage($chapter)[0], 'noindex'), 'Fictional chapter indexable');
seo_pruefe(str_contains(seo_anfrage('/en/biography')[0], 'class="pastiche-text" data-nosnippet'), 'Fictional prose allowed in search snippets');
$beacon = '//script[@src="https://static.cloudflareinsights.com/beacon.min.js"]';
$doc = new DOMDocument(); $doc->loadHTML(seo_anfrage('/en/')[0], LIBXML_NOERROR); $live = new DOMXPath($doc);
seo_pruefe($live->query($beacon)->length === 1 && str_contains($live->query($beacon)[0]->getAttribute('data-cf-beacon'), ANALYTICS_TOKEN), 'Analytics beacon missing on live host');
$doc = new DOMDocument(); $doc->loadHTML(seo_anfrage('/en/', 'localhost:8765')[0], LIBXML_NOERROR); $dev = new DOMXPath($doc);
seo_pruefe($dev->query($beacon)->length === 0, 'Analytics beacon on dev host');
echo count($urls) . " sitemap URLs checked; metadata, languages, structured data, filters, 404, staging and pastiche checks passed.\n";
