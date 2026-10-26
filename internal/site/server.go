// Package site serves the bilingual Jackie Leven tribute with a Go HTTP runtime.
package site

import (
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"jackieleven/internal/searchclient"
)

type Config struct {
	Root           string
	BasePath       string
	TrustProxy     bool
	Contact        ContactConfig
	SearchURL      string
	SearchManifest string
}
type App struct {
	root      string
	basePath  string
	data      *Data
	templates *template.Template
	contact   *Contact
	fanVideos bool
	assets    http.Handler
	search    *searchclient.Client
}
type request struct {
	app                      *App
	lang, route, slug, title string
	live                     bool
	templates                *template.Template
}

func New(config Config) (*App, error) {
	basePath, err := normalizeBasePath(config.BasePath)
	if err != nil {
		return nil, err
	}
	root, err := filepath.Abs(config.Root)
	if err != nil {
		return nil, err
	}
	d, err := loadData(root)
	if err != nil {
		return nil, err
	}
	a := &App{root: root, basePath: basePath, data: d, fanVideos: os.Getenv("JACKIE_FAN_VIDEOS") == "1"}
	if config.SearchURL != "" || config.SearchManifest != "" {
		if config.SearchURL == "" || config.SearchManifest == "" {
			return nil, fmt.Errorf("search: URL and manifest must both be configured")
		}
		a.search, err = searchclient.New(config.SearchURL, config.SearchManifest)
		if err != nil {
			return nil, err
		}
	}
	config.Contact.TrustProxy = config.TrustProxy
	config.Contact.CookiePath = basePath + "/"
	a.contact = NewContact(config.Contact)
	a.assets = http.StripPrefix("/assets/", http.FileServer(http.Dir(filepath.Join(root, "assets"))))
	dummy := &request{app: a, lang: "de"}
	base := template.New("site").Funcs(dummy.functions())
	err = filepath.WalkDir(filepath.Join(root, "templates"), func(p string, e os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if e.IsDir() || !strings.HasSuffix(p, ".gohtml") {
			return nil
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		name, _ := filepath.Rel(filepath.Join(root, "templates"), p)
		_, err = base.New(filepath.ToSlash(name)).Parse(string(b))
		return err
	})
	if err != nil {
		return nil, err
	}
	a.templates = base
	return a, nil
}
func preferredLanguage(header string) string {
	type preference struct {
		lang string
		q    float64
	}
	var p []preference
	for _, part := range strings.Split(header, ",") {
		a := strings.Split(strings.TrimSpace(part), ";")
		l := strings.ToLower(strings.TrimSpace(a[0]))
		if len(l) > 2 {
			l = l[:2]
		}
		q := 1.0
		if len(a) > 1 {
			if j := strings.Index(a[1], "q="); j >= 0 {
				if n, e := strconv.ParseFloat(strings.TrimSpace(a[1][j+2:]), 64); e == nil {
					q = n
				}
			}
		}
		p = append(p, preference{l, q})
	}
	sort.SliceStable(p, func(i, j int) bool { return p[i].q > p[j].q })
	for _, v := range p {
		if v.lang == "de" || v.lang == "en" {
			return v.lang
		}
	}
	return "de"
}
func (a *App) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if a.basePath == "" {
		a.serveHTTP(w, r)
		return
	}
	// A mounted preview is never an indexable production instance, even if its
	// upstream accidentally forwards the production Host header.
	w.Header().Set("X-Robots-Tag", "noindex")
	if r.URL.EscapedPath() == a.basePath {
		target := a.basePath + "/"
		if r.URL.RawQuery != "" {
			target += "?" + r.URL.RawQuery
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Location", target)
		w.WriteHeader(http.StatusMovedPermanently)
		return
	}
	if !strings.HasPrefix(r.URL.EscapedPath(), a.basePath+"/") {
		http.NotFound(w, r)
		return
	}
	http.StripPrefix(a.basePath, http.HandlerFunc(a.serveHTTP)).ServeHTTP(w, r)
}
func (a *App) serveHTTP(w http.ResponseWriter, r *http.Request) {
	if a.serveSearch(w, r) {
		return
	}
	if strings.HasPrefix(r.URL.Path, "/assets/") {
		clean := strings.TrimPrefix(r.URL.Path, "/assets/")
		for _, p := range strings.Split(clean, "/") {
			if p == ".." || strings.HasPrefix(p, ".") {
				http.NotFound(w, r)
				return
			}
		}
		info, err := os.Stat(filepath.Join(a.root, "assets", clean))
		if err != nil || !info.Mode().IsRegular() {
			http.NotFound(w, r)
			return
		}
		if strings.HasSuffix(clean, ".js") {
			w.Header().Set("Content-Type", "application/javascript")
		}
		a.assets.ServeHTTP(w, r)
		return
	}
	if strings.HasPrefix(r.URL.Path, "//") {
		target := "/" + strings.Join(strings.FieldsFunc(r.URL.Path, func(r rune) bool { return r == '/' }), "/")
		if r.URL.RawQuery != "" {
			target += "?" + r.URL.RawQuery
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Location", a.basePath+target)
		w.WriteHeader(301)
		return
	}
	c := &request{app: a, lang: "de", live: a.basePath == "" && strings.ToLower(r.Host) == "jackieleven.com"}
	clone, err := a.templates.Clone()
	if err != nil {
		http.Error(w, "Rendering unavailable", 500)
		return
	}
	c.templates = clone.Funcs(c.functions())
	c.serve(w, r)
}
func (c *request) serve(w http.ResponseWriter, r *http.Request) {
	path := r.URL.EscapedPath()
	redirect := func(target string, status int) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Location", target)
		w.WriteHeader(status)
	}
	notFound := func() { c.page(w, r, "404", M{}, c.tr("titel.404"), "", 404, false) }
	if path == "/robots.txt" {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		if r.Method != "HEAD" {
			if c.live {
				fmt.Fprint(w, "User-agent: *\nAllow: /\nSitemap: "+origin+"/sitemap.xml\n")
			} else {
				fmt.Fprint(w, "User-agent: *\nDisallow: /\n")
			}
		}
		return
	}
	if path == "/sitemap.xml" {
		w.Header().Set("Content-Type", "application/xml; charset=utf-8")
		if !c.live {
			w.Header().Set("X-Robots-Tag", "noindex")
		}
		if r.Method != "HEAD" {
			fmt.Fprint(w, c.sitemap())
		}
		return
	}
	var parts []string
	for _, p := range strings.Split(path, "/") {
		if p != "" {
			parts = append(parts, p)
		}
	}
	if len(parts) == 0 {
		w.Header().Set("Vary", "Accept-Language")
		redirect(c.url("start", M{}, preferredLanguage(r.Header.Get("Accept-Language"))), 302)
		return
	}
	if parts[0] != "de" && parts[0] != "en" {
		c.lang = preferredLanguage(r.Header.Get("Accept-Language"))
		if len(parts) == 1 && parts[0] == "zeitreise" {
			redirect(c.url("zeitreise", M{}, "de"), 301)
			return
		}
		if len(parts) == 2 && parts[0] == "station" {
			slug := parts[1]
			if slug == "1983-der-ueberfall" {
				slug = "1983-caledonian-road"
			}
			redirect(c.url("station", M{"slug": slug}, "de"), 301)
			return
		}
		if len(parts) == 1 && (parts[0] == "biografie" || parts[0] == "ueber") {
			redirect(c.url(parts[0], M{}, "de"), 301)
			return
		}
		notFound()
		return
	}
	c.lang = parts[0]
	parts = parts[1:]
	if len(parts) == 0 {
		if !strings.HasSuffix(path, "/") {
			redirect(c.url("start"), 301)
			return
		}
		c.route = "start"
		c.page(w, r, "start", M{}, c.tr("titel.start"), "start", 200, false)
		return
	}
	page := ""
	for _, candidate := range []string{"station", "biografie", "pool", "diskografie", "stimmen", "hoeren", "ueber", "mitmachen", "impressum"} {
		for _, l := range []string{"de", "en"} {
			if c.tr("pfad."+candidate, M{}, l) == parts[0] {
				page = candidate
				break
			}
		}
		if page != "" {
			break
		}
	}
	if page == "" {
		notFound()
		return
	}
	correct := parts[0] == c.tr("pfad."+page)
	if page == "station" {
		if len(parts) == 1 {
			if !correct {
				redirect(c.url("zeitreise"), 301)
				return
			}
			c.route = "zeitreise"
			c.page(w, r, "zeitreise", M{"aktiv": 0}, c.tr("titel.zeitreise"), "zeitreise", 200, false)
			return
		}
		if len(parts) != 2 {
			notFound()
			return
		}
		slug := parts[1]
		if slug == "1983-der-ueberfall" {
			redirect(c.url("station", M{"slug": "1983-caledonian-road"}), 301)
			return
		}
		a := listValue(c.app.data.Values["stationen"])
		i := find(a, "slug", slug)
		if i < 0 {
			notFound()
			return
		}
		if !correct {
			redirect(c.url("station", M{"slug": slug}), 301)
			return
		}
		st := a[i]
		if parseFormValues(r.URL.RawQuery).Get("fragment") == "1" {
			body, err := c.render("buehne", M{"st": st})
			if err != nil {
				c.renderError(w, err)
				return
			}
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			w.Header().Set("Content-Language", c.lang)
			w.Header().Set("X-Robots-Tag", "noindex")
			w.Header().Set("Link", "<"+origin+c.routePath("station", M{"slug": slug})+">; rel=\"canonical\"")
			if r.Method != "HEAD" {
				fmt.Fprint(w, body)
			}
			return
		}
		c.route, c.slug = "station", slug
		c.page(w, r, "zeitreise", M{"aktiv": i}, c.tr("titel.station", M{"jahr": get(st, "jahr"), "titel": c.stationField(st, "titel")[0]}), "zeitreise", 200, false)
		return
	}
	if page == "pool" {
		if len(parts) == 1 {
			redirect(c.url("kolumne", M{"slug": get(c.app.data.Columns[0], "slug")}), 302)
			return
		}
		if len(parts) == 2 && (parts[1] == c.tr("pfad.pool_archiv", M{}, "de") || parts[1] == c.tr("pfad.pool_archiv", M{}, "en")) {
			if parts[1] != c.tr("pfad.pool_archiv") {
				redirect(c.url("pool_archiv"), 301)
				return
			}
			c.route = "pool_archiv"
			c.page(w, r, "pool", M{}, c.tr("titel.pool_archiv"), "pool", 200, false)
			return
		}
		if len(parts) != 2 {
			notFound()
			return
		}
		i := find(c.app.data.Columns, "slug", parts[1])
		if i < 0 {
			notFound()
			return
		}
		k := c.app.data.Columns[i]
		c.route, c.slug = "kolumne", parts[1]
		c.page(w, r, "kolumne", M{"i": i}, c.tr("titel.kolumne", M{"datum": c.columnDate(k), "rubrik": c.columnRubric(k)}), "pool", 200, false)
		return
	}
	if len(parts) == 2 {
		slug := parts[1]
		switch page {
		case "diskografie":
			ctx := c.releaseContext(parseFormValues(r.URL.RawQuery))
			if slug == "1973-control" {
				redirect(c.releaseLink("1975-control", ctx), 301)
				return
			}
			p := c.release(slug)
			if p == nil {
				notFound()
				return
			}
			if !correct {
				redirect(c.releaseLink(slug, ctx), 301)
				return
			}
			c.route, c.slug = "platte", slug
			c.page(w, r, "platte", M{"platte": p, "kontext": ctx}, str(get(p, "title"))+" · "+str(get(p, "year"))+" · "+c.tr("nav.diskografie"), "diskografie", 200, false)
			return
		case "stimmen":
			i := c.sourceIndex(slug)
			if i < 0 {
				notFound()
				return
			}
			if !correct {
				redirect(c.url("quelle", M{"slug": slug}), 301)
				return
			}
			c.route, c.slug = "quelle", slug
			c.page(w, r, "quelle", M{"i": i}, c.sourceField(c.app.data.Sources[i], "titel")+" · "+c.tr("nav.stimmen"), "stimmen", 200, false)
			return
		case "biografie":
			a := listValue(c.app.data.Values["pastiche"])
			i := find(a, "slug", slug)
			if i < 0 {
				notFound()
				return
			}
			if !correct {
				redirect(c.url("kapitel", M{"slug": slug}), 301)
				return
			}
			c.route, c.slug = "kapitel", slug
			c.page(w, r, "kapitel", M{"i": i}, c.tr("titel.kapitel", M{"titel": get(a[i], "titel"), "nr": i + 1}), "biografie", 200, true)
			return
		}
	}
	if len(parts) != 1 {
		notFound()
		return
	}
	if !correct {
		redirect(c.url(page), 301)
		return
	}
	c.route = page
	v := M{}
	view := page
	status := 200
	switch page {
	case "mitmachen":
		var done bool
		v, done = c.app.contact.Handle(w, r, c.url("mitmachen"))
		if done {
			return
		}
		status = num(v["status"])
	case "stimmen":
		v["filter"] = sourceFilter(parseFormValues(r.URL.RawQuery))
	case "diskografie", "hoeren":
	default:
		view = c.lang + "/" + page
	}
	c.page(w, r, view, v, c.tr("titel."+page), page, status, false)
}
func (c *request) page(w http.ResponseWriter, r *http.Request, view string, v M, title, nav string, status int, noindex bool) {
	c.title = title
	body, err := c.render(view, v)
	if err != nil {
		c.renderError(w, err)
		return
	}
	noindex = noindex || status >= 400 || !c.live
	full, err := c.render("layout", M{"inhalt": body, "titel": title, "nav": nav, "noindex": noindex})
	if err != nil {
		c.renderError(w, err)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Content-Language", c.lang)
	if noindex {
		w.Header().Set("X-Robots-Tag", "noindex")
	}
	w.WriteHeader(status)
	if r.Method != "HEAD" {
		fmt.Fprint(w, full)
	}
}
func (c *request) renderError(w http.ResponseWriter, err error) {
	log.Printf("site: %v", err)
	http.Error(w, "Rendering unavailable", http.StatusInternalServerError)
}

// HTTPServer sets finite read/write deadlines for the public process.
func HTTPServer(addr string, handler http.Handler) *http.Server {
	return &http.Server{Addr: addr, Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: 45 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 1 << 20}
}
