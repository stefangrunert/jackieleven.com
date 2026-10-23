<?php
/** @var array $filter aus stimmen_filter() */
$filter = array_replace(['auswahl' => '1'], $filter);
$auswahl = (int) $filter['auswahl'];
$alleJahre = stimmen_jahre();
$jahre = stimmen_jahre($filter);
$gezeigt = array_sum(array_map('count', $jahre));
$jahrlabel = fn(string $jahr) => $jahr === '' ? t('stimmen.undatiert') : $jahr;
$anker = fn(string $jahr) => 'jahr-' . ($jahr === '' ? 'undatiert' : $jahr);
$meta = fn(array $q) => implode(' · ', [stimme_datum($q['datum']), stimme_feld($q, 'medium'), t('stimmen.kategorie.' . $q['kategorie'])]);
?>
<div class="disk-raum stimmen-raum" data-eintrag="<?= e(t('disk.eintrag', ['n' => '{n}'])) ?>" data-eintraege="<?= e(t('disk.eintraege', ['n' => '{n}'])) ?>">
  <nav class="disk-zeitstrahl" aria-label="<?= e(t('stimmen.zeitstrahl')) ?>">
    <div class="disk-zeitfenster">
      <ol class="disk-spur">
        <?php foreach ($alleJahre as $jahr => $quellen): ?>
          <li data-quellen-jahr="<?= $anker((string) $jahr) ?>"<?= !isset($jahre[$jahr]) ? ' hidden' : '' ?>>
            <a class="g-marker disk-marker" href="#<?= $anker((string) $jahr) ?>" data-art="werk">
              <span class="dot" aria-hidden="true"></span>
              <span class="g-label"><span class="g-year"><?= e($jahrlabel((string) $jahr)) ?></span><span class="g-era"><?= e(t(count($jahre[$jahr] ?? []) === 1 ? 'disk.eintrag' : 'disk.eintraege', ['n' => count($jahre[$jahr] ?? [])])) ?></span></span>
            </a>
          </li>
        <?php endforeach; ?>
      </ol>
    </div>
  </nav>

  <main class="disk-katalog stimmen" id="stimmen">
    <header class="disk-kopf">
      <p class="disk-intro"><?= e(t('stimmen.intro')) ?></p>
    </header>

    <form class="stimmen-filter" method="get" action="<?= e(url('stimmen')) ?>">
      <div class="stimmen-auswahl">
        <label for="quellen-auswahl"><?= e(t('stimmen.auswahl_label')) ?></label>
        <input id="quellen-auswahl" type="range" name="auswahl" min="0" max="2" step="1" value="<?= $auswahl ?>" aria-valuetext="<?= e(t('stimmen.auswahl_' . $auswahl)) ?>" aria-describedby="quellen-auswahl-stufen">
        <div class="stimmen-auswahl-stufen" id="quellen-auswahl-stufen">
          <?php for ($stufe = 2; $stufe >= 0; $stufe--): ?><span data-auswahl-stufe="<?= $stufe ?>"<?= $auswahl === $stufe ? ' class="aktiv"' : '' ?>><?= e(t('stimmen.auswahl_' . $stufe)) ?></span><?php endfor; ?>
        </div>
      </div>
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
    </form>
    <div class="stimmen-ergebnis">
      <p class="stimmen-treffer" role="status" data-vorlage="<?= e(t('stimmen.treffer', ['n' => '{n}', 'gesamt' => count(stimmen())])) ?>"><?= e(t('stimmen.treffer', ['n' => $gezeigt, 'gesamt' => count(stimmen())])) ?></p>
      <a class="stimmen-zuruecksetzen"<?= $filter === ['auswahl' => '0'] ? ' hidden' : '' ?> href="<?= e(url('stimmen') . '?auswahl=0') ?>"><?= e(t('stimmen.zuruecksetzen')) ?></a>
    </div>
    <p class="disk-leer"<?= $jahre !== [] ? ' hidden' : '' ?>><?= e(t('stimmen.leer')) ?></p>

    <div class="disk-jahre">
      <?php foreach ($alleJahre as $jahr => $quellen):
        $jahr = (string) $jahr;
        $weitere = array_values(array_filter($quellen, fn($q) => !stimme_mit_seite($q)));
        $weitereAnzahl = count(array_filter($weitere, fn($q) => stimme_passt($q, $filter))); ?>
        <section class="disk-jahr stimmen-jahr" id="<?= $anker($jahr) ?>" aria-labelledby="titel-<?= $anker($jahr) ?>"<?= !isset($jahre[$jahr]) ? ' hidden' : '' ?>>
          <h2 id="titel-<?= $anker($jahr) ?>"><?= e($jahrlabel($jahr)) ?></h2>
          <?php foreach ($quellen as $q): if (!stimme_mit_seite($q)) continue; [$kurz, $kurzSprache] = stimme_text($q['kurz']); ?>
            <article class="stimme stimme--<?= e($q['stufe']) ?>" id="<?= e($q['id']) ?>" data-quellen-gewicht="<?= stimme_gewicht($q) ?>" data-art="<?= e($q['kategorie']) ?>" data-sprache="<?= e($q['sprache'] === 'nn' ? 'no' : $q['sprache']) ?>" data-zugang="<?= e($q['zugang']) ?>"<?= !stimme_passt($q, $filter) ? ' hidden' : '' ?>>
              <p class="stimme-meta"><?php if ($q['stufe'] === 'auswahl'): ?><span class="stimme-ausgewaehlt"><?= e(t('stimmen.ausgewaehlt')) ?></span> · <?php endif; ?><?= e($meta($q)) ?></p>
              <h3 lang="<?= e(stimme_titelsprache($q)) ?>"><a href="<?= e(stimme_link($q['id'])) ?>"><?= e(stimme_feld($q, 'titel')) ?></a></h3>
              <p class="stimme-kurz"<?= $kurzSprache !== sprache() ? ' lang="de"' : '' ?>><?= md_inline($kurz) ?></p>
              <p class="stimme-merkmale"><span><?= e(stimme_sprache($q['sprache'])) ?></span><span class="stimme-zugang stimme-zugang--<?= e($q['zugang']) ?>"><?= e(t('stimmen.zugang.' . $q['zugang'])) ?></span></p>
            </article>
          <?php endforeach; ?>
          <?php if ($weitere): ?>
            <details class="stimmen-weitere"<?= $weitereAnzahl === 0 ? ' hidden' : '' ?>>
              <summary data-vorlage="<?= e(t('stimmen.weitere', ['n' => '{n}'])) ?>"><?= e(t('stimmen.weitere', ['n' => $weitereAnzahl])) ?></summary>
              <ul>
                <?php foreach ($weitere as $q): ?>
                  <li id="<?= e($q['id']) ?>" data-quellen-gewicht="<?= stimme_gewicht($q) ?>" data-art="<?= e($q['kategorie']) ?>" data-sprache="<?= e($q['sprache'] === 'nn' ? 'no' : $q['sprache']) ?>" data-zugang="<?= e($q['zugang']) ?>"<?= !stimme_passt($q, $filter) ? ' hidden' : '' ?>>
                    <p class="stimme-meta"><?= e($meta($q)) ?> · <?= e(t('stimmen.zugang.' . $q['zugang'])) ?></p>
                    <a lang="<?= e(stimme_titelsprache($q)) ?>" href="<?= e(stimme_ziel($q)) ?>"<?= str_starts_with(stimme_ziel($q), 'http') ? ' target="_blank" rel="noopener noreferrer"' : '' ?>><?= e(stimme_feld($q, 'titel')) ?></a>
                    <?php if ($q['scan']['pages'] !== ''): ?><p class="stimme-merkmale"><?= e(t('stimmen.seite') . ' ' . $q['scan']['pages']) ?></p><?php endif; ?>
                    <?php require __DIR__ . '/quellen-faksimile.php'; ?>
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
