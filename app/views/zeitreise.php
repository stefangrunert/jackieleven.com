<?php
/** @var int $aktiv */
$alle = stationen();
$n    = count($alle);
$vor  = $alle[($aktiv - 1 + $n) % $n];
$nach = $alle[($aktiv + 1) % $n];
?>
<div class="stage-wrap">

  <nav class="graph" aria-label="<?= e(t('graph.label')) ?>">
    <div class="graph-viewport" id="g-viewport">
      <div class="graph-track" id="g-track">
        <?php foreach ($alle as $i => $s): ?>
          <a class="g-marker<?= $i === $aktiv ? ' active' : '' ?>"
             href="<?= e(url('station', ['slug' => $s['slug']])) ?>"
             data-i="<?= $i ?>"
             data-art="<?= e($s['art']) ?>"
             data-jahr="<?= e($s['jahr']) ?>"
             <?= $i === $aktiv ? 'aria-current="true"' : '' ?>>
            <span class="dot"></span>
            <span class="g-label">
              <span class="g-year"><?= e($s['jahr']) ?></span>
              <span class="g-era"><?= sfeld_html($s, 'titel') ?></span>
            </span>
          </a>
        <?php endforeach; ?>
      </div>
    </div>
  </nav>

  <main class="stage" id="stage"><?= render('buehne', ['st' => $alle[$aktiv]]) ?></main>

</div>

<nav class="pager" aria-label="<?= e(t('pager.label')) ?>">
  <a class="knopf" href="<?= e(url('station', ['slug' => $vor['slug']])) ?>" rel="prev">&larr; <?= e($vor['jahr']) ?></a>
  <span class="count" id="count"><?= sprintf('%02d / %02d', $aktiv + 1, $n) ?></span>
  <a class="knopf" href="<?= e(url('station', ['slug' => $nach['slug']])) ?>" rel="next"><?= e($nach['jahr']) ?> &rarr;</a>
</nav>
