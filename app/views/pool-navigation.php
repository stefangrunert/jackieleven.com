<?php /** @var ?array $vor @var ?array $nach @var array $k @var bool $oben */ ?>
<nav class="pool-navigation<?= $oben ? ' pool-navigation--oben' : '' ?>" aria-label="<?= e(t('pool.blaettern')) ?>">
  <?php if ($vor): ?>
    <a href="<?= e(url('kolumne', ['slug' => $vor['slug']])) ?>" rel="prev" aria-label="<?= e(t('pool.vorher') . ': ' . kolumnen_datum($vor) . ', ' . kolumnen_rubrik($vor)) ?>"><span aria-hidden="true">←</span> <?= e(t('pool.zurueck_blaettern')) ?></a>
  <?php else: ?><span></span><?php endif; ?>
  <a class="pool-archivlink" href="<?= e(url('pool_archiv')) ?>#jahr-<?= e(substr($k['datum'], 0, 4)) ?>"><?= e(t('pool.alle')) ?></a>
  <?php if ($nach): ?>
    <a href="<?= e(url('kolumne', ['slug' => $nach['slug']])) ?>" rel="next" aria-label="<?= e(t('pool.naechster') . ': ' . kolumnen_datum($nach) . ', ' . kolumnen_rubrik($nach)) ?>"><?= e(t('pool.weiter_blaettern')) ?> <span aria-hidden="true">→</span></a>
  <?php else: ?><span></span><?php endif; ?>
</nav>
