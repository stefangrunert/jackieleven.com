package site

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var attrPattern = regexp.MustCompile(`^(?:\s*(?:class|lang|target|rel|aria-current|aria-invalid|aria-describedby)="[a-zA-Z0-9 _-]*"|\s*(?:hidden|disabled|required|selected))*\s*$`)

// attrs accepts only the narrow vocabulary of fixed attribute fragments used by
// our templates. Content and request values never get an unbounded HTML bypass.
func attrs(v any) template.HTMLAttr {
	s := str(v)
	if !attrPattern.MatchString(s) {
		return ""
	}
	return template.HTMLAttr(s)
}
func (c *request) functions() template.FuncMap {
	return template.FuncMap{
		"releaseFacts": func() []Pair {
			return []Pair{{"format", "disk.format"}, {"label", "disk.label"}, {"catalog", "disk.katalog"}}
		}, "get": get, "dict": dict, "list": func(v ...any) []any { return v }, "pairs": pairs, "nilValue": func() any { return nil }, "str": str, "num": num, "truth": truth, "coalesce": coalesce, "equal": equal, "unequal": func(a, b any) bool { return !equal(a, b) }, "greater": func(a, b any) bool { return num(a) > num(b) }, "less": func(a, b any) bool { return num(a) < num(b) }, "ge": func(a, b any) bool { return num(a) >= num(b) }, "le": func(a, b any) bool { return num(a) <= num(b) }, "add": func(a, b any) any {
			if _, ok := a.(M); ok {
				m := cloneMap(b)
				for k, v := range asMap(a) {
					m[k] = v
				}
				return m
			}
			return num(a) + num(b)
		}, "sub": func(a, b any) int { return num(a) - num(b) }, "mod": func(a, b any) int {
			if num(b) == 0 {
				return 0
			}
			return num(a) % num(b)
		}, "mul": func(a, b any) int { return num(a) * num(b) }, "cat": func(a, b any) string { return str(a) + str(b) }, "choose": func(v, a, b any) any {
			if truth(v) {
				return a
			}
			return b
		}, "count": count, "empty": func(v any) bool { return !truth(v) }, "isset": func(v any) bool { return v != nil }, "in_array": func(v, a any, _ ...bool) bool { return contains(a, v) }, "implode": join, "array_filter": filtered, "array_slice": slice, "array_key_first": func(v any) any {
			p := pairs(v)
			if len(p) > 0 {
				return p[0].Key
			}
			return nil
		}, "strtoupper": strings.ToUpper, "str_starts_with": strings.HasPrefix, "substr": func(s string, start int, n ...int) string {
			if start < 0 {
				start = len(s) + start
			}
			if start < 0 || start > len(s) {
				return ""
			}
			end := len(s)
			if len(n) > 0 && start+n[0] < end {
				end = start + n[0]
			}
			return s[start:end]
		}, "str_pad": func(v any, n int, pad string, _ any) string {
			s := str(v)
			for len(s) < n {
				s = pad + s
			}
			return s
		}, "sprintf": fmt.Sprintf,
		"attrs": attrs, "nl2br": func(v any, _ ...bool) template.HTML {
			return template.HTML(strings.ReplaceAll(template.HTMLEscapeString(str(v)), "\n", "<br>\n"))
		}, "md": Markdown, "md_inline": MarkdownInline, "kolumnen_html": ColumnHTML, "kolumnen_lesetext": func(v any) string { return ColumnReadingText(asMap(v)) }, "lang": func(l string) template.HTMLAttr {
			if l == c.lang {
				return ""
			}
			return attrs(` lang="` + l + `"`)
		},
		"base_path": func() string { return c.app.basePath }, "asset": c.assetURL, "canonical_alternative": c.canonicalAlternative, "canonical_alternativen": func(slug ...string) string { return c.alternativesJSON(true, slug...) },
		"t": c.tr, "url": c.url, "sprache": func() string { return c.lang }, "alternativ_url": c.alternative, "absolut": func(s string) string { return origin + s }, "seo_live": func() bool { return c.live }, "seo_daten": c.seo, "jsonld": c.jsonLD, "seoAttribut": func(name string, p any, title string) string {
			b, _ := json.Marshal(c.seoFor(title, name, str(get(p, "slug"))))
			return string(b)
		}, "alternativen": func(slug ...string) string { return c.alternativesJSON(false, slug...) },

		"render": c.render, "render_lokal": func(view string, args ...M) (template.HTML, error) { return c.render(c.lang+"/"+view, args...) }, "filemtime": func(p string) int64 {
			if s, e := os.Stat(filepath.Join(c.app.root, p)); e == nil {
				return s.ModTime().Unix()
			}
			return 0
		},
		"sfeld": c.stationField, "sfeld_html": c.stationHTML, "quelle_text": func(q any) string { return c.tr("rubrik."+str(get(q, "rubrik"))) + ", " + c.date(str(get(q, "datum"))) }, "kolumnen_datum": c.columnDate, "kolumnen_rubrik": c.columnRubric, "kapitelliste": func() any { return c.app.data.Values["pastiche"] },
		"diskografie": func() any { return c.app.data.Values["diskografie"] }, "diskografie_index": c.releaseIndex, "diskografie_link": c.releaseLink, "diskografie_zurueck": c.releaseBack, "diskografie_projekte": c.projects, "diskografie_hoerlinks": c.listenLinks, "diskografie_musikdienste": func() M {
			return M{"spotify": M{"name": "Spotify", "tooltip": "Listen on Spotify"}, "apple": M{"name": "Apple Music", "tooltip": "Listen on Apple Music"}, "qobuz": M{"name": "Qobuz", "tooltip": "Listen or download on Qobuz"}, "amazon": M{"name": "Amazon Music", "tooltip": "Listen on Amazon Music"}, "bandcamp": M{"name": "Bandcamp", "tooltip": "Listen or buy on Bandcamp"}}
		}, "diskografie_liedschluessel": songKey, "diskografie_youtube_fassungen": c.videos, "diskografie_youtube": func(s string) any { return get(c.videos(s), 0) }, "youtube_video_id": videoID, "diskografie_livevideos": c.liveVideos, "diskografie_konzertdatum": c.date, "diskografie_fassung_ort": c.versionPlace, "diskografie_fassung_tooltip": versionTooltip, "diskografie_zeitmarke": func(v any) string {
			n := num(v)
			if n >= 3600 {
				return fmt.Sprintf("%d:%02d:%02d", n/3600, n%3600/60, n%60)
			}
			return fmt.Sprintf("%d:%02d", n/60, n%60)
		}, "watch": func(s any) string {
			u := "https://www.youtube.com/watch?v=" + str(get(get(s, "video"), "id"))
			if truth(get(s, "start")) {
				u += "&t=" + str(get(s, "start")) + "s"
			}
			return u
		},
		"stimmen": func() []any { return c.app.data.Sources }, "stimmen_kategorien": func() []any { return categories }, "stimmen_zugaenge": func() []any { return accesses }, "stimme_gewicht": weight, "stimme_mit_seite": sourcePage, "stimme_passt": sourceMatches, "stimme_feld": c.sourceField, "stimme_titelsprache": c.sourceTitleLanguage, "stimme_text": c.sourceText, "stimme_datum": c.sourceDate, "stimme_sprache": func(s string) string {
			return str(coalesce(get(c.app.data.Languages[c.lang]["stimmen.sprachen"], s), strings.ToUpper(s)))
		}, "stimme_lizenz": c.sourceLicense, "stimme_ziel": c.sourceTarget, "stimme_link": func(s string) string { return c.url("quelle", M{"slug": s}) }, "stimmen_zur_ausgabe": func(id string) []any {
			var out []any
			for _, q := range c.app.data.Sources {
				if sourcePage(q) && contains(get(q, "ausgaben"), id) {
					out = append(out, q)
				}
			}
			return out
		}, "weitere": func(qs any) []any {
			var out []any
			for _, q := range listValue(qs) {
				if !sourcePage(q) {
					out = append(out, q)
				}
			}
			return out
		}, "matchedCount": func(qs any, f any) int {
			n := 0
			for _, q := range listValue(qs) {
				if sourceMatches(q, f) {
					n++
				}
			}
			return n
		}, "jahrlabel": func(s string) string {
			if s == "" {
				return c.tr("stimmen.undatiert")
			}
			return s
		}, "anker": func(s string) string {
			if s == "" {
				s = "undatiert"
			}
			return "jahr-" + s
		}, "meta": func(q any) string {
			return c.sourceDate(str(get(q, "datum"))) + " · " + c.sourceField(q, "medium") + " · " + c.tr("stimmen.kategorie."+str(get(q, "kategorie")))
		}, "licenseNotice": func(q, l any) template.HTML {
			s := c.tr("stimmen.lizenz", M{"autor": coalesceNonempty(get(q, "autor"), "–"), "medium": get(q, "medium")})
			link := `<a href="` + template.HTMLEscapeString(str(get(l, "url"))) + `" target="_blank" rel="noopener noreferrer license">` + template.HTMLEscapeString(str(get(l, "name"))) + `</a>`
			return template.HTML(strings.ReplaceAll(template.HTMLEscapeString(s), "{lizenz}", link))
		},
	}
}
func coalesceNonempty(a, b any) any {
	if truth(a) {
		return a
	}
	return b
}
func (c *request) render(name string, args ...M) (template.HTML, error) {
	v := M{}
	if len(args) > 0 {
		v = cloneMap(args[0])
	}
	v = c.viewData(name, v)
	var b bytes.Buffer
	if err := c.templates.ExecuteTemplate(&b, name+".gohtml", v); err != nil {
		return "", fmt.Errorf("render %s: %w", name, err)
	}
	return template.HTML(b.String()), nil
}
func (c *request) viewData(name string, v M) M {
	switch name {
	case "start":
		s := asMap(c.app.data.Values["startseite"])
		v["start"] = s
		v["poolQuelle"] = get(c.app.data.Columns, find(c.app.data.Columns, "slug", str(get(s["pool"], "slug"))))
		v["lebenQuelle"] = get(c.app.data.Columns, find(c.app.data.Columns, "slug", str(get(s["leben"], "slug"))))
		v["platte"] = c.release(str(get(s["platte"], "id")))
		v["erstesVideo"] = get(s["hoeren"], 0)
		v["lebenslinie"] = []any{[]any{"1950", "fife", c.url("station", M{"slug": "1950-kirkcaldy"})}, []any{"1973", "field", c.releaseLink("1975-control")}, []any{"1977", "doll", c.url("station", M{"slug": "1977-doll-by-doll"})}, []any{"1994", "solo", c.url("station", M{"slug": "1994-mystery-of-love"})}, []any{"2011", "november", c.url("station", M{"slug": "2011-november"})}}
	case "zeitreise":
		a := listValue(c.app.data.Values["stationen"])
		i := num(v["aktiv"])
		v["alle"] = a
		v["n"] = len(a)
		v["vor"] = a[(i-1+len(a))%len(a)]
		v["nach"] = a[(i+1)%len(a)]
	case "buehne":
		st := v["st"]
		v["bildtext"] = c.stationField(st, "bildtext")[0]
		v["tusche"] = get(st, "bildstil") == "tusche"
		v["quelltext"] = get(c.app.data.Columns, find(c.app.data.Columns, "datei", str(get(get(st, "quelle"), "datei"))))
		v["platte"] = c.release(str(get(st, "platte")))
	case "hoeren":
		v["kapitel"] = c.app.data.Values["hoeren"]
		v["nummer"] = 0
	case "diskografie":
		v["jahre"] = group(c.releases(), func(p any) string { return str(get(p, "year")) })
		v["quellen"] = get(c.app.data.Values["diskografie"], "sources")
	case "platte":
		p := v["platte"]
		id := str(get(p, "id"))
		details := c.releaseDetails(id)
		v["details"] = details
		v["hoeren"] = c.listenLinks(id)
		ctx := cloneMap(v["kontext"])
		if !releaseMatches(p, ctx) {
			delete(ctx, "projekt")
			delete(ctx, "format")
		}
		v["kontext"] = ctx
		var releases []any
		for _, r := range c.releases() {
			if releaseMatches(r, ctx) {
				releases = append(releases, r)
			}
		}
		i := find(releases, "id", id)
		v["platten"] = releases
		v["vor"] = get(releases, i-1)
		v["nach"] = get(releases, i+1)
		v["navigation"] = M{"vor": v["vor"], "nach": v["nach"], "platte": p, "kontext": ctx}
		var sources []any
		for _, k := range listValue(get(p, "sources")) {
			sources = append(sources, get(get(c.app.data.Values["diskografie"], "sources"), k))
		}
		sources = append(sources, listValue(get(details, "sources"))...)
		if get(p, "coverSource") != nil {
			sources = append(sources, M{"label": c.tr("disk.coverquelle"), "url": get(p, "coverSource")})
		}
		var unique []any
		seen := map[string]int{}
		for _, q := range sources {
			u := str(get(q, "url"))
			if j, ok := seen[u]; ok {
				unique[j] = q
			} else {
				seen[u] = len(unique)
				unique = append(unique, q)
			}
		}
		v["quellen"] = unique
	case "stimmen":
		f := asMap(v["filter"])
		v["auswahl"] = num(f["auswahl"])
		v["alleJahre"] = group(c.app.data.Sources, sourceYear)
		var selected []any
		for _, q := range c.app.data.Sources {
			if sourceMatches(q, f) {
				selected = append(selected, q)
			}
		}
		v["jahre"] = group(selected, sourceYear)
		v["gezeigt"] = len(selected)
	case "quelle":
		q := cloneMap(get(c.app.data.Sources, v["i"]))
		v["q"] = q
		var pages []any
		for _, s := range c.app.data.Sources {
			if sourcePage(s) {
				pages = append(pages, s)
			}
		}
		i := find(pages, "id", str(q["id"]))
		v["vor"] = get(pages, i-1)
		v["nach"] = get(pages, i+1)
		v["inhalt"] = c.sourceText(q["inhalt"])[0]
		v["inhaltSprache"] = c.lang
		v["nb"] = strings.Contains(str(q["url"]), "nb.no")
		var quotes []any
		for _, z := range listValue(q["zitate"]) {
			duplicate := false
			for _, b := range listValue(q["beleg"]) {
				if strings.Trim(str(get(z, "text")), " .") == strings.Trim(str(get(b, "original")), " .") {
					duplicate = true
				}
			}
			if !duplicate {
				quotes = append(quotes, z)
			}
		}
		q["zitate"] = quotes
	case "kolumne":
		i := num(v["i"])
		a := c.app.data.Columns
		k := get(a, i)
		v["liste"] = a
		v["k"] = k
		v["vor"] = get(a, i-1)
		v["nach"] = get(a, i+1)
		v["captureText"] = c.date(str(get(k, "capture")))
	case "pool":
		v["liste"] = c.app.data.Columns
		v["jahre"] = group(c.app.data.Columns, sourceYear)
	case "kapitel":
		i := num(v["i"])
		a := listValue(c.app.data.Values["pastiche"])
		k := get(a, i)
		v["liste"] = a
		v["k"] = k
		v["vor"] = get(a, i-1)
		v["nach"] = get(a, i+1)
		parts := ChapterParts(c.app.root, str(get(k, "slug")), c.lang)
		for key, dest := range map[string]string{"text": "text", "anmerkung": "anm", "apparat": "app"} {
			v[dest] = get(parts[key], 0)
			v[dest+"Sprache"] = get(parts[key], 1)
		}
		v["intro"] = truth(v["intro"])
		v["startseite"] = truth(v["startseite"])
	case "kapitel-zeitstrahl":
		v["startseite"] = truth(v["startseite"])
	case "livevideos":
		v["sichtbar"] = 3
	}
	return v
}
func sourceYear(q any) string {
	s := str(get(q, "datum"))
	if len(s) > 4 {
		return s[:4]
	}
	return s
}
