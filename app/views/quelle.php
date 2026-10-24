<?php
/** @var int $i Position in stimmen() */
$q = stimmen()[$i];
$mitSeite = array_values(array_filter(stimmen(), 'stimme_mit_seite'));
$pos = array_search($q['id'], array_column($mitSeite, 'id'), true);
$vor = $mitSeite[$pos - 1] ?? null;
$nach = $mitSeite[$pos + 1] ?? null;
[$inhalt, $inhaltSprache] = stimme_text($q['inhalt']);
$nb = str_contains($q['url'], 'nb.no');
// Zitate, die schon als Beleg mit Übersetzung stehen, nicht doppelt zeigen.
$q['zitate'] = array_values(array_filter($q['zitate'], fn($z) => !in_array(trim($z['text'], ' .'), array_map(fn($b) => trim($b['original'], ' .'), $q['beleg'] ?? []), true)));
?>
<main class="stimme-detail">
  <p class="stimme-zurueck"><a href="<?= e(url('stimmen')) ?>#<?= e($q['id']) ?>">← <?= e(t('stimmen.zurueck')) ?></a></p>
  <article>
    <header class="stimme-kopf">
      <p class="disk-kicker"><?= e(t('stimmen.kategorie.' . $q['kategorie'])) ?><?php if ($q['stufe'] === 'auswahl'): ?> · <?= e(t('stimmen.ausgewaehlt')) ?><?php endif; ?></p>
      <h1 lang="<?= e(stimme_titelsprache($q)) ?>"><?= e(stimme_feld($q, 'titel')) ?></h1>
      <dl class="disk-fakten">
        <div><dt><?= e(t('stimmen.medium')) ?></dt><dd><?= e(stimme_feld($q, 'medium')) ?></dd></div>
        <?php if ($q['autor'] !== ''): ?><div><dt><?= e(t('stimmen.autor')) ?></dt><dd><?= e(stimme_feld($q, 'autor')) ?></dd></div><?php endif; ?>
        <div><dt><?= e(t('stimmen.datum')) ?></dt><dd><?= e(stimme_datum($q['datum'])) ?></dd></div>
        <?php if ($q['scan']['pages'] !== ''): ?><div><dt><?= e(t('stimmen.seite')) ?></dt><dd><?= e($q['scan']['pages']) ?></dd></div><?php endif; ?>
        <div><dt><?= e(t('stimmen.sprache')) ?></dt><dd><?= e(stimme_sprache($q['sprache'])) ?></dd></div>
        <div><dt><?= e(t('stimmen.zugang')) ?></dt><dd><?= e(t('stimmen.zugang.' . $q['zugang'])) ?></dd></div>
      </dl>
    </header>

    <?php if ($q['korrektur'] ?? null): ?>
      <aside class="stimme-korrektur" aria-label="<?= e(t('stimmen.korrektur')) ?>"><p class="stimme-korrektur-titel"><?= e(t('stimmen.korrektur')) ?></p><p><?= md_inline($q['korrektur'][sprache()] ?? $q['korrektur']['de']) ?></p></aside>
    <?php endif; ?>

    <section class="stimme-inhalt" aria-label="<?= e(t('stimmen.inhalt')) ?>">
      <?php if ($inhalt === null): ?>
        <p class="stimme-hinweis"><?= e(t('stimmen.in_arbeit')) ?></p>
      <?php else: ?>
        <div>
          <?php foreach ($inhalt as $absatz): ?><p><?= md_inline($absatz) ?></p><?php endforeach; ?>
        </div>
      <?php endif; ?>
      <?php if ($inhalt !== null): ?><p class="stimme-hinweis"><?= e(t('stimmen.eigene_worte')) ?></p><?php endif; ?>
    </section>

    <?php if ($q['beleg'] ?? []): ?>
      <section class="stimme-beleg" aria-labelledby="beleg">
        <h2 id="beleg"><?= e(t('stimmen.beleg')) ?></h2>
        <?php foreach ($q['beleg'] as $beleg): ?>
          <figure>
            <blockquote lang="<?= e($q['sprache']) ?>"><p><?= e($beleg['original']) ?></p></blockquote>
            <figcaption><?= e($beleg[sprache()] ?? $beleg['de']) ?></figcaption>
          </figure>
        <?php endforeach; ?>
        <p class="stimme-hinweis"><?= e(t('stimmen.beleg_hinweis')) ?></p>
      </section>
    <?php endif; ?>

    <?php if ($q['zitate']): ?>
      <section class="stimme-zitate" aria-label="<?= e(t('stimmen.zitate')) ?>">
        <?php foreach ($q['zitate'] as $zitat): ?>
          <figure>
            <blockquote lang="<?= e($q['sprache']) ?>"><p><?= e($zitat['text']) ?></p></blockquote>
            <?php $kontext = sprache() === 'de' ? $zitat['kontext'] : ($zitat['kontext_' . sprache()] ?? ''); ?>
            <?php if ($kontext !== ''): ?><figcaption><?= md_inline($kontext) ?></figcaption><?php endif; ?>
          </figure>
        <?php endforeach; ?>
      </section>
    <?php endif; ?>

    <section class="stimme-quelle" aria-labelledby="quelle">
      <h2 id="quelle"><?= e(t('stimmen.lesen')) ?></h2>
      <?php require __DIR__ . '/quellen-faksimile.php'; ?>
      <?php require __DIR__ . '/quellen-auszuege.php'; ?>
      <ul>
        <?php if ($q['url'] !== ''): ?><li><a href="<?= e($q['url']) ?>" target="_blank" rel="noopener noreferrer"><?= e(t($nb ? 'stimmen.nb' : 'stimmen.original')) ?></a></li><?php endif; ?>
        <?php if ($q['archiv'] !== '' && $q['archiv'] !== $q['url']): ?><li><a href="<?= e($q['archiv']) ?>" target="_blank" rel="noopener noreferrer"><?= e(t('stimmen.archiv')) ?></a></li><?php endif; ?>
      </ul>
      <?php if ($q['lizenz'] && empty($q['scan']['facsimiles'])): $lizenz = stimme_lizenz($q['lizenz']); ?>
        <p class="stimme-lizenz"><?= str_replace('{lizenz}', '<a href="' . e($lizenz['url']) . '" target="_blank" rel="noopener noreferrer license">' . e($lizenz['name']) . '</a>', e(t('stimmen.lizenz', ['autor' => $q['autor'] !== '' ? $q['autor'] : '–', 'medium' => $q['medium']]))) ?></p>
      <?php endif; ?>
    </section>

    <?php if ($q['ausgaben']): ?>
      <section class="stimme-bezuege" aria-labelledby="bezuege">
        <h2 id="bezuege"><?= e(t('stimmen.ausgaben')) ?></h2>
        <ul>
          <?php foreach ($q['ausgaben'] as $id): $platte = diskografie()['releases'][diskografie_index($id)]; ?>
            <li><a href="<?= e(diskografie_link($id)) ?>"><?= e($platte['title']) ?></a> <span><?= $platte['year'] ?> · <?= e($platte['artist']) ?></span></li>
          <?php endforeach; ?>
        </ul>
      </section>
    <?php endif; ?>
  </article>

  <nav class="stimme-blaettern" aria-label="<?= e(t('stimmen.blaettern')) ?>">
    <?php if ($vor): ?><a rel="prev" href="<?= e(stimme_link($vor['id'])) ?>"><span>← <?= e(t('stimmen.vorher')) ?></span><span lang="<?= e(stimme_titelsprache($vor)) ?>"><?= e(stimme_feld($vor, 'titel')) ?></span></a><?php else: ?><span></span><?php endif; ?>
    <?php if ($nach): ?><a rel="next" href="<?= e(stimme_link($nach['id'])) ?>"><span><?= e(t('stimmen.naechste')) ?> →</span><span lang="<?= e(stimme_titelsprache($nach)) ?>"><?= e(stimme_feld($nach, 'titel')) ?></span></a><?php endif; ?>
  </nav>
</main>
