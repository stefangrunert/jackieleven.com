<?php
$start = require APP_ROOT . '/data/startseite.php';
$poolQuelle = kolumnen()[kolumnen_index($start['pool']['slug'])];
$lebenQuelle = kolumnen()[kolumnen_index($start['leben']['slug'])];
$platte = diskografie()['releases'][diskografie_index($start['platte']['id'])];
$erstesVideo = $start['hoeren'][0];
$lebenslinie = [
    ['1950', 'fife', url('station', ['slug' => '1950-kirkcaldy'])],
    ['1973', 'field', diskografie_link('1973-control')],
    ['1977', 'doll', url('station', ['slug' => '1977-doll-by-doll'])],
    ['1994', 'solo', url('station', ['slug' => '1994-mystery-of-love'])],
    ['2011', 'november', url('station', ['slug' => '2011-november'])],
];
?>
<main class="home">
  <section class="home-auftakt" aria-labelledby="home-titel">
    <div class="home-buehne">
      <figure class="home-portraet">
        <img src="/assets/bilder/startseite/portrait-graphic.png" alt="<?= e(t('home.portraet_alt')) ?>" width="1536" height="1024" fetchpriority="high">
      </figure>
      <header class="home-name">
        <h1 id="home-titel">Jackie Leven</h1>
        <p>1950–2011</p>
      </header>
      <figure class="home-vers">
        <blockquote lang="en"><?= nl2br(e($start['vers']), false) ?></blockquote>
        <figcaption lang="en">My Philosophy</figcaption>
      </figure>
    </div>
  </section>

  <section class="home-hoeren" aria-labelledby="home-hoeren-titel">
    <div class="home-hoeren-inner">
      <div class="home-video-raum">
        <div class="home-video" data-youtube-id="<?= e($erstesVideo['video']) ?>" data-youtube-title="<?= e($erstesVideo['kuenstler'] . ': ' . $erstesVideo['titel']) ?>">
          <button class="hoer-video-laden" type="button" aria-label="<?= e(t('hoeren.video_laden_titel', ['titel' => $erstesVideo['titel']])) ?>">
            <img class="hoer-video-bild" src="<?= e($erstesVideo['preview']) ?>" alt="" width="1672" height="941" loading="eager" decoding="async">
            <span class="hoer-play" aria-hidden="true"></span>
            <span class="hoer-video-text"><?= e(t('hoeren.video_laden')) ?><small><?= e($erstesVideo['kuenstler']) ?> · <?= e($erstesVideo['kontext']) ?></small></span>
          </button>
          <a id="home-hoeren-youtube" class="hoer-youtube-link" href="https://www.youtube.com/watch?v=<?= e($erstesVideo['video']) ?>" target="_blank" rel="noopener noreferrer" data-music-link><?= e(t('hoeren.youtube')) ?></a>
        </div>
      </div>
      <nav class="home-playlist" aria-labelledby="home-hoeren-titel">
        <div class="home-playlist-kopf">
          <h2 id="home-hoeren-titel"><?= e(t('nav.hoeren')) ?></h2>
          <a class="home-hoeren-link" href="<?= e(url('hoeren')) ?>"><?= e(t('home.hoeren.mehr')) ?></a>
        </div>
        <ol>
          <?php foreach ($start['hoeren'] as $index => $video): ?>
            <li<?= $video['video'] === '' ? ' class="home-playlist-offen"' : '' ?>>
              <?php if ($video['video'] !== ''): ?>
                <button type="button" data-youtube-id="<?= e($video['video']) ?>" data-youtube-title="<?= e($video['kuenstler'] . ': ' . $video['titel']) ?>" data-youtube-label="<?= e(t('hoeren.video_laden_titel', ['titel' => $video['titel']])) ?>" data-youtube-preview="<?= e($video['preview']) ?>" data-youtube-meta="<?= e($video['kuenstler'] . ' · ' . $video['kontext']) ?>" aria-pressed="<?= $index === 0 ? 'true' : 'false' ?>">
                  <span class="home-playlist-nummer"><?= e(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)) ?></span>
                  <span class="home-playlist-titel" lang="en"><?= e($video['titel']) ?></span>
                  <span class="home-playlist-meta"><?= e($video['kuenstler']) ?> · <?= e($video['kontext']) ?></span>
                </button>
              <?php else: ?>
                <span class="home-playlist-platz" aria-hidden="true"><span class="home-playlist-nummer"><?= e(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)) ?></span><span>—</span></span>
              <?php endif; ?>
            </li>
          <?php endforeach; ?>
        </ol>
      </nav>
    </div>
  </section>

  <div class="home-inhalte">
    <nav class="home-lebenslinie" aria-label="<?= e(t('home.lebenslinie')) ?>">
      <ol>
        <?php foreach ($lebenslinie as [$jahr, $key, $ziel]): ?>
          <li><a href="<?= e($ziel) ?>"><span class="home-jahr"><?= e($jahr) ?></span><span class="home-station"><?= e(t('home.weg.' . $key)) ?></span></a></li>
        <?php endforeach; ?>
      </ol>
    </nav>

    <div class="home-auszuege">
      <article class="home-auszug">
        <span class="home-anfuhrung" aria-hidden="true">“</span>
        <figure>
          <blockquote lang="en" cite="<?= e($poolQuelle['archiv']) ?>"><?= e($start['pool']['zitat']) ?></blockquote>
          <figcaption><a href="<?= e(url('kolumne', ['slug' => $poolQuelle['slug']])) ?>">The Deep Pool · <?= e(kolumnen_datum($poolQuelle)) ?> · <span lang="en"><?= e($start['pool']['titel']) ?></span></a></figcaption>
        </figure>
      </article>
      <article class="home-auszug">
        <span class="home-anfuhrung" aria-hidden="true">“</span>
        <figure>
          <blockquote lang="en" cite="<?= e($lebenQuelle['archiv']) ?>"><?= e($start['leben']['zitat']) ?></blockquote>
          <figcaption><a href="<?= e(url('station', ['slug' => $start['leben']['station']])) ?>"><?= e(t('nav.zeitreise')) ?> · 2011</a></figcaption>
        </figure>
      </article>
      <article class="home-platte">
        <a class="home-cover" href="<?= e(diskografie_link($platte['id'])) ?>" aria-label="<?= e(t('disk.oeffnen', ['titel' => $platte['title']])) ?>">
          <img src="/assets/bilder/startseite/cover-mystery-of-love.png" alt="<?= e(t('disk.cover', ['titel' => $platte['title']])) ?>" width="600" height="600" loading="lazy" decoding="async">
        </a>
        <div>
          <p class="home-plattenjahr"><?= e(t('nav.diskografie')) ?> · <?= e((string) $platte['year']) ?></p>
          <h2 lang="en"><a href="<?= e(diskografie_link($platte['id'])) ?>"><?= e($platte['title']) ?></a></h2>
          <p class="home-liedzeile" lang="en"><?= e($start['platte']['zeile']) ?></p>
        </div>
      </article>
    </div>
  </div>
  <section class="home-mitmachen" aria-labelledby="mitmachen-titel">
    <h2 id="mitmachen-titel"><a href="<?= e(url('mitmachen')) ?>"><?= e(t('mit.titel')) ?></a></h2>
    <p><?= e(t('mit.home')) ?></p>
    <a href="<?= e(url('mitmachen')) ?>"><?= e(t('nav.mitmachen')) ?></a>
  </section>
  <nav class="home-fussnav" aria-label="<?= e(t('nav.label')) ?>">
    <?php foreach (['hoeren', 'diskografie', 'zeitreise', 'biografie', 'pool', 'ueber', 'mitmachen'] as $rubrik): ?>
      <a href="<?= e(url($rubrik)) ?>"><?= e(t('nav.' . $rubrik)) ?></a>
    <?php endforeach; ?>
  </nav>
</main>
