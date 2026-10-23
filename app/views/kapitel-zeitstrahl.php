<?php
/** @var int|null $aktiv */
$aktiv = $aktiv ?? null;
$startseite = $startseite ?? false;
?>
<nav class="bio-zeitstrahl" aria-label="<?= e(t('pastiche.kapitelnav')) ?>">
  <div class="bio-zeitfenster">
    <ol class="bio-spur">
      <?php foreach (kapitelliste() as $i => $k): ?>
        <li>
          <a class="g-marker bio-marker<?= $aktiv === $i ? ' active' : '' ?>"
             data-art="leben"
             href="<?= e($startseite && $i === 0 ? url('biografie') : url('kapitel', ['slug' => $k['slug']])) ?>"
             <?= $aktiv === $i ? 'aria-current="page"' : '' ?>>
            <span class="dot" aria-hidden="true"></span>
            <span class="g-label">
              <span class="g-year"><?= e($k['zeit']) ?></span>
              <span class="g-era" lang="en"><?= e($k['titel']) ?></span>
            </span>
          </a>
        </li>
      <?php endforeach; ?>
    </ol>
  </div>
</nav>
