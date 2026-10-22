<?php
declare(strict_types=1);

/** Kuratierter Katalog; Quellen und Ausgaben sind pro Eintrag dokumentiert. */
function diskografie(): array
{
    static $daten = null;
    return $daten ??= json_decode(file_get_contents(APP_ROOT . '/data/diskografie.json'), true, flags: JSON_THROW_ON_ERROR);
}

function diskografie_jahre(): array
{
    $jahre = [];
    foreach (diskografie()['releases'] as $platte) {
        $jahre[$platte['year']][] = $platte;
    }
    return $jahre;
}

function diskografie_projekte(): array
{
    return [
        'john-st-field' => 'John St. Field',
        'doll-by-doll' => 'Doll by Doll',
        'jackie-leven' => 'Jackie Leven',
        'sir-vincent-lone' => 'Sir Vincent Lone',
        'jackie-balfour' => 'Jackie Balfour',
        'concrete-bulletproof-invisible' => 'Concrete Bulletproof Invisible',
        'haunted-valley' => 'Haunted Valley',
        'collaborations' => t('disk.kooperationen'),
    ];
}
