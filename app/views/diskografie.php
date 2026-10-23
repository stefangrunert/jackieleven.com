<?php $jahre = diskografie_jahre(); $quellen = diskografie()['sources']; ?>
<div class="disk-raum">
  <nav class="disk-zeitstrahl" aria-label="<?= e(t('disk.zeitstrahl')) ?>">
    <div class="disk-zeitfenster">
      <ol class="disk-spur">
        <?php foreach ($jahre as $jahr => $platten): ?>
          <li data-jahr="<?= $jahr ?>">
            <a class="g-marker disk-marker<?= $jahr === array_key_first($jahre) ? ' active' : '' ?>" href="#jahr-<?= $jahr ?>" data-art="werk"<?= $jahr === array_key_first($jahre) ? ' aria-current="location"' : '' ?>>
              <span class="dot" aria-hidden="true"></span>
              <span class="g-label"><span class="g-year"><?= $jahr ?></span><span class="g-era"><?= e(t(count($platten) === 1 ? 'disk.eintrag' : 'disk.eintraege', ['n' => count($platten)])) ?></span></span>
            </a>
          </li>
        <?php endforeach; ?>
      </ol>
    </div>
  </nav>

  <main class="disk-katalog" id="diskografie">
    <header class="disk-kopf">
      <p class="disk-kicker">John St. Field · Doll by Doll · Jackie Leven</p>
      <h1><?= e(t('nav.diskografie')) ?></h1>
      <p class="disk-intro"><?= e(t('disk.intro')) ?></p>
    </header>

    <form class="disk-auswahl" hidden>
      <label><?= e(t('disk.projekt')) ?>
        <select name="projekt">
          <option value="alle"><?= e(t('disk.alle_projekte')) ?></option>
          <?php foreach (diskografie_projekte() as $key => $name): ?><option value="<?= e($key) ?>"><?= e($name) ?></option><?php endforeach; ?>
        </select>
      </label>
      <label><?= e(t('disk.ausgabe')) ?>
        <select name="format">
          <option value="alle"><?= e(t('disk.alle_formate')) ?></option>
          <option value="alben"><?= e(t('disk.alben')) ?></option>
          <option value="kleine"><?= e(t('disk.singles')) ?></option>
          <option value="reissue"><?= e(t('disk.type.reissue')) ?></option>
          <option value="video"><?= e(t('disk.type.video')) ?></option>
          <option value="unreleased"><?= e(t('disk.type.unreleased')) ?></option>
        </select>
      </label>
      <button type="reset" hidden><?= e(t('disk.zuruecksetzen')) ?></button>
    </form>
    <p class="disk-filterstatus" role="status" aria-live="polite"></p>

    <div class="disk-jahre">
      <?php foreach ($jahre as $jahr => $platten): ?>
        <section class="disk-jahr" id="jahr-<?= $jahr ?>" aria-labelledby="titel-<?= $jahr ?>" data-jahr="<?= $jahr ?>">
          <h2 id="titel-<?= $jahr ?>"><?= $jahr ?></h2>
          <?php foreach ($platten as $platte): ?>
            <article id="<?= e($platte['id']) ?>" class="disk-platte<?= isset($platte['cover']) ? ' disk-mit-cover' : '' ?><?= in_array($platte['kind'], ['single', 'ep'], true) ? ' disk-kleine-ausgabe' : '' ?>"
                     data-projekte="<?= e(implode(' ', $platte['tags'])) ?>" data-format="<?= e($platte['kind']) ?>" aria-labelledby="titel-<?= e($platte['id']) ?>">
              <?php if (isset($platte['cover'])): ?>
                <figure class="disk-cover">
                  <a href="<?= e(diskografie_link($platte['id'])) ?>" data-release-link="<?= e($platte['id']) ?>" aria-label="<?= e(t('disk.oeffnen', ['titel' => $platte['title']])) ?>"><img src="<?= e($platte['cover']) ?>" alt="<?= e(t('disk.cover', ['titel' => $platte['title']])) ?>" width="600" height="600" loading="<?= $platte['id'] === '1973-control' ? 'eager' : 'lazy' ?>" decoding="async" referrerpolicy="no-referrer"></a>
                </figure>
              <?php endif; ?>
              <div class="disk-plattentext">
                <p class="disk-kuenstler"><?= e($platte['artist']) ?></p>
                <h3 id="titel-<?= e($platte['id']) ?>"><a href="<?= e(diskografie_link($platte['id'])) ?>" data-release-link="<?= e($platte['id']) ?>"><?= e($platte['title']) ?></a></h3>
                <p class="disk-metadaten"><?= e(implode(' · ', array_filter([t('disk.type.' . $platte['kind']), $platte['format'], $platte['label']])) ) ?></p>
                <?php if ($platte['notes'][sprache()] !== ''): ?><p class="disk-notiz"><?= e($platte['notes'][sprache()]) ?></p><?php endif; ?>
                <?php if (diskografie_hoerlinks($platte['id']) !== []): ?>
                  <p class="disk-hoeren-kurz"><a href="<?= e(diskografie_link($platte['id'])) ?>#hoeren" data-release-link="<?= e($platte['id']) ?>"><?= e(t('disk.hoeren')) ?></a></p>
                <?php endif; ?>
                <details class="disk-details">
                  <summary><?= e(t('disk.details')) ?></summary>
                  <?php if ($platte['catalog'] !== ''): ?><p><?= e(t('disk.katalognummer')) ?> <?= e($platte['catalog']) ?></p><?php endif; ?>
                  <?php if ($platte['tracks'] !== []): ?><p><?= e(t('disk.weitere_titel')) ?> <?= e(implode(' / ', $platte['tracks'])) ?></p><?php endif; ?>
                  <ul>
                    <?php foreach ($platte['sources'] as $key): ?><li><a href="<?= e($quellen[$key]['url']) ?>" target="_blank" rel="noopener noreferrer"><?= e($quellen[$key]['label']) ?></a></li><?php endforeach; ?>
                    <?php if (isset($platte['coverSource'])): ?><li><a href="<?= e($platte['coverSource']) ?>" target="_blank" rel="noopener noreferrer"><?= e(t('disk.coverquelle')) ?></a></li><?php endif; ?>
                  </ul>
                </details>
              </div>
            </article>
          <?php endforeach; ?>
        </section>
      <?php endforeach; ?>
    </div>
    <p class="disk-leer" hidden><?= e(t('disk.leer')) ?></p>
    <aside class="disk-hinweis">
      <p><?= e(t('disk.hinweis')) ?></p>
      <p><?= e(t('disk.quellenhinweis')) ?></p>
    </aside>
    <a class="disk-nach-oben" href="#diskografie"><?= e(t('disk.nach_oben')) ?> ↑</a>
  </main>
</div>
