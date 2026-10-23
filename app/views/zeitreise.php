<?php
/** @var int $aktiv */
$alle = stationen();
$n    = count($alle);
$vor  = $alle[($aktiv - 1 + $n) % $n];
$nach = $alle[($aktiv + 1) % $n];
$seoAttribut = fn(string $name, array $p, string $titel) => e(json_encode(seo_daten($titel, ['name' => $name, 'p' => $p]), JSON_THROW_ON_ERROR));
$alternativen = function (?string $slug = null): string {
    $urls = [];
    foreach ([...SPRACHEN, 'x-default'] as $s) {
        $urls[$s] = $slug === null
            ? url('zeitreise', [], $s === 'x-default' ? STANDARD_SPRACHE : $s)
            : url('station', ['slug' => $slug], $s === 'x-default' ? STANDARD_SPRACHE : $s);
    }
    return e(json_encode($urls, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR));
};
?>
<div class="stage-wrap">

  <nav class="graph" aria-label="<?= e(t('graph.label')) ?>">
    <div class="graph-viewport" id="g-viewport">
      <div class="graph-track" id="g-track" data-seo="<?= $seoAttribut('zeitreise', [], t('titel.zeitreise')) ?>" data-alternativen="<?= $alternativen() ?>" data-titel="<?= e(t('titel.zeitreise')) ?>">
        <?php foreach ($alle as $i => $s): ?>
          <a class="g-marker<?= $i === $aktiv ? ' active' : '' ?>"
             href="<?= e(url('station', ['slug' => $s['slug']])) ?>"
             data-i="<?= $i ?>"
             data-seo="<?= $seoAttribut('station', ['slug' => $s['slug']], t('titel.station', ['jahr' => $s['jahr'], 'titel' => sfeld($s, 'titel')[0]])) ?>"
             data-art="<?= e($s['art']) ?>"
             data-jahr="<?= e($s['jahr']) ?>"
             data-alternativen="<?= $alternativen($s['slug']) ?>"
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
