<?php
/** @var int $aktiv */
$alle = stationen();
$st   = $alle[$aktiv];
$vor  = $alle[($aktiv - 1 + count($alle)) % count($alle)];
$nach = $alle[($aktiv + 1) % count($alle)];
?>
<div class="stage-wrap">

  <nav class="graph" aria-label="Zeitleiste">
    <div class="graph-viewport" id="g-viewport">
      <div class="graph-track" id="g-track">
        <?php foreach ($alle as $i => $s): ?>
          <a class="g-marker<?= $i === $aktiv ? ' active' : '' ?>"
             href="/station/<?= e($s['slug']) ?>"
             data-i="<?= $i ?>"
             data-art="<?= e($s['art']) ?>"
             data-jahr="<?= e($s['jahr']) ?>"
             <?= $i === $aktiv ? 'aria-current="true"' : '' ?>>
            <span class="dot"></span>
            <span class="g-label">
              <span class="g-year"><?= e($s['jahr']) ?></span>
              <span class="g-era"><?= e($s['titel']) ?></span>
            </span>
          </a>
        <?php endforeach; ?>
      </div>
    </div>
  </nav>

  <main class="stage" id="stage"><?= render('buehne', ['st' => $st, 'i' => $aktiv]) ?></main>

</div>

<div class="pager">
  <a class="knopf" href="/station/<?= e($vor['slug']) ?>" rel="prev">&larr; <?= e($vor['jahr']) ?></a>
  <span class="count" id="count"><?= str_pad((string)($aktiv + 1), 2, '0', STR_PAD_LEFT) ?> / <?= str_pad((string)count($alle), 2, '0', STR_PAD_LEFT) ?></span>
  <a class="knopf" href="/station/<?= e($nach['slug']) ?>" rel="next"><?= e($nach['jahr']) ?> &rarr;</a>
</div>
