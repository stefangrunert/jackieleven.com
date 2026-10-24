#!/usr/bin/env python3
"""Build compact Voices facsimiles from the preserved, annotated source images.

python3 werkzeug/quellen-auszuege.py (requires Pillow)
Crop coordinates and provenance stay in research; only captions, source links and
image dimensions are written to the public catalogue. No enlargement or retouching.
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/faksimiles'
TARGET = ROOT / 'assets/images/voices'


def main():
    manifest = json.loads((SOURCE / 'web-auszuege.json').read_text())
    TARGET.mkdir(parents=True, exist_ok=True)
    catalogue = {}
    for item in manifest:
        with Image.open(SOURCE / 'markiert' / item['input']) as original:
            width, height = original.size
            crop = item.get('crop', [0, 0, 1, 1])
            excerpt = original.crop(tuple(round(v * (width if i % 2 == 0 else height)) for i, v in enumerate(crop))).convert('RGB')
            excerpt.thumbnail((1200, 1800), Image.Resampling.LANCZOS)
            excerpt.save(TARGET / item['file'], 'WEBP', quality=88, method=6)
            catalogue.setdefault(item['id'], []).append({
                'image': '/assets/images/voices/' + item['file'],
                'width': excerpt.width,
                'height': excerpt.height,
                'caption': item['caption'],
                'source': item['source'],
                'url': item['url'],
            })
    (ROOT / 'app/data/quellen-auszuege.json').write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(manifest)} compact facsimiles for {len(catalogue)} sources.')


if __name__ == '__main__':
    main()
