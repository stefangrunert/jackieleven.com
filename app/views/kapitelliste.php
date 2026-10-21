<ol class="kapitel-liste">
  <?php foreach (kapitelliste() as $i => $k): ?>
    <li>
      <a href="<?= e(url('kapitel', ['slug' => $k['slug']])) ?>">
        <span class="nr"><?= $i + 1 ?></span>
        <span class="titel" lang="en"><?= e($k['titel']) ?></span>
      </a>
    </li>
  <?php endforeach; ?>
</ol>
