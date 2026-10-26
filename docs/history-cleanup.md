# Photo removal from Git history

Eleven original photographs, stored at 22 paths under `assets/bilder/` and
`sketches/assets/`, were removed from the repository history before publication.
The generated illustrations and research material were retained. Historical
source trees otherwise remain unchanged; commit dates and parent relationships
are preserved, but commit IDs changed. This cleanup is separate from the PHP-to-Go
migration and does not change its chronology.

The static sketches now show a placeholder where an original photograph was
removed. The production release manifest did not include these photographs.

The pinned website snapshot used by the search exporter and its corpus tests
changed from `a1ea02707d3cc4fa9f3ef4b0a2f71bd9c9a538e9` to `11947ff9ed768bdd525defbc1807d6ebb1f88266`.
Its text and catalogue files are byte-for-byte identical. The archive snapshot
belongs to a separate repository and is unchanged. Existing search exports may
still record the original website revision as provenance.

Older clones contain the original history. Use a fresh clone after the rewrite;
merging or pushing branches from an older clone can restore the removed files.
