<?php /** @var ?array $vor @var ?array $nach @var array $platte @var array $kontext @var bool $oben */ ?>
<nav class="disk-blaettern<?= $oben ? ' disk-blaettern--oben' : '' ?>" aria-label="<?= e(t('disk.blaettern')) ?>">
  <?php if ($vor): ?>
    <a href="<?= e(diskografie_link($vor['id'], $kontext)) ?>" rel="prev" aria-label="<?= e(t('disk.vorher') . ': ' . $vor['title']) ?>"><span aria-hidden="true">←</span><span><small><?= e(t('disk.vorher')) ?></small><?= e($vor['title']) ?></span></a>
  <?php else: ?><span></span><?php endif; ?>
  <a class="disk-uebersichtlink" href="<?= e(diskografie_zurueck($platte['id'], $kontext)) ?>" data-overview-return><?= e(t('disk.uebersicht')) ?></a>
  <?php if ($nach): ?>
    <a href="<?= e(diskografie_link($nach['id'], $kontext)) ?>" rel="next" aria-label="<?= e(t('disk.naechste') . ': ' . $nach['title']) ?>"><span><small><?= e(t('disk.naechste')) ?></small><?= e($nach['title']) ?></span><span aria-hidden="true">→</span></a>
  <?php else: ?><span></span><?php endif; ?>
</nav>
