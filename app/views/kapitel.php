<?php
/** @var int $i */
$liste = kapitelliste();
$k     = $liste[$i];
$teile = kapitel($k);
[$text, $textSprache] = $teile['text'];
[$anm, $anmSprache]   = $teile['anmerkung'];
[$app, $appSprache]   = $teile['apparat'];
$vor   = $liste[$i - 1] ?? null;
$nach  = $liste[$i + 1] ?? null;
$lang  = fn(string $s) => $s !== sprache() ? ' lang="' . e($s) . '"' : '';
$intro = $intro ?? false;
$startseite = $startseite ?? false;
?>
<div class="bio-raum bio-detailraum">
<?= render('kapitel-zeitstrahl', ['aktiv' => $i, 'startseite' => $startseite]) ?>
<article class="text-seite kapitel bio-inhalt">

  <?php if ($intro): ?>
    <?= render_lokal('biografie-intro') ?>
  <?php endif; ?>

  <?php if (!$intro): ?>
    <aside class="pastiche-hinweis" role="note">
      <span class="etikett"><?= e(t('pastiche.etikett')) ?></span>
      <p><?= e(t('pastiche.erklaerung')) ?>
        <a href="<?= e(url('biografie')) ?>"><?= e(t('pastiche.ueber_buch')) ?></a></p>
    </aside>
  <?php endif; ?>

  <p class="kicker"><?= e(t('pastiche.kapitel_von', ['nr' => $i + 1, 'gesamt' => count($liste)])) ?> <span aria-hidden="true">·</span> <?= e($k['zeit']) ?></p>
  <?php if ($intro): ?>
    <h2 class="kapitel-titel" lang="en"><?= e($k['titel']) ?></h2>
  <?php else: ?>
    <h1 class="kapitel-titel" lang="en"><?= e($k['titel']) ?></h1>
  <?php endif; ?>

  <?php if ($anm !== ''): ?>
    <div class="anmerkung"<?= $lang($anmSprache) ?>><?= md($anm) ?></div>
  <?php endif; ?>

  <?php if ($textSprache !== sprache()): ?>
    <p class="teil-fremd"><?= e(t('pastiche.text_fremd', ['sprache' => t('sprachname.' . $textSprache)])) ?></p>
  <?php elseif ($textSprache !== 'en'): ?>
    <p class="teil-fremd"><?= e(t('pastiche.uebersetzt')) ?> ·
      <a href="<?= e(url('kapitel', ['slug' => $k['slug']], 'en')) ?>" hreflang="en"><?= e(t('pastiche.zum_original')) ?></a></p>
  <?php endif; ?>
  <div class="pastiche-text" data-nosnippet lang="<?= e($textSprache) ?>">
    <?= md($text) ?>
  </div>

  <?php if ($app !== ''): ?>
    <section class="apparat">
      <?php if ($appSprache !== sprache()): ?>
        <p class="teil-fremd"><?= e(t('pastiche.apparat_fremd', ['sprache' => t('sprachname.' . $appSprache)])) ?></p>
      <?php endif; ?>
      <div<?= $lang($appSprache) ?>><?= md($app) ?></div>
    </section>
  <?php endif; ?>

  <nav class="kapitel-nav" aria-label="<?= e(t('pastiche.kapitelnav')) ?>">
    <?php if ($vor): ?>
      <a href="<?= e(url('kapitel', ['slug' => $vor['slug']])) ?>" rel="prev">&larr; <span lang="en"><?= e($vor['titel']) ?></span></a>
    <?php else: ?><span></span><?php endif; ?>
    <a href="<?= e(url('biografie')) ?>"><?= e(t('pastiche.inhalt')) ?></a>
    <?php if ($nach): ?>
      <a href="<?= e(url('kapitel', ['slug' => $nach['slug']])) ?>" rel="next"><span lang="en"><?= e($nach['titel']) ?></span> &rarr;</a>
    <?php else: ?><span></span><?php endif; ?>
  </nav>

</article>
</div>
