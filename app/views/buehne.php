<?php /** @var array $st @var int $i */ ?>
<div class="stage-visual">
  <img src="/assets/bilder/<?= e($st['bild']) ?>" alt="<?= e($st['bildtext']) ?>">
  <?php if ($st['bildtext']): ?><span class="bildtext"><?= e($st['bildtext']) ?></span><?php endif; ?>
</div>

<div class="stage-body" data-art="<?= e($st['art']) ?>">
  <p class="stage-year"><?= e($st['jahr']) ?></p>
  <p class="stage-kind"><?= e($st['label']) ?></p>

  <?php if ($st['zitat'] !== ''): ?>
    <blockquote lang="en">
      <?= e($st['zitat']) ?>
      <cite>
        <?php if ($st['archiv']): ?>
          <a href="<?= e($st['archiv']) ?>" rel="noopener noreferrer" target="_blank">Jackie Leven, <?= e($st['quelle']) ?></a>
        <?php else: ?>
          Jackie Leven, <?= e($st['quelle']) ?>
        <?php endif; ?>
      </cite>
    </blockquote>
  <?php else: ?>
    <p class="kein-zitat">Über diese Zeit hat er nichts geschrieben.</p>
  <?php endif; ?>

  <p class="stage-text"><?= e($st['text']) ?></p>
</div>
