<?php
/** @var array $st */
[$bildtext] = sfeld($st, 'bildtext');
$tusche = ($st['bildstil'] ?? '') === 'tusche';
$quelltext = $st['quelle'] === null ? null : kolumne_nach_datei($st['quelle']['datei']);
$platte = null;
if (isset($st['platte']) && ($plattenindex = diskografie_index($st['platte'])) >= 0) {
  $platte = diskografie()['releases'][$plattenindex];
}
?>
<div class="stage-visual<?= $tusche ? ' stage-visual--tusche' : '' ?>">
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
        <?php if ($quelltext !== null): ?>
          <a href="<?= e(url('kolumne', ['slug' => $quelltext['slug']])) ?>"><?= e(t('station.zitat_von', ['quelle' => quelle_text($st['quelle'])])) ?></a>
        <?php else: ?>
          <a href="<?= e($st['quelle']['archiv']) ?>" rel="noopener noreferrer" target="_blank"><?= e(t('station.zitat_von', ['quelle' => quelle_text($st['quelle'])])) ?></a>
        <?php endif; ?>
      </cite>
    </blockquote>
  <?php else: ?>
    <p class="kein-zitat"><?= e(t('station.kein_zitat')) ?></p>
  <?php endif; ?>

  <p class="stage-text"><?= sfeld_html($st, 'text') ?></p>

  <?php if ($platte !== null): ?>
    <a class="stage-werk" href="<?= e(diskografie_link($platte['id'])) ?>">
      <?php if (isset($platte['cover'])): ?>
        <img src="<?= e($platte['cover']) ?>" alt="" width="600" height="600" loading="lazy" decoding="async" referrerpolicy="no-referrer">
      <?php endif; ?>
      <span class="stage-werk-text">
        <span class="stage-werk-meta"><?= e(t('nav.diskografie')) ?> · <?= e((string) $platte['year']) ?></span>
        <span class="stage-werk-titel" lang="en"><?= e($platte['title']) ?></span>
        <span class="stage-werk-kuenstler"><?= e($platte['artist']) ?></span>
      </span>
    </a>
  <?php endif; ?>
</div>
