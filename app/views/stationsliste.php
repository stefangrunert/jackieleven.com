<ol class="stationen-liste">
  <?php foreach (stationen() as $s): ?>
    <li>
      <a href="<?= e(url('station', ['slug' => $s['slug']])) ?>">
        <span class="jahr"><?= e($s['jahr']) ?></span>
        <span class="was"><?= sfeld_html($s, 'titel') ?></span>
        <span class="wo"><?= sfeld_html($s, 'label') ?></span>
      </a>
    </li>
  <?php endforeach; ?>
</ol>
