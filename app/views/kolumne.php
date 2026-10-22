<?php
/** @var int $i */
$liste = kolumnen();
$k = $liste[$i];
$vor = $liste[$i - 1] ?? null;
$nach = $liste[$i + 1] ?? null;
$capture = explode('-', $k['capture']);
$captureText = (int) $capture[2] . (sprache() === 'de' ? '. ' : ' ') . kolumnen_datum(['datum' => substr($k['capture'], 0, 7)]);
?>
<div class="pool-raum">
  <?= render('pool-zeitstrahl', ['liste' => $liste, 'aktiv' => $i]) ?>
<main class="pool-leseseite">
  <?= render('pool-navigation', ['vor' => $vor, 'nach' => $nach, 'k' => $k, 'oben' => true]) ?>
  <?php if ($i === 0): ?>
    <p class="pool-intro"><?= e(t('pool.intro')) ?></p>
  <?php endif; ?>
  <article>
    <header class="pool-lesekopf">
      <p class="pool-rubrik" lang="en"><?= e(kolumnen_rubrik($k)) ?></p>
      <h1><time datetime="<?= e($k['datum']) ?>"><?= e(kolumnen_datum($k)) ?></time></h1>
      <p class="pool-verfasser"><?= e($k['autor'] === 'Jackie Leven' ? 'Jackie Leven' : t('pool.webmaster')) ?><?php if ($k['datierung'] === 'archivdatum'): ?> · <a href="#quellenhinweis"><?= e(t('pool.archivdatum')) ?></a><?php endif; ?></p>
    </header>

    <div class="pool-original" lang="en"><?= kolumnen_html(kolumnen_lesetext($k)) ?></div>

  </article>

  <?= render('pool-navigation', ['vor' => $vor, 'nach' => $nach, 'k' => $k, 'oben' => false]) ?>

  <aside class="pool-quellennotiz" id="quellenhinweis" role="note">
    <p><?= e(t('pool.quelle')) ?> <?= e($k['website']) ?>.
      <a href="<?= e($k['archiv']) ?>" rel="noopener noreferrer"><?= e(t('pool.archivlink')) ?> <span aria-hidden="true">↗</span></a>
    </p>
    <details>
      <summary><?= e(t('pool.hinweis_titel')) ?></summary>
      <p><?= e(t('pool.hinweis')) ?></p>
      <?php if ($k['datierung'] === 'archivdatum'): ?><p><?= e(t('pool.datum_unsicher')) ?></p><?php endif; ?>
      <p><?= e(t('pool.gesichert', ['datum' => $captureText])) ?></p>
    </details>
  </aside>
</main>
</div>
