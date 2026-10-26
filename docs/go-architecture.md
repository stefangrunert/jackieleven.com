# Go migration architecture

The first stage replaces the server runtime while preserving the existing public contract: URLs, redirects, languages, content, HTML structure, CSS/JavaScript hooks, metadata and form behaviour. Ontology and search follow as separate features. This allows migration differences to be checked separately from later product changes.

## Runtime and content

`cmd/jackieleven` starts a `net/http` server. `internal/site` contains routing, content preparation, SEO, templates and contact handling. The application needs no libraries beyond the Go standard library and no PHP process.

`data/` contains the existing structured catalogues and translations as JSON. Go loads them at startup. Catalogue records retain their content field names; routing, session and configuration state have dedicated Go types. The flexible catalogue records initially make the transfer of the existing dataset easier to verify. They are not yet an ontological domain model.

`templates/` contains actual `html/template` templates. Prerendered page snapshots are not used as runtime sources. Language, route and template functions are bound to each individual request. Shared content data is read-only after loading. This is an important difference from PHP: a Go process handles several requests concurrently and must not keep language or route state in mutable global variables.

The selected texts in `research/columns/` and `autobiografie/` remain Markdown sources. The deliberately small renderer reproduces the existing reading rules, including verse lines, repeated historical headings and translation fallbacks. The Go version was compared against all 73 published column models and their HTML reading versions, both chapter languages and 202 Markdown examples.

## HTML and addresses

`html/template` handles contextual escaping. Trusted HTML is produced only in a few controlled places: already rendered application templates, the Markdown reader that escapes its input first, and explicitly permitted attribute fragments. The entire public identity remains `https://jackieleven.com`; arbitrary Host headers cannot generate arbitrary canonical URLs. Local and other non-production hosts remain noindex.

Only `/assets/` serves files directly. Data, templates, research and dotfiles have no general file-serving route. Release packages additionally allow only an explicit selection of the files actually needed. A production process reads its content, including assets, from a release directory resolved once at startup.

## Contact handling and concurrency

Contact configuration comes exclusively from process environment variables. Tests can replace Turnstile and delivery functions without contacting real providers. Sessions, form tokens, retry identifiers and IP limits are stored in private state files. File locks serialise concurrent processing of the same session and protect IP counters. This preserves CSRF lifetime, form age, multiple open tabs, cooldown and retry protection across concurrency and restarts.

A delivery attempt with unchanged form content retains its idempotency identifier after an uncertain outcome. Successful delivery is recorded under the same session lock. External responses must be complete and valid; request and response sizes are bounded. Sensitive form contents and credentials are not logged.

Proxy headers are trusted only with `-trust-proxy` enabled and a direct loopback peer. nginx replaces them with its own values obtained from trusted sources. The backend port remains local. On SIGTERM, the main process waits for requests to finish gracefully, up to the documented shutdown deadline.

## Evidence and limits

The HTTP comparison covers every sitemap target plus alias, language, filter, fragment and error cases. Normalisation rules are listed in `werkzeug/parity.md`. In particular, meaningful inline spaces and non-breaking spaces are retained; attributes consumed as JSON are compared by data value.

The frozen PHP snapshot is a test reference, not part of the Go server. An Apache-generated error for an encoded path separator is explicitly checked only for a 404 status and absence of data disclosure; equality of its error-page HTML is not claimed.

Nine page types were also compared in the browser at 1440×1000 and 390×844: identical DOM geometry and pixel-identical screenshots after images had finished loading. Interaction checks cover the dynamic timeline, language changes, history and filter context. This evidence concerns the states tested; it does not establish equivalence in every possible browser or network situation.

The separate Linux test instance is installed on Hetzner and was checked at `https://unpubli.sh/jackieleven/`; see `ops/GO-PREVIEW.md`. Real provider integration and the production cutover are separate acceptance steps. The existing site remains available until then.
