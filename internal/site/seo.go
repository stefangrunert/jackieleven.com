package site

import (
	"encoding/json"
	"html"
	"html/template"
	"regexp"
	"strings"
)

var tagsRE = regexp.MustCompile(`<[^>]*>`)
var whitespaceRE = regexp.MustCompile(`\s+`)
var lastWordRE = regexp.MustCompile(`\s+\S*$`)

func shortDescription(s string) string {
	s = strings.TrimSpace(whitespaceRE.ReplaceAllString(html.UnescapeString(tagsRE.ReplaceAllString(string(MarkdownInline(s)), "")), " "))
	r := []rune(s)
	if len(r) <= 165 {
		return s
	}
	return lastWordRE.ReplaceAllString(string(r[:164]), "") + "…"
}
func (c *request) seo(title string) M { return c.seoFor(title, c.route, c.slug) }
func (c *request) seoFor(title, name, slug string) M {
	i := 0
	if c.lang != "de" {
		i = 1
	}
	desc := c.tr("meta.beschreibung")
	if d, ok := descriptions[name]; ok {
		desc = d[i]
	}
	switch name {
	case "platte":
		if p := c.release(slug); p != nil {
			suffix := "Titelliste, Veröffentlichungsangaben, Quellen und verfügbare Hörlinks."
			if c.lang != "de" {
				suffix = "Track list, release information, sources and available listening links."
			}
			desc = str(get(p, "artist")) + ": " + str(get(p, "title")) + " (" + str(get(p, "year")) + "). " + suffix
		}
	case "quelle":
		if i := c.sourceIndex(slug); i >= 0 {
			q := c.app.data.Sources[i]
			desc = str(get(q, "medium")) + " · " + str(get(q, "datum")) + ": " + str(coalesce(get(get(q, "kurz"), c.lang), coalesce(get(get(q, "kurz"), "de"), c.sourceField(q, "titel"))))
		}
	case "station":
		a := listValue(c.app.data.Values["stationen"])
		if i := find(a, "slug", slug); i >= 0 {
			desc = str(c.stationField(a[i], "text")[0])
		}
	case "kolumne":
		if i := find(c.app.data.Columns, "slug", slug); i >= 0 {
			k := c.app.data.Columns[i]
			suffix := "Eine Kolumne von Jackie Leven, im englischen Original aus seiner damaligen Website."
			if c.lang != "de" {
				suffix = "A column by Jackie Leven, in its original English, from his former website."
			}
			desc = c.columnRubric(k) + " · " + c.columnDate(k) + ". " + suffix
		}
	}
	if name == "stimmen" {
		title = c.tr("nav.stimmen") + " · Jackie Leven"
	}
	if !strings.Contains(title, "Jackie Leven") {
		title += " · Jackie Leven"
	}
	var canonical any
	if name != "" {
		canonical = origin + c.url(name, M{"slug": slug})
	}
	return M{"titel": title, "beschreibung": shortDescription(desc), "url": canonical, "bild": origin + "/assets/bilder/startseite/portrait-graphic.png"}
}
func (c *request) jsonLD() template.JS {
	s := c.seo(c.title)
	b, _ := json.Marshal(M{"@context": "https://schema.org", "@graph": []any{M{"@type": "WebSite", "@id": origin + "/#website", "url": origin + "/", "name": "Jackie Leven", "inLanguage": []string{"de", "en"}, "description": "An independent personal tribute to Jackie Leven, his music and his writing."}, M{"@type": "Person", "@id": origin + "/#jackie-leven", "name": "Jackie Leven"}, M{"@type": "WebPage", "@id": str(s["url"]) + "#webpage", "url": s["url"], "name": s["titel"], "description": s["beschreibung"], "inLanguage": c.lang, "isPartOf": M{"@id": origin + "/#website"}, "about": M{"@id": origin + "/#jackie-leven"}}}})
	return template.JS(b)
}
func (c *request) sitemap() string {
	routes := [][2]string{}
	for _, n := range []string{"start", "hoeren", "diskografie", "zeitreise", "biografie", "stimmen", "pool_archiv", "ueber", "mitmachen", "impressum"} {
		routes = append(routes, [2]string{n, ""})
	}
	for _, v := range listValue(c.app.data.Values["stationen"]) {
		routes = append(routes, [2]string{"station", str(get(v, "slug"))})
	}
	for _, v := range c.app.data.Columns {
		routes = append(routes, [2]string{"kolumne", str(get(v, "slug"))})
	}
	for _, v := range c.releases() {
		routes = append(routes, [2]string{"platte", str(get(v, "id"))})
	}
	for _, q := range c.app.data.Sources {
		if sourcePage(q) {
			routes = append(routes, [2]string{"quelle", str(get(q, "id"))})
		}
	}
	var b strings.Builder
	b.WriteString("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:xhtml=\"http://www.w3.org/1999/xhtml\">")
	for _, r := range routes {
		for _, l := range []string{"de", "en"} {
			b.WriteString("\n<url><loc>" + html.EscapeString(origin+c.url(r[0], M{"slug": r[1]}, l)) + "</loc>")
			for _, a := range []string{"de", "en", "x-default"} {
				lang := a
				if a == "x-default" {
					lang = "de"
				}
				b.WriteString(`<xhtml:link rel="alternate" hreflang="` + a + `" href="` + html.EscapeString(origin+c.url(r[0], M{"slug": r[1]}, lang)) + `"/>`)
			}
			b.WriteString("</url>")
		}
	}
	b.WriteString("\n</urlset>\n")
	return b.String()
}
