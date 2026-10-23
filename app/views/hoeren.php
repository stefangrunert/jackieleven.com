<?php
$kapitel = require APP_ROOT . '/data/hoeren.php';
$nummer = 0;
?>
<main class="hoer-seite">
  <h1 class="hoer-seitentitel"><?= e(t('nav.hoeren')) ?></h1>
  <p class="hoer-intro"><?= e(t('hoeren.intro_anfang')) ?> <a href="<?= e(url('diskografie')) ?>"><?= e(t('nav.diskografie')) ?></a><?= e(t('hoeren.intro_ende')) ?></p>

  <?php foreach ($kapitel as $kapitelIndex => $gruppe): ?>
    <section class="hoer-kapitel" aria-labelledby="hoer-kapitel-<?= $kapitelIndex + 1 ?>">
      <header class="hoer-kapitelkopf">
        <span><?= str_pad((string) ($kapitelIndex + 1), 2, '0', STR_PAD_LEFT) ?></span>
        <h2 id="hoer-kapitel-<?= $kapitelIndex + 1 ?>"><?= e($gruppe['titel'][sprache()]) ?></h2>
      </header>
      <div class="hoer-stuecke">
        <?php foreach ($gruppe['stuecke'] as $stueck):
          $nummer++;
          $platte = diskografie()['releases'][diskografie_index($stueck['release'])];
          $video = diskografie_youtube($stueck['song']);
          $videoId = $video ? youtube_video_id($video['url']) : '';
        ?>
          <article class="hoer-stueck" id="<?= e(diskografie_liedschluessel($stueck['song'])) ?>">
            <div class="hoer-stuecktext">
              <p class="hoer-laufnummer"><?= str_pad((string) $nummer, 2, '0', STR_PAD_LEFT) ?> <span>· <?= e((string) $platte['year']) ?></span></p>
              <h3 lang="en"><?= e($stueck['song']) ?></h3>
              <p class="hoer-ausgabe"><?= e(t('hoeren.aus')) ?> <a href="<?= e(diskografie_link($platte['id'])) ?>"><span lang="en"><?= e($platte['title']) ?></span></a> · <?= e($platte['artist']) ?></p>
            </div>
            <?php if ($video && $videoId !== ''): ?>
              <div class="hoer-video" data-youtube-id="<?= e($videoId) ?>" data-youtube-title="<?= e($video['title']) ?>">
                <button class="hoer-video-laden" type="button" aria-label="<?= e(t('hoeren.video_laden_titel', ['titel' => $stueck['song']])) ?>">
                  <?php if (!empty($platte['cover'])): ?><img class="hoer-video-bild" src="<?= e($platte['cover']) ?>" alt="" width="600" height="600" loading="lazy" decoding="async" referrerpolicy="no-referrer"><?php endif; ?>
                  <span class="hoer-video-nummer" aria-hidden="true"><?= str_pad((string) $nummer, 2, '0', STR_PAD_LEFT) ?></span>
                  <span class="hoer-play" aria-hidden="true"></span>
                  <span class="hoer-video-text"><?= e(t('hoeren.video_laden')) ?><small><?= e($video['channel']) ?></small></span>
                </button>
                <a class="hoer-youtube-link" href="<?= e($video['url']) ?>" target="_blank" rel="noopener noreferrer" data-music-link><?= e(t('hoeren.youtube')) ?></a>
                <noscript><p><a href="<?= e($video['url']) ?>" target="_blank" rel="noopener noreferrer"><?= e(t('hoeren.youtube')) ?></a></p></noscript>
              </div>
            <?php endif; ?>
          </article>
        <?php endforeach; ?>
      </div>
    </section>
  <?php endforeach; ?>
</main>
