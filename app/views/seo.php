<?php /** @var array $seo @var bool $noindex */ ?>
<title><?= e($seo['titel']) ?></title>
<meta name="description" content="<?= e($seo['beschreibung']) ?>">
<meta name="robots" content="<?= $noindex ? 'noindex, follow' : 'index, follow, max-image-preview:large' ?>">
<?php if ($seo['url'] !== null): ?>
<link rel="canonical" href="<?= e($seo['url']) ?>">
<?php foreach (SPRACHEN as $s): ?>
<link rel="alternate" hreflang="<?= e($s) ?>" href="<?= e(absolut(alternativ_url($s))) ?>">
<?php endforeach; ?>
<link rel="alternate" hreflang="x-default" href="<?= e(absolut(alternativ_url(STANDARD_SPRACHE))) ?>">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jackie Leven">
<meta property="og:title" content="<?= e($seo['titel']) ?>">
<meta property="og:description" content="<?= e($seo['beschreibung']) ?>">
<meta property="og:url" content="<?= e($seo['url']) ?>">
<meta property="og:locale" content="<?= sprache() === 'de' ? 'de_DE' : 'en_GB' ?>">
<meta property="og:locale:alternate" content="<?= sprache() === 'de' ? 'en_GB' : 'de_DE' ?>">
<meta property="og:image" content="<?= e($seo['bild']) ?>">
<meta property="og:image:alt" content="Jackie Leven">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="<?= e($seo['titel']) ?>">
<meta name="twitter:description" content="<?= e($seo['beschreibung']) ?>">
<meta name="twitter:image" content="<?= e($seo['bild']) ?>">
<?php
$graph = [
    ['@type' => 'WebSite', '@id' => SEO_ORIGIN . '/#website', 'url' => SEO_ORIGIN . '/', 'name' => 'Jackie Leven', 'inLanguage' => SPRACHEN,
        'description' => 'An independent personal tribute to Jackie Leven, his music and his writing.'],
    ['@type' => 'Person', '@id' => SEO_ORIGIN . '/#jackie-leven', 'name' => 'Jackie Leven'],
    ['@type' => 'WebPage', '@id' => $seo['url'] . '#webpage', 'url' => $seo['url'], 'name' => $seo['titel'], 'description' => $seo['beschreibung'],
        'inLanguage' => sprache(), 'isPartOf' => ['@id' => SEO_ORIGIN . '/#website'], 'about' => ['@id' => SEO_ORIGIN . '/#jackie-leven']],
];
?>
<script type="application/ld+json"><?= json_encode(['@context' => 'https://schema.org', '@graph' => $graph], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_THROW_ON_ERROR) ?></script>
<?php endif; ?>
