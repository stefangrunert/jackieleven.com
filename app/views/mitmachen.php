<main class="text-seite mitmachen">
  <p class="lead"><?= e(t('mit.intro')) ?></p>
  <p><?= e(t('mit.mitarbeit')) ?></p>
  <p><?= e(t('mit.absprache')) ?></p>
  <p><?= e(t('mit.mail')) ?> <a href="mailto:stefan@jackieleven.com">stefan@jackieleven.com</a>.<br><?= e(t('mit.fotos')) ?></p>

  <section id="nachricht" class="kontakt" aria-labelledby="kontakt-titel">
    <h2 id="kontakt-titel"><?= e(t('mit.formular')) ?></h2>
    <?php if ($erfolg): ?>
      <p class="kontakt-erfolg" role="status"><?= e(t('mit.erfolg')) ?></p>
    <?php endif; ?>
    <?php if ($global || !$bereit): ?>
      <p class="kontakt-fehler" role="alert"><?= e(t('mit.fehler.' . ($global ?? 'konfiguration'))) ?></p>
    <?php endif; ?>
    <form action="<?= e(url('mitmachen')) ?>#nachricht" method="post" class="kontakt-formular">
      <input type="hidden" name="token" value="<?= e($token) ?>">
      <div class="kontakt-fang" aria-hidden="true" inert>
        <label for="kontakt-website">Website</label>
        <input id="kontakt-website" type="text" name="website" tabindex="-1" autocomplete="off">
      </div>
      <?php foreach (['name', 'email', 'nachricht'] as $feld): ?>
        <div class="kontakt-feld">
          <label for="kontakt-<?= e($feld) ?>"><?= e(t('mit.' . $feld)) ?><?php if ($feld === 'name'): ?> <small>(<?= e(t('mit.optional')) ?>)</small><?php endif; ?></label>
          <?php $aria = isset($fehler[$feld]) ? ' aria-invalid="true" aria-describedby="fehler-' . $feld . '"' : ''; ?>
          <?php if ($feld === 'nachricht'): ?>
            <textarea id="kontakt-nachricht" name="nachricht" rows="9" maxlength="10000" required<?= $aria ?>><?= e($felder[$feld]) ?></textarea>
          <?php else: ?>
            <input id="kontakt-<?= e($feld) ?>" type="<?= $feld === 'email' ? 'email' : 'text' ?>" name="<?= e($feld) ?>" autocomplete="<?= e($feld) ?>" maxlength="<?= $feld === 'email' ? '254' : '120' ?>" value="<?= e($felder[$feld]) ?>"<?= $feld === 'email' ? ' required' : '' ?><?= $aria ?>>
          <?php endif; ?>
          <?php if (isset($fehler[$feld])): ?><p class="kontakt-fehler" id="fehler-<?= e($feld) ?>"><?= e(t('mit.fehler.' . $fehler[$feld])) ?></p><?php endif; ?>
        </div>
      <?php endforeach; ?>
      <p class="kontakt-hinweis"><?= e(t('mit.datenschutz')) ?></p>
      <?php if ($turnstile_sitekey !== ''): ?>
        <div class="cf-turnstile" data-sitekey="<?= e($turnstile_sitekey) ?>" data-action="contact" data-theme="dark" data-size="flexible" data-language="<?= e(sprache()) ?>" data-refresh-expired="auto" data-refresh-timeout="auto"></div>
        <p class="kontakt-hinweis"><?= e(t('mit.turnstile')) ?> <a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noopener noreferrer"><?= e(t('mit.turnstile.datenschutz')) ?></a></p>
        <noscript><p class="kontakt-fehler"><?= e(t('mit.turnstile.noscript')) ?></p></noscript>
      <?php endif; ?>
      <button type="submit"<?= !$bereit ? ' disabled' : '' ?>><?= e(t('mit.senden')) ?></button>
    </form>
  </section>
</main>
<?php if ($turnstile_sitekey !== ''): ?>
<script src="/assets/js/kontakt.js?v=<?= filemtime(PUBLIC_ROOT . '/assets/js/kontakt.js') ?>" defer></script>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" defer></script>
<?php endif; ?>
