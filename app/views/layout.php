<?php /** @var string $inhalt @var string $titel @var string $nav @var bool $noindex */ ?>
<!DOCTYPE html>
<html lang="<?= e(sprache()) ?>">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($titel) ?></title>
<meta name="description" content="<?= e(t('meta.beschreibung')) ?>">
<?php if (!empty($noindex)): ?>
<meta name="robots" content="noindex">
<?php endif; ?>
<?php if (route()['name'] !== null): ?>
<?php foreach (SPRACHEN as $s): ?>
<link rel="alternate" hreflang="<?= e($s) ?>" href="<?= e(absolut(alternativ_url($s))) ?>">
<?php endforeach; ?>
<link rel="alternate" hreflang="x-default" href="<?= e(absolut(alternativ_url(STANDARD_SPRACHE))) ?>">
<?php endif; ?>
<link rel="stylesheet" href="/assets/css/site.css?v=<?= filemtime(APP_ROOT . '/../assets/css/site.css') ?>">
</head>
<body>

<header class="topbar">
  <a class="name" href="<?= e(url('start')) ?>">Jackie Leven</a>
  <div class="kopf-rechts">
    <nav aria-label="<?= e(t('nav.label')) ?>">
      <a href="<?= e(url('start')) ?>"<?= $nav === 'zeitreise' ? ' class="hier"' : '' ?>><?= e(t('nav.zeitreise')) ?></a>
      <a href="<?= e(url('biografie')) ?>"<?= $nav === 'biografie' ? ' class="hier"' : '' ?>><?= e(t('nav.biografie')) ?></a>
      <a href="<?= e(url('diskografie')) ?>"<?= $nav === 'diskografie' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.diskografie')) ?></a>
      <a href="<?= e(url('pool')) ?>"<?= $nav === 'pool' ? ' class="hier" aria-current="page"' : '' ?>><?= e(t('nav.pool')) ?></a>
      <a href="<?= e(url('ueber')) ?>"<?= $nav === 'ueber' ? ' class="hier"' : '' ?>><?= e(t('nav.ueber')) ?></a>
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

<footer>
  <span><?= e(t('fuss.lebensdaten')) ?></span>
  <span><?= e(t('fuss.hinweis')) ?></span>
</footer>

<script src="/assets/js/zeitgraph.js" defer></script>
<?php if ($nav === 'pool'): ?>
<script src="/assets/js/kolumnen.js?v=<?= filemtime(APP_ROOT . '/../assets/js/kolumnen.js') ?>" defer></script>
<?php endif; ?>
<?php if ($nav === 'diskografie'): ?>
<script src="/assets/js/diskografie.js?v=<?= filemtime(APP_ROOT . '/../assets/js/diskografie.js') ?>" defer></script>
<?php endif; ?>
</body>
</html>
