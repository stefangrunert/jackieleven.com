<?php
/** @var array $platte @var array $kontext */
$details = diskografie_details($platte['id']);
$hoeren = diskografie_hoerlinks($platte['id']);
if (!diskografie_passt($platte, $kontext)) unset($kontext['projekt'], $kontext['format']);
$platten = array_values(array_filter(diskografie()['releases'], fn($p) => diskografie_passt($p, $kontext)));
$index = array_search($platte['id'], array_column($platten, 'id'), true);
$vor = $platten[$index - 1] ?? null;
$nach = $platten[$index + 1] ?? null;
$navigation = compact('vor', 'nach', 'platte', 'kontext');
$quellen = [];
foreach ($platte['sources'] as $key) $quellen[] = diskografie()['sources'][$key];
foreach ($details['sources'] ?? [] as $quelle) $quellen[] = $quelle;
if (isset($platte['coverSource'])) $quellen[] = ['label' => t('disk.coverquelle'), 'url' => $platte['coverSource']];
$quellen = array_column($quellen, null, 'url');
?>
<div class="disk-raum disk-detailraum" data-release="<?= e($platte['id']) ?>" data-origin="<?= e($kontext['von'] ?? $platte['id']) ?>">
  <nav class="disk-zeitstrahl" aria-label="<?= e(t('disk.zeitstrahl')) ?>">
    <div class="disk-zeitfenster">
      <ol class="disk-spur">
        <?php foreach ($platten as $eintrag): $aktiv = $platte['id'] === $eintrag['id']; ?>
          <li>
            <a class="g-marker disk-marker<?= $aktiv ? ' active' : '' ?>" href="<?= e(diskografie_link($eintrag['id'], $kontext)) ?>" data-art="werk"<?= $aktiv ? ' aria-current="page"' : '' ?>>
              <span class="dot" aria-hidden="true"></span>
              <span class="g-label"><span class="g-year"><?= $eintrag['year'] ?></span><span class="g-era"><?= e($eintrag['title']) ?></span></span>
            </a>
          </li>
        <?php endforeach; ?>
      </ol>
    </div>
  </nav>
  <main class="disk-katalog disk-detail" id="platte">
    <?= render('platte-navigation', $navigation + ['oben' => true]) ?>
    <article>
      <header class="disk-albumkopf<?= isset($platte['cover']) ? ' disk-albumkopf--cover' : '' ?>">
        <?php if (isset($platte['cover'])): ?>
          <figure class="disk-cover">
            <img src="<?= e($platte['cover']) ?>" alt="<?= e(t('disk.cover', ['titel' => $platte['title']])) ?>" width="600" height="600" decoding="async" referrerpolicy="no-referrer">
          </figure>
        <?php endif; ?>
        <div>
          <p class="disk-kuenstler"><?= e($platte['artist']) ?></p>
          <h1><?= e($platte['title']) ?></h1>
          <p class="disk-ausgabenjahr"><?= $platte['year'] ?> <span>· <?= e(t('disk.type.' . $platte['kind'])) ?></span></p>
          <dl class="disk-fakten">
            <?php foreach (['format' => 'disk.format', 'label' => 'disk.label', 'catalog' => 'disk.katalog'] as $key => $titel): ?>
              <?php if ($platte[$key] !== ''): ?><div><dt><?= e(t($titel)) ?></dt><dd><?= e($platte[$key]) ?></dd></div><?php endif; ?>
            <?php endforeach; ?>
          </dl>
        </div>
      </header>

      <?php if (!empty($details['facts'])): ?>
        <dl class="disk-fakten disk-aufnahmefakten">
          <?php foreach ($details['facts'] as $fakt): ?><div><dt><?= e($fakt['label'][sprache()]) ?></dt><dd><?= e($fakt['value'][sprache()]) ?></dd></div><?php endforeach; ?>
        </dl>
      <?php endif; ?>

      <?php if ($hoeren !== []): ?>
        <section class="disk-hoeren" id="hoeren" aria-labelledby="hoeren-titel">
          <h2 id="hoeren-titel"><?= e(t('disk.album_hoeren')) ?></h2>
          <ul>
            <?php foreach ($hoeren['links'] as $link): $anbieter = diskografie_musikdienste()[$link['service']]; $dienst = $anbieter['name']; ?>
              <li><a class="musik-dienst" href="<?= e($link['url']) ?>" target="_blank" rel="noopener noreferrer" data-music-link title="<?= e($anbieter['tooltip']) ?>" aria-label="<?= e(t('disk.hoerlink', ['titel' => $platte['title'], 'dienst' => $dienst])) ?>"><?= render('musik-icon', ['dienst' => $link['service']]) ?></a></li>
            <?php endforeach; ?>
          </ul>
          <?php if (!empty($hoeren['note'][sprache()])): ?><p><?= e($hoeren['note'][sprache()]) ?></p><?php endif; ?>
        </section>
      <?php endif; ?>

      <section class="disk-titelliste" aria-labelledby="titelliste">
        <h2 id="titelliste"><?= e(t('disk.titelliste')) ?></h2>
        <?php if (empty($details['tracklists'])): ?>
          <p class="disk-fehlende-angaben"><?= e(t('disk.titelliste_fehlt')) ?></p>
        <?php else: ?>
          <?php foreach ($details['tracklists'] as $liste): ?>
            <?php if (!empty($liste['label'])): ?><h3><?= e($liste['label'][sprache()]) ?></h3><?php endif; ?>
            <ol class="disk-tracks">
              <?php foreach ($liste['tracks'] as $track): ?>
                <?php $videos = diskografie_youtube_fassungen($track['title']); $video = $videos[0] ?? null; $live = array_slice($videos, 1); ?>
                <li><span class="disk-tracknummer" aria-hidden="true"><?= e($track['number']) ?></span><span class="disk-tracktitel"><?= e($track['title']) ?><?php if (!empty($track['artist'])): ?><small><?= e($track['artist']) ?></small><?php endif; ?><?php if ($live): ?><small class="disk-track-live"><span><?= e(t('disk.live')) ?></span> <?php foreach ($live as $j => $fassung): ?><?= $j ? ' · ' : '' ?><a href="<?= e($fassung['url']) ?>" target="_blank" rel="noopener noreferrer" data-music-link title="<?= e(diskografie_fassung_tooltip($fassung)) ?>" aria-label="<?= e(t('disk.youtube_live', ['titel' => $track['title'], 'ort' => diskografie_fassung_ort($fassung)])) ?>"><?= e(diskografie_fassung_ort($fassung)) ?></a><?php endforeach; ?></small><?php endif; ?></span><?php if ($video): ?><a class="disk-track-youtube" href="<?= e($video['url']) ?>" target="_blank" rel="noopener noreferrer" data-music-link title="<?= e(diskografie_fassung_tooltip($video)) ?>" aria-label="<?= e(t('disk.youtube_lied', ['titel' => $track['title']])) ?>"><?= render('musik-icon', ['dienst' => 'youtube']) ?></a><?php endif; ?><?php if (!empty($track['duration'])): ?><span class="disk-trackdauer"><?= e($track['duration']) ?></span><?php endif; ?></li>
              <?php endforeach; ?>
            </ol>
          <?php endforeach; ?>
        <?php endif; ?>
      </section>

      <?php if (!empty($details['credits'])): ?>
        <section class="disk-beteiligte" aria-labelledby="beteiligte">
          <h2 id="beteiligte"><?= e(t('disk.beteiligte')) ?></h2>
          <dl class="disk-fakten">
            <?php foreach ($details['credits'] as $credit): ?><div><dt><?= e($credit['role'][sprache()]) ?></dt><dd><?= e($credit['name']) ?></dd></div><?php endforeach; ?>
          </dl>
        </section>
      <?php endif; ?>

      <section class="disk-quellen" aria-labelledby="quellen">
        <h2 id="quellen"><?= e(t('disk.quellen')) ?></h2>
        <ul><?php foreach ($quellen as $quelle): ?><li><a href="<?= e($quelle['url']) ?>" rel="noopener noreferrer"><?= e($quelle['label']) ?></a></li><?php endforeach; ?></ul>
      </section>
    </article>
    <?= render('platte-navigation', $navigation + ['oben' => false]) ?>
  </main>
</div>
