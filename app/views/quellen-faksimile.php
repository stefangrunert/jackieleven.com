<?php if (!empty($q['scan']['facsimiles'])): ?>
  <div class="quellen-faksimiles">
    <?php foreach ($q['scan']['facsimiles'] as $scan): ?>
      <figure>
        <a href="<?= e($scan['full']) ?>" target="_blank" rel="noopener noreferrer" title="<?= e(t('stimmen.scan_gross')) ?>">
          <img src="<?= e($scan['image']) ?>" width="<?= (int) $scan['width'] ?>" height="<?= (int) $scan['height'] ?>" loading="lazy" alt="<?= e(stimme_feld($q, 'medium') . ' · ' . stimme_datum($q['datum']) . ' · ' . t('stimmen.seite') . ' ' . $scan['page']) ?>">
        </a>
        <figcaption><a href="<?= e($scan['url']) ?>" target="_blank" rel="noopener noreferrer"><?= e(t('stimmen.seite') . ' ' . $scan['page']) ?></a></figcaption>
      </figure>
    <?php endforeach; ?>
  </div>
  <?php $scanLizenz = stimme_lizenz(['name' => $q['scan']['license']]); ?>
  <p class="quellen-scan-credit"><?= e(implode(' · ', array_filter([stimme_feld($q, 'autor'), stimme_feld($q, 'medium'), stimme_datum($q['datum'])]))) ?> · Nasjonalbiblioteket · <a href="<?= e($scanLizenz['url']) ?>" target="_blank" rel="noopener noreferrer license"><?= e($scanLizenz['name']) ?></a></p>
<?php endif; ?>
