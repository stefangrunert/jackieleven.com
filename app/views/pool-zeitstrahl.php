<?php /** @var array $liste @var int $aktiv */ ?>
<nav class="pool-zeitstrahl" aria-label="<?= e(t('pool.zeitstrahl')) ?>">
  <div class="pool-zeitfenster">
    <ol class="pool-spur">
      <?php foreach ($liste as $n => $text): ?>
        <?php
        $neuesJahr = $n > 0 && substr($text['datum'], 0, 4) !== substr($liste[$n - 1]['datum'], 0, 4);
        $mehrfach = ($liste[$n - 1]['datum'] ?? null) === $text['datum'] || ($liste[$n + 1]['datum'] ?? null) === $text['datum'];
        ?>
        <li<?= $neuesJahr ? ' class="pool-jahreswechsel"' : '' ?>>
          <a class="g-marker pool-marker<?= $mehrfach ? ' pool-mehrfach' : '' ?><?= $n === $aktiv ? ' active' : '' ?>"
             href="<?= e(url('kolumne', ['slug' => $text['slug']])) ?>"
             data-art="wort"
             aria-label="<?= e(kolumnen_datum($text) . ', ' . kolumnen_rubrik($text) . ($text['datierung'] === 'archivdatum' ? ', ' . t('pool.archivdatum') : '')) ?>"
             <?= $n === $aktiv ? 'aria-current="page"' : '' ?>>
            <span class="dot" aria-hidden="true"></span>
            <span class="g-label">
              <time class="g-year" datetime="<?= e($text['datum']) ?>"><?= e(kolumnen_datum($text)) ?></time>
              <span class="g-era" lang="en"><?= e(kolumnen_rubrik($text)) ?></span>
            </span>
          </a>
        </li>
      <?php endforeach; ?>
    </ol>
  </div>
</nav>
