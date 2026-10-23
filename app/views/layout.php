<?php /** @var string $inhalt @var string $titel @var string $nav @var bool $noindex */ ?>
<!DOCTYPE html>
<html lang="<?= e(sprache()) ?>">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?= render('seo', ['seo' => seo_daten($titel), 'noindex' => $noindex]) ?>
<?php if ($nav === 'start'): ?>
<link rel="preload" href="/assets/fonts/instrument-serif-italic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts/home.css">
<?php endif; ?>
<link rel="stylesheet" href="/assets/css/site.css?v=<?= filemtime(PUBLIC_ROOT . '/assets/css/site.css') ?>">
</head>
<body<?= $nav === 'start' ? ' class="home-page"' : '' ?>>

<header class="topbar">
  <a class="name" href="<?= e(url('start')) ?>" aria-label="<?= e(t('nav.start')) ?>"<?= $nav === 'start' ? ' aria-current="page"' : '' ?>>
    <img class="site-logo" src="/assets/bilder/jackie-leven-logo-originalnah.png" alt="" width="56" height="56">
    <span>Jackie Leven</span>
  </a>
  <div class="kopf-rechts">
    <nav aria-label="<?= e(t('nav.label')) ?>">
      <a href="<?= e(url('hoeren')) ?>"<?= $nav === 'hoeren' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.hoeren')) ?></a>
      <a href="<?= e(url('zeitreise')) ?>"<?= $nav === 'zeitreise' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.zeitreise')) ?></a>
      <a href="<?= e(url('diskografie')) ?>"<?= $nav === 'diskografie' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.diskografie')) ?></a>
      <a href="<?= e(url('biografie')) ?>"<?= $nav === 'biografie' ? ' class="hier"' : '' ?>><?= e(t('nav.biografie')) ?></a>
      <a href="<?= e(url('pool')) ?>"<?= $nav === 'pool' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.pool')) ?></a>
      <a href="<?= e(url('stimmen')) ?>"<?= $nav === 'stimmen' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.stimmen')) ?></a>
      <a href="<?= e(url('ueber')) ?>"<?= $nav === 'ueber' ? ' class="hier"' : '' ?>><?= e(t('nav.ueber')) ?></a>
      <a class="nav-mitmachen" href="<?= e(url('mitmachen')) ?>"<?= $nav === 'mitmachen' ? ' aria-current="page"' : '' ?>><?= e(t('nav.mitmachen')) ?></a>
    </nav>
    <nav class="sprachen" aria-label="<?= e(t('sprache.wahl')) ?>">
      <?php foreach (SPRACHEN as $s): ?>
        <?php if ($s === sprache()): ?>
          <span lang="<?= e($s) ?>" aria-current="true"><?= e(strtoupper($s)) ?></span>
        <?php else: ?>
          <a href="<?= e(alternativ_url($s)) ?>" hreflang="<?= e($s) ?>" lang="<?= e($s) ?>" title="<?= e(t('sprache.name', [], $s)) ?>"><?= e(strtoupper($s)) ?></a>
        <?php endif; ?>
      <?php endforeach; ?>
    </nav>
  </div>
</header>

<?= $inhalt ?>

<footer<?= $nav === 'start' ? ' class="home-footer"' : '' ?>>
  <a class="fuss-impressum" href="<?= e(url('impressum')) ?>"<?= $nav === 'impressum' ? ' aria-current="page"' : '' ?>><?= e(t('nav.impressum')) ?></a>
  <div class="fuss-text">
    <span><?= e(t('fuss.hommage')) ?></span>
    <span><?= e(t('fuss.unabhaengig')) ?></span>
  </div>
</footer>
<?php if ($nav === 'start'): ?>
<script src="/assets/js/startseite.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/startseite.js') ?>" defer></script>
<?php endif; ?>

<?php if ($nav === 'zeitreise'): ?>
<script src="/assets/js/zeitgraph.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/zeitgraph.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'pool'): ?>
<script src="/assets/js/kolumnen.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/kolumnen.js') ?>" defer></script>
<?php endif; ?>
<?php if (in_array($nav, ['start', 'diskografie', 'hoeren'], true)): ?>
<script src="/assets/js/musiklinks.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/musiklinks.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'diskografie'): ?>
<script src="/assets/js/diskografie.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/diskografie.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'biografie'): ?>
<script src="/assets/js/biografie.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/biografie.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'stimmen'): ?>
<script src="/assets/js/stimmen.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/stimmen.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'hoeren'): ?>
<script src="/assets/js/hoeren.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/hoeren.js') ?>" defer></script>
<?php endif; ?>
</body>
</html>
