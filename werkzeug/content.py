"""Shared, dependency-free readers for the neutral content catalogues."""
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {'john-st-field': 'John St. Field', 'doll-by-doll': 'Doll by Doll',
    'jackie-leven': 'Jackie Leven', 'sir-vincent-lone': 'Sir Vincent Lone',
    'jackie-balfour': 'Jackie Balfour', 'concrete-bulletproof-invisible': 'Concrete Bulletproof Invisible',
    'haunted-valley': 'Haunted Valley', 'collaborations': 'Kooperationen'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value, indent=4):
    """Replace one catalogue atomically; leave the previous file on failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=indent)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def source_path(directory, relative):
    """Catalogue paths may only refer to files inside the source directory."""
    directory = Path(directory).resolve()
    candidate = (directory / relative).resolve()
    if not candidate.is_relative_to(directory):
        raise ValueError(f'Source path escapes its directory: {relative}')
    return candidate


def identity(text):
    text = text.translate(str.maketrans({'ø': 'o', 'Ø': 'O', 'æ': 'ae', 'Æ': 'AE', 'ß': 'ss', 'ð': 'd', 'Ð': 'D', 'þ': 'th', 'Þ': 'Th'}))
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub('[^a-z0-9]', '', text)


SONG_ALIASES = {
 'shadowinmyeye':'shadowinmyeyes', 'thebarsofdundee':'barsofdundee', 'levenlament':'levenslament',
 'standinginanothermansrain':'anothermansrain', 'theworkingmanslovesong':'workingmanslovesong',
 'isawmylovewalkintotheclouds':'isawmylovewalkintoclouds', 'oliverblues':'olivierblues',
 'humanface':'thehumanface', 'palaceoflove':'thepalaceoflove',
 'boxershitharderwhenwomanarearound':'boxershitharderwhenwomenarearound', 'balladofanneredmond':'theballadofanneredmond',
 'kingsofinfinitespaceplusstoryofbasilandronnie':'kingsofinfinitespace', 'loversatthegunclubplusstoryofshannondoyle':'loversatthegunclub',
 'stingsdeadstoryofthesaddeathofthewellknownsinger':'stingsdead', 'sextouriststory':'sextourist',
 'whenamandieswithjoshaw':'whenamandies', 'poortounlosingmyvoice':'poortoun',
 'jackiesbaddepressionafunnystory':'jackiesbaddepression', 'jackietalksaboutkielandhismother':'kielandhismother',
 'jackietalksaboutnorwegianprisoners':'norwegianprisoners',
}


def song_key(title):
    title = re.sub(r'^\s*\(spoken\)\s*', '', title, flags=re.I)
    title = re.sub(r'\s*[\[(](?:live|edit|radio|remaster|bonus track|full version|beautiful version|from live show|etc\.)[^\])]*[\])]', '', title, flags=re.I)
    title = re.sub(r'\s*[-–—]\s*(?:live|radio edit|edit|remaster).*$', '', title, flags=re.I)
    key = identity(title)
    return SONG_ALIASES.get(key, key)
