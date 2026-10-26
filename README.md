# Jackie Leven

A personal tribute to the Scottish songwriter **Jackie Leven** (18 June 1950, Kirkcaldy – 14 November 2011, Hampshire). An independent project, unaffiliated with the artist's estate or any record label.

The project has three parts: a research archive, an imagined autobiography in his voice, and a website that makes both accessible. The website runs as a standalone Go server.

## Run locally (Go 1.26)

```sh
go run ./cmd/jackieleven -root "$PWD" -listen 127.0.0.1:8080
go test -race ./...
go vet ./...
```

The Go version is available at `http://127.0.0.1:8080/de/`. It uses only the Go standard library. JSON data and Go templates load at startup; Markdown remains the content source. The frozen reference for historical comparisons is retained outside this branch.

- [Migration status and resuming work](docs/go-migration.md)
- [Architecture and design decisions](docs/go-architecture.md)
- [HTTP comparison and normalisation](werkzeug/parity.md)
- [Releases and Linux operations](ops/GO-BETRIEB.md)
- [Separate live test instance at unpubli.sh/jackieleven](ops/GO-PREVIEW.md)

The production Go site runs at <https://jackieleven.com/de/>, including its contact form. The separate test instance remains available at <https://unpubli.sh/jackieleven/de/> with email delivery disabled. The server retains the previous application for rollback.

## The foundation: his own writing

Leven wrote on his own websites from October 2002 until autumn 2011: first the monthly column *The Deep Pool* on jackieleven.com, then blogs and other sections on jackieleven.co.uk from 2008. Both original sites are offline; the host suspended jackieleven.co.uk in 2024.

The Internet Archive made it possible to recover **76 texts, around 90,000 words**: the only place where he writes at length about himself in his own voice. They are preserved verbatim in [`research/columns/`](research/columns/README.md), one file per contribution, with section, date, source URL and archive link in the YAML header.

This corpus provides both the project's **factual basis** and its **stylistic reference**.

## Homepage and timeline

`/de/` and `/en/` are the shared entry points. The homepage follows the supplied “Startseite nachgebaut” design (desktop 1200, tablet 768, phone 390): an illustrated concert portrait with a verse from *My Philosophy*, five milestones and three excerpts introducing the columns, timeline and discography. Original texts remain in English; labels are translated. The text about Ed links to its timeline entry and the album to its release page. The cover is displayed in black and white. The footer identifies the personal, independent tribute without repeating the dates of birth and death.

`data/startseite.json` contains the excerpts and their source mappings; archived original files remain unchanged. The initial T missing from the archived Ed text is restored to match the design. Instrument Serif, Newsreader and Space Grotesk, with their OFL licences, are in `assets/fonts/`; supplied images are in `assets/bilder/startseite/`. The fonts and mobile menu are loaded only on the homepage. All navigation links remain visible without JavaScript; with JavaScript, the small-screen menu opens and closes with Escape. The year strip scrolls horizontally on small screens.

The timeline has its own overview at `/de/zeitreise` and `/en/timeline`. Existing milestone URLs remain valid. The name in the header leads home; the Timeline menu item and biography references lead to the timeline.

## Contributions and contact form

`/de/mitmachen` and `/en/contribute` invite memories, additions and collaboration. The homepage and shared footer link to the invitation. The form sends only to `stefan@jackieleven.com`, using `Jackie Leven · Hommage <jackieleven@unpubli.sh>` as sender and the visitor's address as `reply_to`. It neither publishes submissions nor sends automatic replies. Photographs are initially submitted by email.

Delivery uses the Resend REST API through the Go standard-library HTTP client. Configuration comes exclusively from `JACKIE_RESEND_API_KEY`, `JACKIE_TURNSTILE_SITEKEY` and `JACKIE_TURNSTILE_SECRET` in the process environment. Keys belong neither in the repository nor in browser code. The unpubli.sh test instance deliberately has no delivery credentials.

The form uses session tokens, a hidden honeypot, minimum completion time, a cooldown after successful delivery and a shared, locked limit of five attempts per hour/IP. The counter lives outside the web root in a temporary directory; `JACKIE_CONTACT_STATE_DIR` can specify a dedicated writable private directory. It contains timestamps and daily rotating hashes, not message content. Old counters are removed on the next attempt after two days. Multiple servers must share this store. Errors preserve input; a Resend idempotency key protects identical retries after timeouts. Without keys, the send button stays disabled and the direct email address remains visible.

The Go test instance visibly disables its contact form while provider credentials are absent.

## The Deep Pool on the website

At `/de/deep-pool` and `/en/deep-pool`, reading starts directly with the first column from October 2002. Only that page has a short introduction above the article. A timeline based on the main timeline leads through all texts and highlights the current contribution: vertically on large screens, horizontally on narrow ones. Simple links above and below the text lead to the previous and next contribution and to All texts. The full annual overview is at `/de/deep-pool/archiv` and `/en/deep-pool/archive`. Each reading page shows the English original, date and author; provenance, archive link and expandable notes appear below. No new editorial titles or summaries have been added.

`data/kolumnen.json` defines the published collection: 73 contributions up to and including the November 2011 death announcement. The three later archived contributions from 2012 remain in the research collection but are not displayed on the website. `internal/site/markdown.go` reads original files without modifying them. Known publication months from early archive URLs are used; otherwise later dates are explicitly identified as archive dates. The death announcement is attributed to the website operators. Repeated sidebar images and two navigation remnants in the September 2007 column are omitted from the reading version. Duplicate month and section headings at the beginning of old columns are replaced by the reader header; the prose is unchanged.

## Discography

The **discography** at `/de/diskografie` and `/en/discography` covers 88 entries from 1975 to 2024: John St. Field, Doll by Doll, Concrete Bulletproof Invisible, Jackie Leven, Sir Vincent Lone and Jackie Balfour, plus Haunted Valley, collaborations and later releases. The year timeline follows the reading position; project and release-type filters also update year navigation. Existing entry anchors remain valid; language changes preserve the selection. The entire catalogue remains readable without JavaScript.

Covers and titles open a dedicated release page, such as `/de/diskografie/1999-greek-notebook`. It shows facts, a track list and documented credits, without background essays. Its timeline links to individual releases; previous/next navigation follows the current filters. Returning to the overview preserves filters, expanded sources and reading position, including through the browser Back button. This uses the history entry and browser session storage; detail pages and navigation remain accessible without JavaScript.

`data/diskografie-details.json` adds release-specific facts and sources to the 88 catalogue entries: 85 track lists containing 881 track entries, plus credits for 22 releases. LP sides, multiple CDs and different track orders are represented separately. Complete track lists are unavailable for *The Last Flick of the Golden Wrench*, *The Meeting of Remarkable Men* and *Live from a Cornish Pub in Germany*; their pages say so. Catalogue entries grouping several single variants show separate track lists. Sources include Stuart Briers and Bob Astridge's current discography, specific MusicBrainz releases, and the MIG and Guerssen label catalogues.

`data/diskografie.json` contains releases, bilingual notes, sources and cover URLs. Its basis is `research/05-diskografie.md`, supplemented by label evidence and Jackie's announcements. In particular, *Live from a Cornish Pub in Germany* is documented in his September 2008 text; *Troubadour Heart* was first available directly in 2008 and released regularly in 2009; the 2024 Rockpalast edition includes CD and DVD. Unreleased or unconfirmed projects are explicitly labelled. Covers are embedded from linked label and music catalogues; digital covers do not establish historical release dates.

## Listening links and YouTube song examples

`data/diskografie-hoerlinks.json` lists verified digital album offers with Spotify, Apple Music, Qobuz, Amazon Music and Bandcamp links. The first 14 album offers were supplemented with 15 Qobuz and ten Amazon offers and two Bandcamp releases: *Straight Outta Caledonia* and *The Wanderer – A Tribute*. Qobuz/Amazon mappings use visible artist catalogues; Bandcamp mappings use individual release pages. Links refer to the storefront observed; availability and playback may vary by region.

A total of 44 releases have an album offer. Recent additions include Spotify and Apple Music links for 16 releases, among them *For Peace Comes Dropping Slow*, all four parts of *The Haunted Year*, the three Sir Vincent Lone albums, *Chip Pan Fire*, *Heroes Can Be Any Size*, *Live Or Die* and the Rockpalast recording; *Straight Outta Caledonia* also gained both services. These are based on Apple's catalogue search and Spotify discography pages. *Songs for Lonely Americans* (2004) links to the identically named digital version from 2006; the 2011 and 2024 Rockpalast editions share one digital version. The digital *Live Or Die* has only the 25 songs, excluding the CDs' ten spoken interludes.

*Control* and all five Doll by Doll albums are also linked on Spotify, including their reissues. YouTube examples cover every song title on them; the title variants “Human Face” / “The Human Face” and “Palace of Love” / “The Palace of Love” share mappings.

Album links appear as individual monochrome SVG icons before the track list, with English tooltips and accessible labels. Qobuz also offers downloads; Bandcamp offers downloads and available physical editions. Prices and stock levels are not stored. Historical track lists and release years are preserved. The digital *Gothic Road* contains two extra tracks; Bandcamp lists the tribute album's 22 tracks in a different order.

`data/youtube-titel.json` assigns a list of YouTube recordings to each of 343 song titles: first a listening example (studio preferred, official Topic and label channels before fan uploads), then 135 live versions in total. Mapping follows the song, **not the specific recording**: the same links appear wherever the song occurs, including studio/live versions and reissues. The listening example appears as a YouTube icon in the row; live versions follow chronologically in a small Live line beneath the title, with place and year, for example “Bremen 1999 · Kiel 2003 · Rockpalast 2004”. Official live albums without a documented recording date use their title (“Munich Blues”). Each concert has at most one version. Place names with distinct German forms use bilingual labels (`label` as `{de, en}`).

Sources for live versions include Topic-channel album playlists (*The Haunted Year*, *For Peace Comes Dropping Slow*, *Live Or Die*, *Revenge of Memory*), MIG's official Rockpalast concert film with track timestamps, and fan/TV recordings whose titles or descriptions document place and date. Longer recordings without timestamps remain in the discovery list. Punctuation, Live/Edit suffixes, “(Spoken)”, “(bonus track)”, “(Full Version)”, “(From Live Show)” and a few documented spelling variants are normalised. “Intro” remains unlinked because different introductions share the title. Tooltips name the actual video, album where applicable, and channel. `internal/site/content.go` maps listening examples and live versions to songs. In the current track lists, 813 of 881 track entries across 84 release pages have a listening example, with 876 additional live links.

Research is in `research/youtube-fundliste.md`, structured data in `research/youtube-fundliste.json`, and a locally searchable table in `research/youtube-fundliste.html`. As of 23 October 2026, it contains 785 distinct videos from search results, Topic-channel and album pages, and targeted searches per song: Topic audio, official audio/still-image videos, fan uploads, dated and located concerts, interviews and alias projects. It records which video is used as a listening example or live version, and ends with 46 song titles for which no recording was found. Categories follow visible metadata and video descriptions. Videos used by the app were reachable on the review date; rights have not been verified. The collection does not claim completeness. Unrelated results and mix links have been removed.

No players, external music scripts or automatic platform queries load on a page visit. Services open only on click. A displayed link does not guarantee playback in every country or without an account.

### Live videos on release pages

Below the track list, Live videos shows concert recordings of songs on the release, one card per concert. `data/live-videos.json` stores concerts (title, date at the supported precision, `official` or `fan` provenance, associated releases) with videos, channel, duration and songs with start seconds. The concert's own release lists all tracks; other releases show only shared songs. Clicking a song seeks to its position. Currently only MIG's complete Rockpalast film is official. Fan recordings (ZDF Disco 1981, Cropredy 2004, Manchester 2009, Essen 2010, Glasgow 2011) are recorded but embedded only with `JACKIE_FAN_VIDEOS=1`. Upload availability does not establish a licence; uploaders of fan and TV recordings are rarely the rights holders.

Only videos stored as embeddable by `werkzeug/livevideos.py` (`embeddable`, `checked`) are embedded. With `JACKIE_YOUTUBE_API_KEY`, the tool checks embedding permission, visibility, age restrictions and blocks for Germany through the YouTube Data API; without a key it uses only oEmbed. If YouTube still refuses playback, the card becomes a link. Without JavaScript, all cards and songs are ordinary YouTube links.

Before a click, the page loads nothing from YouTube. The tool stores local previews in `assets/bilder/live/` (480×270 WebP, currently 3–12 KB). They use `loading="lazy"` and load on scrolling; concerts from the fourth onward are collapsed and load only when expanded. `assets/js/livevideos.js` appears only on pages with live videos. YouTube's player API and the player (`youtube-nocookie.com`) load after the first click, with one player per concert.

```sh
python3 werkzeug/livevideos.py            # check embedding permission, create missing previews (network)
python3 werkzeug/livevideos.py --vorschau # regenerate all previews
```

## Voices: external sources

`/de/stimmen` and `/en/voices` present what others have written and said about Jackie: 741 interviews, reviews, profiles, concert reports, obituaries, memories, broadcasts, forum discussions and books from 1971 onwards. The timeline follows the discography pattern, with filters for type, language and access (freely readable, online, web archive, paywall, lost). Sources come from `research/quellen/`, one file per source with an original summary; the concept is in `research/ressourcen-seite-konzept.md`.

`werkzeug/quellen.py` generates `data/quellen.json`. The website publishes header metadata, the project's detailed summaries and verbatim quotations in the original language, including longer quotations. Discovery paths, confidence, contradictions and working-file references remain outside the website output. Sources correcting a common error, such as the release year of *Control*, have a **Correction** section and **Evidence** with original wording and translation. Tiers comprise 34 selected sources (listed in the tool and YAML headers), directory entries with dedicated detail pages, and further sources collapsed by year and linked directly to the original. Sources known only second-hand remain outside the website. A source's YAML `stufe:` field overrides the default rule. Reviews are mapped to releases through album titles and appear there as press coverage.

The National Library of Norway makes some newspaper issues available under CC BY-NC-ND or CC BY-NC. `--lizenzen` retrieves this from `api.nb.no` and stores it in `data/quellen-lizenzen.json`; freely licensed articles are labelled freely readable and include attribution and licence information. English versions are in `data/quellen-en.json`, each with a checksum of the German source text; a change marks the translation stale. English pages never fall back to German, and `werkzeug/inhalte.py` fails if a source with a dedicated page lacks an English version. Selected detail pages show compact facsimile excerpts with source references; red frames are identified as editorial additions. `werkzeug/quellen-auszuege.py` generates local WebP files and `data/quellen-auszuege.json` from retained marked originals and `research/faksimiles/web-auszuege.json`. Previews are limited to 24 rem wide and 26 rem high, load lazily and can be clicked. The overview loads none of these images; the server should use gzip.

```sh
python3 werkzeug/quellen.py              # generate website data from research/quellen/
python3 werkzeug/quellen.py --lizenzen   # also query National Library licences (network)
python3 werkzeug/quellen-auszuege.py     # generate compact facsimile excerpts (Pillow)
python3 werkzeug/inhalte.py             # validate catalogues and translations
```

## Directories

| Path | Contents |
|---|---|
| [`research/`](research/README.md) | Biographical compendium: twelve dossiers with footnotes, a timeline with conflicting dates, concert calendar (470 appearances), website history, and `columns/` as a primary source |
| [`autobiografie/`](autobiografie/00-rahmen.md) | The pastiche: 15 chapters in Leven's voice, **not written by him**. Also the framework, chapter plan and language document; translations in `autobiografie/<language>/` |
| `werkzeug/` | `messen.py` measures chapters against the corpus, `pruefen.py` flags AI sentence patterns, `zitate.py` checks website quotations against sources, and `uebersetzung.py` compares pastiche translations with the original |
| `cmd/`, `internal/site/` | Go server, routing, readers, SEO and contact handling |
| `data/`, `templates/`, `assets/` | JSON catalogues, Go templates, CSS/JS, images and fonts |
| `sketches/` | Design studies A–E; the website follows design E |
| `.dev/` | Development reports, architecture proposals and a Go tutorial |

## The autobiography is imagined

**The text in `autobiografie/` was not written by Jackie Leven.** It is a pastiche based on what Leven said about himself. Each chapter carries this notice and ends with a “Documented / invented” section listing each separately.

The distinction matters. Leven was a habitual embellisher: Bob Dylan as a supposed co-writer, a contract killer as song inspiration, a whisky his label boss called “a complete scam”. His real memories already sound invented. Unlabelled fictional first-person prose alongside them would make his biography impossible to disentangle.

On the website, the book appears under Biography: every chapter has a pastiche notice, Pastiche in the page title, no quotation markup, and `noindex`. The website reads chapters directly from `autobiografie/`. See [`autobiografie/00-rahmen.md`](autobiografie/00-rahmen.md), the section on the website presentation.

## Validate content

The [maintenance tools](werkzeug/README.md) require Python 3.10 or newer. Image processing also requires Pillow; the Go runtime itself does not use these tools.

The server serves only approved routes and files under `/assets/`. Research, templates, data and dotfiles are not exposed as browsable website directories.

```sh
python3 werkzeug/messen.py              # measure chapters against the corpus
python3 werkzeug/pruefen.py 07 08       # identify possible AI language patterns
python3 werkzeug/zitate.py              # check original quotations against sources
python3 werkzeug/inhalte.py            # validate catalogues and sources
```

## Languages

The website runs in German and English under `/de/…` and `/en/…`. `/` redirects according to the browser's `Accept-Language`, falling back to German. Paths are translated too (`/de/zeitreise/1950-kirkcaldy`, `/en/timeline/1950-kirkcaldy`); paths in the wrong language redirect, as do old addresses without a language prefix.

**Quotations are never translated.** They occur once in `data/stationen.json` and appear in the original English in every language version, with `lang="en"`.

Text lives in three places depending on its purpose:

| Content | Location | Requirement |
|---|---|---|
| Interface, month names, URL paths | `data/lang/<code>.json` | Required |
| Milestone texts (title, label, description, caption) | `data/texte/<code>.json` | Optional |
| Prose pages (About, Biography) | `templates/<code>/` | Optional |

Additional languages need matching language, route and fallback rules in `internal/site/` and corresponding tests, as well as content. German and English are currently supported. English labels are deliberately not word-for-word translations: German uses “Station · Kirkcaldy”, while English uses just the place name.

```sh
python3 werkzeug/zitate.py                 # compare each quotation character by character with its source
```

## Tests, releases and operations

```sh
go test -race ./...
go vet ./...
node werkzeug/browserablaeufe.cjs
python3 -B -m unittest discover -s ops -p 'test_*.py'
python3 ops/prepare-go-release.py /tmp/jackieleven-go-release --goos linux --goarch amd64
```

The destination directory must be new. `ops/go-release-files.json` limits the package to the binary, published texts, JSON data, templates and required assets. The builder writes the revision, build status and SHA-256 checksums. Before deployment, a release is started independently and checked against the stored page contract; source-tree tests alone are insufficient.

The [operations guide](ops/GO-BETRIEB.md) describes the Go service behind nginx, private state files and version switching. The [preview guide](ops/GO-PREVIEW.md) documents the installed Hetzner test instance and its removal. This branch no longer contains tools for installing the old server runtime. Static studies in `sketches/` and the former interim page in `interim/` remain as design material.

## Development documents

The development documents in `.dev/` are versioned project documentation and are not served by the website. They retain their dates, reviewed revisions and distinctions between proposals and implemented features.

- [Go tutorial](.dev/go-tutorial.html)
- [Search architecture and implementation status](.dev/suche-architektur.html)
- [Archive ontology](.dev/ontologie.html)
- [Cataloguing strategy](.dev/erschliessung.html)
- [Ontology and search review, 25 October 2026](.dev/pruefung-ontologie-suche-2026-10-25.html)
- [Pastiche workshop report, 17 September 2026](.dev/pastiche-werkstattbericht-2026-09-17.md)

## Sources and attribution

The research archive preserves source references and distinguishes documented findings, unresolved leads and editorial interpretation. Original texts and images retain their respective authorship and rights; inclusion in this repository does not assign those rights to this project.

The timeline uses short verbatim quotations with archive links. The Deep Pool reproduces original contributions, including their quotations and song passages, with provenance and rights notices. The imagined autobiography is explicitly labelled as pastiche throughout.

## Search engines and previews

`internal/site/seo.go` manages metadata and the public origin `https://jackieleven.com`. Each content page has a canonical link, DE/EN alternate-language links, a description and Open Graph/Twitter preview data. JSON-LD describes an independent tribute and content about Jackie, not an official artist website. Filter and context parameters are excluded from canonical URLs.

`/sitemap.xml` is generated from published routes, including language variants. Redirects, filter variants and pastiche chapters marked `noindex` are excluded. The biography landing page remains discoverable; `data-nosnippet` excludes its fictional narrative from search previews. The sitemap does not invent modification dates.

Only requests to `jackieleven.com` permit indexing. Other hosts, including localhost and previews, return `noindex` and a blocking `robots.txt`. A domain change requires updating the `origin` constant and host check in `internal/site/server.go`. Error pages and HTML fragments also use `noindex`.

Check with `go test ./internal/site` and the release checks above. `ops/nginx-go-site.conf` is the installed production template; `ops/check-site.py` checks a fully configured production instance. The current preview uses a separate service and nginx rules. Search Console verification will be added only with the actual verification code.
