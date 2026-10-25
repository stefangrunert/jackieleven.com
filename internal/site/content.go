package site

import (
	"fmt"
	"html/template"
	"net/url"
	"regexp"
	"sort"
	"strings"
)

const origin = "https://jackieleven.com"

var categories = []any{"interviews", "portraets", "rezensionen", "konzertberichte", "nachrufe", "erinnerungen", "radio-tv", "foren", "buecher", "nachschlagewerke", "meldungen"}
var accesses = []any{"frei", "online", "archiv", "abo", "verloren"}

func (c *request) tr(key string, args ...any) string {
	l := c.lang
	if len(args) > 1 && str(args[1]) != "" {
		l = str(args[1])
	}
	v := coalesce(c.app.data.Languages[l][key], coalesce(c.app.data.Languages["de"][key], key))
	s := str(v)
	if len(args) > 0 {
		for k, v := range asMap(args[0]) {
			s = strings.ReplaceAll(s, "{"+k+"}", str(v))
		}
	}
	return s
}
func (c *request) url(name string, args ...any) string {
	p := M{}
	l := c.lang
	if len(args) > 0 {
		p = asMap(args[0])
	}
	if len(args) > 1 && str(args[1]) != "" {
		l = str(args[1])
	}
	base := "/" + l + "/"
	switch name {
	case "start":
		return base
	case "zeitreise":
		return base + c.tr("pfad.station", M{}, l)
	case "station", "kapitel", "kolumne", "platte", "quelle":
		parent := map[string]string{"station": "station", "kapitel": "biografie", "kolumne": "pool", "platte": "diskografie", "quelle": "stimmen"}[name]
		return base + c.tr("pfad."+parent, M{}, l) + "/" + url.PathEscape(str(p["slug"]))
	case "pool_archiv":
		return base + c.tr("pfad.pool", M{}, l) + "/" + c.tr("pfad.pool_archiv", M{}, l)
	default:
		return base + c.tr("pfad."+name, M{}, l)
	}
}
func (c *request) alternative(l string) string {
	name := c.route
	if name == "" {
		name = "start"
	}
	return c.url(name, M{"slug": c.slug}, l)
}
func (c *request) stationField(st any, f string) []any {
	slug := str(get(st, "slug"))
	if v := get(get(c.app.data.Texts[c.lang], slug), f); v != nil {
		return []any{v, c.lang}
	}
	return []any{coalesce(get(get(c.app.data.Texts["de"], slug), f), ""), "de"}
}
func (c *request) stationHTML(st any, f string) template.HTML {
	v := c.stationField(st, f)
	s := template.HTMLEscapeString(str(v[0]))
	if v[1] != c.lang {
		s = `<span lang="` + str(v[1]) + `">` + s + `</span>`
	}
	return template.HTML(s)
}
func (c *request) columnDate(v any) string { return c.date(str(get(v, "datum"))) }
func (c *request) columnRubric(v any) string {
	s := c.tr("pool.art." + str(get(v, "art")))
	if get(v, "nummer") != nil {
		s += " · " + str(get(v, "nummer"))
	}
	return s
}
func (c *request) date(s string) string {
	a := strings.Split(s, "-")
	if len(a) < 2 {
		return s
	}
	months := listValue(c.app.data.Languages[c.lang]["monate"])
	m := num(a[1]) - 1
	if m < 0 || m >= len(months) {
		return s
	}
	out := str(months[m]) + " " + a[0]
	if len(a) > 2 {
		sep := " "
		if c.lang == "de" {
			sep = ". "
		}
		out = fmt.Sprint(num(a[2])) + sep + out
	}
	return out
}
func (c *request) sourceDate(s string) string {
	if s == "" {
		return c.tr("stimmen.undatiert")
	}
	return c.date(s)
}
func (c *request) releases() []any {
	return listValue(get(c.app.data.Values["diskografie"], "releases"))
}
func (c *request) releaseIndex(id string) int { return find(c.releases(), "id", id) }
func (c *request) release(id string) any      { return get(c.releases(), c.releaseIndex(id)) }
func (c *request) releaseDetails(id string) any {
	return coalesce(get(c.app.data.Values["diskografie-details"], id), M{})
}
func (c *request) listenLinks(id string) any {
	return coalesce(get(c.app.data.Values["diskografie-hoerlinks"], id), []any{})
}
func (c *request) projects() []Pair {
	return []Pair{{"john-st-field", "John St. Field"}, {"doll-by-doll", "Doll by Doll"}, {"jackie-leven", "Jackie Leven"}, {"sir-vincent-lone", "Sir Vincent Lone"}, {"jackie-balfour", "Jackie Balfour"}, {"concrete-bulletproof-invisible", "Concrete Bulletproof Invisible"}, {"haunted-valley", "Haunted Valley"}, {"collaborations", c.tr("disk.kooperationen")}}
}
func (c *request) releaseContext(query url.Values) M {
	m := M{}
	for _, p := range c.projects() {
		if query.Get("projekt") == str(p.Key) {
			m["projekt"] = p.Key
		}
	}
	if contains([]any{"alben", "kleine", "reissue", "video", "unreleased"}, query.Get("format")) {
		m["format"] = query.Get("format")
	}
	if c.releaseIndex(query.Get("von")) >= 0 {
		m["von"] = query.Get("von")
	}
	return m
}
func releaseMatches(p any, m M) bool {
	if v := m["projekt"]; v != nil && !contains(get(p, "tags"), v) {
		return false
	}
	f := str(m["format"])
	kind := str(get(p, "kind"))
	switch f {
	case "":
		return true
	case "alben":
		return contains([]any{"album", "live", "compilation", "spoken", "tribute"}, kind)
	case "kleine":
		return kind == "single" || kind == "ep"
	default:
		return kind == f
	}
}
func contextQuery(m M) string {
	var p []string
	for _, k := range []string{"projekt", "format", "von"} {
		if m[k] != nil {
			p = append(p, k+"="+url.QueryEscape(str(m[k])))
		}
	}
	if len(p) == 0 {
		return ""
	}
	return "?" + strings.Join(p, "&")
}
func (c *request) releaseLink(id string, args ...M) string {
	m := M{}
	if len(args) > 0 {
		m = args[0]
	}
	return c.url("platte", M{"slug": id}) + contextQuery(m)
}
func (c *request) releaseBack(id string, m M) string {
	a := str(coalesce(m["von"], id))
	m = cloneMap(m)
	delete(m, "von")
	return c.url("diskografie") + contextQuery(m) + "#" + a
}

var songPrefix = regexp.MustCompile(`(?i)^\s*\(spoken\)\s*`)
var songBrackets = regexp.MustCompile(`(?i)\s*[\[(](?:live|edit|radio|remaster|bonus track|full version|beautiful version|from live show|etc\.)[^\])]*[\])]`)
var songSuffix = regexp.MustCompile(`(?i)\s*[-–—]\s*(?:live|radio edit|edit|remaster).*$`)
var nonSong = regexp.MustCompile(`[^a-z0-9]`)
var songAliases = map[string]string{"shadowinmyeye": "shadowinmyeyes", "thebarsofdundee": "barsofdundee", "levenlament": "levenslament", "standinginanothermansrain": "anothermansrain", "theworkingmanslovesong": "workingmanslovesong", "isawmylovewalkintotheclouds": "isawmylovewalkintoclouds", "oliverblues": "olivierblues", "humanface": "thehumanface", "palaceoflove": "thepalaceoflove", "boxershitharderwhenwomanarearound": "boxershitharderwhenwomenarearound", "balladofanneredmond": "theballadofanneredmond", "kingsofinfinitespaceplusstoryofbasilandronnie": "kingsofinfinitespace", "loversatthegunclubplusstoryofshannondoyle": "loversatthegunclub", "stingsdeadstoryofthesaddeathofthewellknownsinger": "stingsdead", "sextouriststory": "sextourist", "whenamandieswithjoshaw": "whenamandies", "poortounlosingmyvoice": "poortoun", "jackiesbaddepressionafunnystory": "jackiesbaddepression", "jackietalksaboutkielandhismother": "kielandhismother", "jackietalksaboutnorwegianprisoners": "norwegianprisoners"}

func songKey(s string) string {
	s = songPrefix.ReplaceAllString(s, "")
	s = songBrackets.ReplaceAllString(s, "")
	s = songSuffix.ReplaceAllString(s, "")
	s = strings.NewReplacer("é", "e", "è", "e", "á", "a", "à", "a", "ö", "o", "ü", "u", "ä", "a", "ø", "o", "ñ", "n", "ß", "ss").Replace(strings.ToLower(s))
	s = nonSong.ReplaceAllString(s, "")
	if a := songAliases[s]; a != "" {
		return a
	}
	return s
}
func (c *request) videos(title string) []any {
	v := get(c.app.data.Values["youtube-titel"], songKey(title))
	if v == nil {
		return nil
	}
	if a, ok := v.([]any); ok {
		return a
	}
	return []any{v}
}
func videoID(raw string) string {
	u, err := url.Parse(raw)
	if err != nil {
		return ""
	}
	switch strings.ToLower(u.Host) {
	case "youtu.be":
		return strings.Trim(u.Path, "/")
	case "youtube.com", "www.youtube.com":
		return u.Query().Get("v")
	}
	return ""
}
func (c *request) versionPlace(v any) string {
	if m, ok := get(v, "label").(M); ok {
		return str(coalesce(m[c.lang], m["en"]))
	}
	return str(get(v, "label"))
}
func versionTooltip(v any) string {
	out := []string{"Listen on YouTube", str(get(v, "title"))}
	if truth(get(v, "album")) {
		out = append(out, str(get(v, "album")))
	}
	if get(v, "kind") == "live" {
		s := "Live"
		if label := get(v, "label"); label != nil {
			if m, ok := label.(M); ok {
				label = m["en"]
			}
			s += ", " + str(label)
		}
		out = append(out, s)
	}
	out = append(out, str(get(v, "channel")))
	return strings.Join(out, " · ")
}
func (c *request) liveVideos(id string) []any {
	songs := map[string]bool{}
	for _, l := range listValue(get(c.releaseDetails(id), "tracklists")) {
		for _, t := range listValue(get(l, "tracks")) {
			songs[songKey(str(get(t, "title")))] = true
		}
	}
	var out []any
	for _, p := range pairs(c.app.data.Values["live-videos"]) {
		v := p.Value
		if get(v, "source") != "official" && !c.app.fanVideos {
			continue
		}
		own := contains(get(v, "releases"), id)
		var selected []any
		for _, video := range listValue(get(v, "videos")) {
			if get(video, "embeddable") != true || !truth(get(video, "checked")) {
				continue
			}
			for _, song := range listValue(get(video, "songs")) {
				if own || songs[songKey(str(get(song, "title")))] {
					m := cloneMap(song)
					m["video"] = video
					selected = append(selected, m)
				}
			}
		}
		if len(selected) > 0 {
			m := cloneMap(v)
			m["name"] = p.Key
			m["stuecke"] = selected
			out = append(out, m)
		}
	}
	sort.SliceStable(out, func(i, j int) bool { return str(get(out[i], "date")) < str(get(out[j], "date")) })
	return out
}
func weight(q any) int {
	return map[string]int{"weitere": 0, "verzeichnis": 1, "auswahl": 2}[str(get(q, "stufe"))]
}
func sourcePage(q any) bool { return get(q, "stufe") != "weitere" }
func (c *request) sourceIndex(id string) int {
	i := find(c.app.data.Sources, "id", id)
	if i >= 0 && sourcePage(c.app.data.Sources[i]) {
		return i
	}
	return -1
}
func (c *request) sourceField(q any, field string) string {
	if field == "titel" && c.lang != "de" && get(get(q, "en"), "titel") == nil && strings.HasPrefix(str(get(q, "titel")), "[") {
		return c.tr("stimmen.kategorie."+str(get(q, "kategorie"))) + " · " + str(get(q, "medium"))
	}
	v := get(q, field)
	if c.lang == "en" && get(get(q, "en"), field) != nil {
		v = get(get(q, "en"), field)
	}
	s := str(v)
	if field == "titel" {
		s = strings.NewReplacer("[", "", "]", "").Replace(s)
	}
	return s
}
func (c *request) sourceTitleLanguage(q any) string {
	if strings.HasPrefix(str(get(q, "titel")), "[") {
		if c.lang == "de" || get(get(q, "en"), "titel") != nil {
			return c.lang
		}
		return "en"
	}
	if c.lang == "en" && get(get(q, "en"), "titel") != nil {
		return "en"
	}
	return str(get(q, "sprache"))
}
func (c *request) sourceText(v any) []any {
	if t := get(v, c.lang); truth(t) {
		return []any{t, c.lang}
	}
	if c.lang == "de" {
		return []any{get(v, "de"), "de"}
	}
	return []any{nil, c.lang}
}
func (c *request) sourceTarget(q any) string {
	if sourcePage(q) {
		return c.url("quelle", M{"slug": get(q, "id")})
	}
	if get(q, "zugang") == "archiv" && truth(get(q, "archiv")) {
		return str(get(q, "archiv"))
	}
	if truth(get(q, "url")) {
		return str(get(q, "url"))
	}
	if truth(get(q, "archiv")) {
		return str(get(q, "archiv"))
	}
	return c.url("stimmen") + "#" + str(get(q, "id"))
}
func sourceMatches(q any, f any) bool {
	if weight(q) < num(get(f, "auswahl")) {
		return false
	}
	if get(f, "art") != nil && get(q, "kategorie") != get(f, "art") {
		return false
	}
	if get(f, "zugang") != nil && get(q, "zugang") != get(f, "zugang") {
		return false
	}
	if lang := get(f, "sprache"); lang != nil {
		s := get(q, "sprache")
		if s == "nn" {
			s = "no"
		}
		if lang == "andere" {
			return !contains([]any{"en", "no", "de"}, s)
		}
		return s == lang
	}
	return true
}
func sourceFilter(q url.Values) M {
	f := M{"auswahl": "1"}
	for k, allowed := range map[string][]any{"art": categories, "sprache": {"en", "no", "de", "andere"}, "zugang": accesses, "auswahl": {"0", "1", "2"}} {
		if contains(allowed, q.Get(k)) {
			f[k] = q.Get(k)
		}
	}
	return f
}
func (c *request) sourceLicense(l any) M {
	name, path := "CC BY-NC 4.0", "by-nc"
	if get(l, "name") == "ccbyncnd" {
		name, path = "CC BY-NC-ND 4.0", "by-nc-nd"
	}
	return M{"name": name, "url": "https://creativecommons.org/licenses/" + path + "/4.0/deed." + c.lang}
}
