<?php
declare(strict_types=1);

// Vergleich im bestehenden Layout; die regulären Stationsbilder bleiben unverändert.
require dirname(__DIR__) . '/app/bootstrap.php';
sprache('de');

$zurueckgenommen = ($_GET['variante'] ?? '') === 'zurueckgenommen';
$datei = $zurueckgenommen ? '02-zurueckgenommen.png' : '01-praesent.png';
$bild = '/assets/grafik-entwuerfe/doll-by-doll-zeit/runde-03/' . $datei;
$aktiv = stations_index('1977-doll-by-doll');
$inhalt = render('zeitreise', ['aktiv' => $aktiv]);
$inhalt = str_replace('/assets/bilder/' . stationen()[$aktiv]['bild'], $bild, $inhalt);
$inhalt = preg_replace(
    '~<span class="bildtext">.*?</span>~s',
    '<span class="bildtext">Doll by Doll · Tusche auf Anthrazit</span>',
    $inhalt,
    1
);

ob_start();
?>
<style>
  .portrait-comparison {
    display: flex; align-items: center; justify-content: center;
    flex-wrap: wrap; gap: .65rem 1.4rem;
    padding: .75rem 1rem;
    border-bottom: 1px solid var(--line);
    font-family: var(--rough); font-size: 12px;
  }
  .portrait-comparison > span {
    color: var(--ink-dim); font-size: 10px;
    letter-spacing: .15em; text-transform: uppercase;
  }
  .portrait-comparison .choices { display: flex; gap: .4rem; }
  .portrait-comparison a {
    display: inline-block; padding: .35rem .85rem;
    color: var(--ink-soft); text-decoration: none;
    border: 1px solid var(--line); border-radius: 2px;
  }
  .portrait-comparison a[aria-current="true"] {
    color: var(--accent); border-color: var(--accent);
    background: rgba(212,162,78,.06);
  }
  .portrait-comparison a:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  .stage { min-height: 77vh; }
  .stage-visual img {
    object-fit: cover; object-position: 58% 25%;
    filter: none;
    -webkit-mask-image: linear-gradient(to bottom, transparent, black 3%, black 83%, transparent 100%);
    mask-image: linear-gradient(to bottom, transparent, black 3%, black 83%, transparent 100%);
  }
  .stage-visual::after {
    background: linear-gradient(to right, var(--bg), transparent 8%, transparent 76%, var(--bg));
  }
  @media (max-width: 860px) {
    .stage-visual { min-height: 70vh; }
    .stage-visual::after {
      background: linear-gradient(to bottom, transparent 75%, var(--bg));
    }
  }
</style>
<nav class="portrait-comparison" aria-label="Porträtvergleich">
  <span>Bildprobe · Doll by Doll</span>
  <div class="choices">
    <a href="?variante=praesent"<?= !$zurueckgenommen ? ' aria-current="true"' : '' ?>>A · Präsent</a>
    <a href="?variante=zurueckgenommen"<?= $zurueckgenommen ? ' aria-current="true"' : '' ?>>B · Zurückgenommen</a>
  </div>
</nav>
<?= $inhalt ?>
<?php
$vergleich = ob_get_clean();
seite($vergleich, 'Bildprobe · Dunkle Porträts · Jackie Leven', 'zeitreise', 200, true);
