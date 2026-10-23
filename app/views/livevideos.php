<?php
/**
 * @var array $konzerte aus diskografie_livevideos()
 * Vor dem Klick lädt nichts von YouTube: Vorschauen liegen lokal und werden erst
 * beim Scrollen geladen; ab dem vierten Konzert stehen sie eingeklappt.
 */
$sichtbar = 3;
$watch = fn(array $stueck) => 'https://www.youtube.com/watch?v=' . $stueck['video']['id'] . ($stueck['start'] ? '&t=' . $stueck['start'] . 's' : '');
?>
<section class="disk-livevideos" id="live-videos" aria-labelledby="livevideos-titel" data-fehler="<?= e(t('disk.video_fehler')) ?>" data-youtube="<?= e(t('disk.video_youtube')) ?>">
  <h2 id="livevideos-titel"><?= e(t('disk.livevideos')) ?></h2>
  <p class="disk-livevideos-hinweis"><?= e(t('disk.livevideos_hinweis')) ?></p>
  <?php foreach ($konzerte as $i => $konzert): $erstes = $konzert['stuecke'][0]; ?>
    <?php if ($i === $sichtbar): ?><details class="disk-livevideos-mehr"><summary><?= e(t('disk.weitere_konzerte', ['n' => count($konzerte) - $sichtbar])) ?></summary><?php endif; ?>
    <article class="disk-konzert">
      <div class="disk-konzert-player">
        <a class="disk-konzert-vorschau" href="<?= e($watch($erstes)) ?>" target="_blank" rel="noopener noreferrer" data-livevideo="<?= e($erstes['video']['id']) ?>" data-start="<?= (int) $erstes['start'] ?>" aria-label="<?= e(t('disk.video_laden', ['titel' => $erstes['title'], 'ort' => $konzert['title']])) ?>">
          <img src="/assets/bilder/live/<?= e($erstes['video']['id']) ?>.webp" alt="" width="480" height="270" loading="lazy" decoding="async" fetchpriority="low">
          <span class="disk-konzert-play" aria-hidden="true"></span>
        </a>
      </div>
      <div class="disk-konzert-text">
        <h3 lang="en"><?= e($konzert['title']) ?></h3>
        <p class="disk-konzert-meta"><?= e(diskografie_konzertdatum($konzert['date'])) ?> · <?= e(t($konzert['source'] === 'official' ? 'disk.video_offiziell' : 'disk.video_fan')) ?></p>
        <ol class="disk-konzert-stuecke">
          <?php foreach ($konzert['stuecke'] as $stueck): ?>
            <li><a href="<?= e($watch($stueck)) ?>" target="_blank" rel="noopener noreferrer" data-livevideo="<?= e($stueck['video']['id']) ?>" data-start="<?= (int) $stueck['start'] ?>" title="<?= e('YouTube · ' . $stueck['video']['title'] . ' · ' . $stueck['video']['channel']) ?>"><span lang="en"><?= e($stueck['title']) ?></span><span class="disk-konzert-zeit"><?= e($stueck['start'] ? diskografie_zeitmarke($stueck['start']) : $stueck['video']['duration']) ?></span></a></li>
          <?php endforeach; ?>
        </ol>
      </div>
    </article>
  <?php endforeach; ?>
  <?php if (count($konzerte) > $sichtbar): ?></details><?php endif; ?>
  <script src="/assets/js/livevideos.js?v=<?= filemtime(APP_ROOT . '/../assets/js/livevideos.js') ?>" defer></script>
</section>
