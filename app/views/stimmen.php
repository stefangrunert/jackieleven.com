<?php
/** @var array $filter aus stimmen_filter() */
$jahre = stimmen_jahre($filter);
$gezeigt = array_sum(array_map('count', $jahre));
$jahrlabel = fn(string $jahr) => $jahr === '' ? t('stimmen.undatiert') : $jahr;
$anker = fn(string $jahr) => 'jahr-' . ($jahr === '' ? 'undatiert' : $jahr);
$meta = fn(array $q) => implode(' · ', [stimme_datum($q['datum']), stimme_feld($q, 'medium'), t('stimmen.kategorie.' . $q['kategorie'])]);
?>
<div class="disk-raum stimmen-raum">
  <nav class="disk-zeitstrahl" aria-label="<?= e(t('stimmen.zeitstrahl')) ?>">
    <div class="disk-zeitfenster">
      <ol class="disk-spur">
        <?php foreach ($jahre as $jahr => $quellen): ?>
          <li>
            <a class="g-marker disk-marker" href="#<?= $anker((string) $jahr) ?>" data-art="werk">
              <span class="dot" aria-hidden="true"></span>
              <span class="g-label"><span class="g-year"><?= e($jahrlabel((string) $jahr)) ?></span><span class="g-era"><?= e(t(count($quellen) === 1 ? 'disk.eintrag' : 'disk.eintraege', ['n' => count($quellen)])) ?></span></span>
            </a>
          </li>
        <?php endforeach; ?>
      </ol>
    </div>
  </nav>

  <main class="disk-katalog stimmen" id="stimmen">
    <header class="disk-kopf">
      <p class="disk-kicker"><?= e(t('stimmen.kicker')) ?></p>
      <h1><?= e(t('nav.stimmen')) ?></h1>
      <p class="disk-intro"><?= e(t('stimmen.intro')) ?></p>
      <p class="stimmen-hinweis"><?= e(t('stimmen.hinweis')) ?></p>
    </header>

    <form class="stimmen-filter" method="get" action="<?= e(url('stimmen')) ?>">
      <label><?= e(t('stimmen.art')) ?>
        <select name="art">
          <option value=""><?= e(t('stimmen.alle_arten')) ?></option>
          <?php foreach (stimmen_kategorien() as $art): ?><option value="<?= e($art) ?>"<?= ($filter['art'] ?? '') === $art ? ' selected' : '' ?>><?= e(t('stimmen.kategorie.' . $art)) ?></option><?php endforeach; ?>
        </select>
      </label>
      <label><?= e(t('stimmen.sprache')) ?>
        <select name="sprache">
          <option value=""><?= e(t('stimmen.alle_sprachen')) ?></option>
          <?php foreach ([...stimmen_sprachen(), 'andere'] as $code): ?><option value="<?= e($code) ?>"<?= ($filter['sprache'] ?? '') === $code ? ' selected' : '' ?>><?= e($code === 'andere' ? t('stimmen.andere_sprachen') : stimme_sprache($code)) ?></option><?php endforeach; ?>
        </select>
      </label>
      <label><?= e(t('stimmen.zugang')) ?>
        <select name="zugang">
          <option value=""><?= e(t('stimmen.alle_zugaenge')) ?></option>
          <?php foreach (stimmen_zugaenge() as $zugang): ?><option value="<?= e($zugang) ?>"<?= ($filter['zugang'] ?? '') === $zugang ? ' selected' : '' ?>><?= e(t('stimmen.zugang.' . $zugang)) ?></option><?php endforeach; ?>
        </select>
      </label>
      <button type="submit"><?= e(t('stimmen.anwenden')) ?></button>
      <?php if ($filter): ?><a class="stimmen-zuruecksetzen" href="<?= e(url('stimmen')) ?>"><?= e(t('stimmen.zuruecksetzen')) ?></a><?php endif; ?>
    </form>
    <p class="stimmen-treffer" role="status"><?= e(t('stimmen.treffer', ['n' => $gezeigt, 'gesamt' => count(stimmen())])) ?></p>
    <?php if ($jahre === []): ?><p class="disk-leer"><?= e(t('stimmen.leer')) ?></p><?php endif; ?>

    <div class="disk-jahre">
      <?php foreach ($jahre as $jahr => $quellen):
        $jahr = (string) $jahr;
        $weitere = array_values(array_filter($quellen, fn($q) => !stimme_mit_seite($q))); ?>
        <section class="disk-jahr stimmen-jahr" id="<?= $anker($jahr) ?>" aria-labelledby="titel-<?= $anker($jahr) ?>">
          <h2 id="titel-<?= $anker($jahr) ?>"><?= e($jahrlabel($jahr)) ?></h2>
          <?php foreach ($quellen as $q): if (!stimme_mit_seite($q)) continue; [$kurz, $kurzSprache] = stimme_text($q['kurz']); ?>
            <article class="stimme stimme--<?= e($q['stufe']) ?>" id="<?= e($q['id']) ?>">
              <p class="stimme-meta"><?php if ($q['stufe'] === 'auswahl'): ?><span class="stimme-ausgewaehlt"><?= e(t('stimmen.ausgewaehlt')) ?></span> · <?php endif; ?><?= e($meta($q)) ?></p>
              <h3 lang="<?= e(stimme_titelsprache($q)) ?>"><a href="<?= e(stimme_link($q['id'])) ?>"><?= e(stimme_feld($q, 'titel')) ?></a></h3>
              <p class="stimme-kurz"<?= $kurzSprache !== sprache() ? ' lang="de"' : '' ?>><?= md_inline($kurz) ?></p>
              <p class="stimme-merkmale"><span><?= e(stimme_sprache($q['sprache'])) ?></span><span class="stimme-zugang stimme-zugang--<?= e($q['zugang']) ?>"><?= e(t('stimmen.zugang.' . $q['zugang'])) ?></span></p>
            </article>
          <?php endforeach; ?>
          <?php if ($weitere): ?>
            <details class="stimmen-weitere">
              <summary><?= e(t('stimmen.weitere', ['n' => count($weitere)])) ?></summary>
              <ul>
                <?php foreach ($weitere as $q): ?>
                  <li id="<?= e($q['id']) ?>">
                    <p class="stimme-meta"><?= e($meta($q)) ?> · <?= e(t('stimmen.zugang.' . $q['zugang'])) ?></p>
                    <a lang="<?= e(stimme_titelsprache($q)) ?>" href="<?= e(stimme_ziel($q)) ?>"<?= str_starts_with(stimme_ziel($q), 'http') ? ' target="_blank" rel="noopener noreferrer"' : '' ?>><?= e(stimme_feld($q, 'titel')) ?></a>
                  </li>
                <?php endforeach; ?>
              </ul>
            </details>
          <?php endif; ?>
        </section>
      <?php endforeach; ?>
    </div>
  </main>
</div>
