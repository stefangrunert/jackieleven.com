<?php /** @var array $st */ [$bildtext] = sfeld($st, 'bildtext'); ?>
<div class="stage-visual">
  <img src="/assets/bilder/<?= e($st['bild']) ?>" alt="<?= e($bildtext) ?>">
  <?php if ($bildtext !== ''): ?><span class="bildtext"><?= sfeld_html($st, 'bildtext') ?></span><?php endif; ?>
</div>

<div class="stage-body" data-art="<?= e($st['art']) ?>">
  <p class="stage-year"><?= e($st['jahr']) ?></p>
  <p class="stage-kind"><?= sfeld_html($st, 'label') ?></p>

  <?php if ($st['zitat'] !== ''): ?>
    <blockquote lang="en">
      <p><?= e($st['zitat']) ?></p>
      <cite lang="<?= e(sprache()) ?>">
        <a href="<?= e($st['quelle']['archiv']) ?>" rel="noopener noreferrer" target="_blank"><?= e(t('station.zitat_von', ['quelle' => quelle_text($st['quelle'])])) ?></a>
      </cite>
    </blockquote>
  <?php else: ?>
    <p class="kein-zitat"><?= e(t('station.kein_zitat')) ?></p>
  <?php endif; ?>

  <p class="stage-text"><?= sfeld_html($st, 'text') ?></p>
</div>
