# Maintenance tools

The website runs exclusively as a Go process. These tools work with language-neutral JSON catalogues in `data/` and the retained sources in `research/` and `autobiografie/`. No tool starts a legacy application process or reads a local credentials file.

## Generate and validate content

```sh
python3 werkzeug/quellen.py --check       # offline: reproduce the complete catalogue in memory
python3 werkzeug/inhalte.py              # integrity, translations, references and local media
python3 werkzeug/zitate.py               # compare timeline quotations verbatim with archived texts
python3 werkzeug/quellen.py              # atomically rewrite the validated source catalogue
```

`quellen.py` preserves the existing publication rules: explicit editorial tiers, selected sources, private/internal exclusions, removal of working-file references, summaries, verbatim evidence, corrections and discography-release mappings. English versions are published only when their checksum matches. `--check` writes nothing and cannot be combined with a network update. The unchanged output currently comprises 741 public and 25 excluded sources, with no stale translations.

`inhalte.py` checks publication boundaries, unique IDs, source and release references, DE/EN fields, album offers and media providers, song/video mappings, embedding-check metadata, local previews, homepage excerpts and the listening selection. Go tests, HTTP contract checks and browser workflows verify presentation, routing, filters, sessions, SEO and release behaviour.

## Explicit network and image updates

```sh
python3 werkzeug/quellen.py --lizenzen    # National Library: update licence/access metadata
python3 werkzeug/quellen-scans.py        # NB IIIF manifests and verified page references
python3 werkzeug/quellen-auszuege.py      # local image excerpts + public catalogue
python3 werkzeug/livevideos.py           # YouTube embedding checks + missing local previews
python3 werkzeug/livevideos.py --vorschau # regenerate all local video previews
```

Source/catalogue checks require only the Python standard library. `quellen-scans.py` also uses `curl`. Both image generators need Pillow; `livevideos.py` loads Pillow only when it actually needs to write an image.

The video updater uses only `JACKIE_YOUTUBE_API_KEY` from its process environment. With a key, the Data API checks embedding permission, public visibility, age restrictions and availability in Germany. Without a key, it uses oEmbed, which does not cover country or age restrictions. Previews remain local 480×270 WebP images. These requests belong to an explicitly started maintenance run and never occur during a page request. Tests replace all network transports with local responses.

## Regressions

```sh
python3 -B -m unittest discover -s werkzeug -p 'test_*.py'
python3 werkzeug/cleanup.py
node werkzeug/browserablaeufe.cjs
go test -race ./...
go vet ./...
```

The new tool tests compare the entire generated source catalogue with the existing `data/quellen.json`, check publication filters and stale translations, and verify video eligibility, API batching, oEmbed errors, preview selection and image dimensions without network access. The cleanup test uses temporary Go sessions and counters, including active locks, symlinks and unrelated files.

The old interpreter-specific runtime, router and package checks were removed. The current checks are the Go tests, `ops/prepare-go-release.py` and HTTP/browser checks. The literary analysis tools `messen.py`, `pruefen.py` and `uebersetzung.py` remain available unchanged.

The frozen migration comparison and its documented normalisations are described in [parity.md](parity.md). It can use stored response contracts without a running reference. The additional historical contact comparison needs only an explicitly isolated external HTTP reference; this repository neither installs nor starts its legacy process.
