<header class="home-kopf">
  <a class="home-wortmarke" href="<?= e(url('start')) ?>" aria-label="<?= e(t('nav.start')) ?>" aria-current="page">Jackie Leven</a>
  <div class="home-kopfwerkzeuge">
    <nav class="home-sprachen" aria-label="<?= e(t('sprache.wahl')) ?>">
      <?php foreach (SPRACHEN as $s): if ($s === sprache()) continue; ?>
        <a href="<?= e(alternativ_url($s)) ?>" hreflang="<?= e($s) ?>" lang="<?= e($s) ?>" title="<?= e(t('sprache.name', [], $s)) ?>"><?= e(strtoupper($s)) ?></a>
      <?php endforeach; ?>
    </nav>
    <button class="home-menuknopf" type="button" aria-label="<?= e(t('home.menue')) ?>" aria-expanded="false" aria-controls="home-menu" hidden><span></span><span></span></button>
  </div>
  <nav class="home-menu" id="home-menu" aria-label="<?= e(t('nav.label')) ?>">
    <?php foreach (['hoeren', 'diskografie', 'zeitreise', 'biografie', 'pool', 'ueber', 'mitmachen'] as $rubrik): ?>
      <a href="<?= e(url($rubrik)) ?>"<?= $rubrik === 'mitmachen' ? ' class="nav-mitmachen"' : '' ?>><?= e(t('nav.' . $rubrik)) ?></a>
    <?php endforeach; ?>
  </nav>
</header>
