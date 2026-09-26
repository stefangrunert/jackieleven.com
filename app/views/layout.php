<?php /** @var string $inhalt @var string $titel @var string $nav */ ?>
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= e($titel) ?></title>
<meta name="description" content="Eine Hommage an den schottischen Songwriter Jackie Leven (1950–2011), erzählt entlang seiner eigenen Texte.">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>

<header class="topbar">
  <a class="name" href="/">Jackie Leven</a>
  <nav>
    <a href="/zeitreise"<?= $nav === 'zeitreise' ? ' class="hier"' : '' ?>>Zeitreise</a>
    <a href="/biografie"<?= $nav === 'biografie' ? ' class="hier"' : '' ?>>Biografie</a>
    <a href="/ueber"<?= $nav === 'ueber' ? ' class="hier"' : '' ?>>Über diese Seite</a>
  </nav>
</header>

<?= $inhalt ?>

<footer>
  <span>1950–2011</span>
  <span>Private Hommage · keine offizielle Seite</span>
</footer>

<script src="/assets/js/zeitgraph.js" defer></script>
</body>
</html>
