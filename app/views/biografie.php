<?php $alle = stationen(); ?>
<article class="text-seite">
  <p class="kicker">Biografie</p>
  <h1>Jackie Leven, 1950–2011</h1>

  <p class="lead">Geboren als Alan Moffatt am 18. Juni 1950 in Kirkcaldy, Fife. Gestorben am
  14. November 2011 in Hampshire. Dazwischen: eine Band, die zu früh kam, ein Überfall, der ihm
  die Stimme nahm, zwölf Jahre Stille und siebzehn Jahre, in denen er mehr Platten machte, als
  seine Plattenfirma für vernünftig hielt.</p>

  <p>Die ausführliche Fassung entsteht noch. Bis dahin führt die
  <a href="/zeitreise">Zeitreise</a> durch die Stationen, jede mit dem, was er selbst dazu
  geschrieben hat.</p>

  <ol class="stationen-liste">
    <?php foreach ($alle as $s): ?>
      <li>
        <a href="/station/<?= e($s['slug']) ?>">
          <span class="jahr"><?= e($s['jahr']) ?></span>
          <span class="was"><?= e($s['titel']) ?></span>
          <span class="wo"><?= e($s['label']) ?></span>
        </a>
      </li>
    <?php endforeach; ?>
  </ol>
</article>
