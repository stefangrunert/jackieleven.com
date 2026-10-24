<?php if ($q['auszuege']): ?>
  <div class="quellen-auszuege">
    <?php foreach ($q['auszuege'] as $auszug): ?>
      <figure>
        <a href="<?= e($auszug['image']) ?>" target="_blank" rel="noopener noreferrer" title="<?= e(t('stimmen.auszug_gross')) ?>">
          <img src="<?= e($auszug['image']) ?>" width="<?= (int) $auszug['width'] ?>" height="<?= (int) $auszug['height'] ?>" loading="lazy" decoding="async" alt="<?= e($auszug['caption'][sprache()]) ?>">
        </a>
        <figcaption>
          <?= e($auszug['caption'][sprache()]) ?>
          <a href="<?= e($auszug['url']) ?>" target="_blank" rel="noopener noreferrer"><?= e($auszug['source'][sprache()]) ?></a>
        </figcaption>
      </figure>
    <?php endforeach; ?>
  </div>
  <p class="quellen-scan-credit"><?= e(t('stimmen.auszug_hinweis')) ?></p>
<?php endif; ?>
