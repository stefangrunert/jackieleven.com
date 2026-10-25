#!/usr/bin/env python3
"""Verify station quotations verbatim against their archived column sources.

Whitespace is normalized; spelling, punctuation, quote marks and case are not.
An optional argument selects another neutral JSON station catalogue.
"""
import argparse
from pathlib import Path
import re
from content import ROOT, read_json, source_path


def norm(text):
    return re.sub(r'\s+', ' ', text).strip()


def verify(stations, root=ROOT):
    errors, checked = [], 0
    for station in stations:
        quote, source = station['zitat'], station['quelle']
        if not quote:
            if source is not None:
                errors.append(station['slug'] + ': Quelle ohne Zitat')
            continue
        filename = (source or {}).get('datei', '')
        path = source_path(Path(root) / 'research/columns', filename)
        if not path.is_file():
            errors.append(station['slug'] + ': Quelldatei fehlt: ' + filename)
            continue
        checked += 1
        if norm(quote) not in norm(path.read_text(encoding='utf-8')):
            errors.append(station['slug'] + ': Zitat steht nicht wortgetreu in ' + filename)
    return checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalogue', nargs='?', type=Path, default=None)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    checked, errors = verify(read_json(args.catalogue or args.root / 'data/stationen.json'), args.root)
    print('\n'.join(errors) if errors else f'Alle {checked} Zitate stehen wortgetreu in ihren Quellen.')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
