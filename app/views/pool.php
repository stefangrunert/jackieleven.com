<?php
$liste = kolumnen();
$jahre = [];
foreach ($liste as $k) {
    $jahre[substr($k['datum'], 0, 4)][] = $k;
}
?>
<main class="pool-index" id="textarchiv">
  <header class="pool-archivkopf">
    <a class="pool-textlink" href="<?= e(url('pool')) ?>"><?= e(t('pool.von_anfang')) ?> <span aria-hidden="true">→</span></a>
    <h1 id="archiv-titel"><?= e(t('pool.alle')) ?></h1>
  </header>

  <section class="pool-archiv" id="alle-texte" aria-labelledby="archiv-titel">
    <nav class="pool-jahreswahl" aria-label="<?= e(t('pool.jahre')) ?>">
      <?php foreach ($jahre as $jahr => $texte): ?><a href="#jahr-<?= e((string) $jahr) ?>"><?= e((string) $jahr) ?></a><?php endforeach; ?>
    </nav>
    <p class="pool-datierung"><?= e(t('pool.datierung')) ?></p>
    <?php foreach ($jahre as $jahr => $texte): ?>
      <section class="pool-jahr" id="jahr-<?= e((string) $jahr) ?>" aria-labelledby="jahr-titel-<?= e((string) $jahr) ?>">
        <div class="pool-jahreskopf">
          <h2 id="jahr-titel-<?= e((string) $jahr) ?>"><?= e((string) $jahr) ?></h2>
          <span class="pool-label"><?= e(t('pool.anzahl', ['anzahl' => count($texte)])) ?></span>
        </div>
        <ol class="pool-liste">
          <?php foreach ($texte as $k): ?>
            <li>
              <a href="<?= e(url('kolumne', ['slug' => $k['slug']])) ?>">
                <span class="pool-listendatum"><time datetime="<?= e($k['datum']) ?>"><?= e(kolumnen_datum($k)) ?></time><?php if ($k['datierung'] === 'archivdatum'): ?><small><?= e(t('pool.archivdatum')) ?></small><?php endif; ?></span>
                <span class="pool-listenrubrik"><span lang="en"><?= e(kolumnen_rubrik($k)) ?></span><?php if ($k['autor'] !== 'Jackie Leven'): ?><small><?= e(t('pool.webmaster')) ?></small><?php endif; ?></span>
              </a>
            </li>
          <?php endforeach; ?>
        </ol>
      </section>
    <?php endforeach; ?>
  </section>

  <aside class="pool-provenienz" role="note">
    <h2><?= e(t('pool.hinweis_titel')) ?></h2>
    <p><?= e(t('pool.hinweis')) ?></p>
  </aside>
</main>
