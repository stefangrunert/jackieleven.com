package site

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/url"
	"path"
	"strings"
	"unicode"
	"unicode/utf8"

	"jackieleven/internal/searchclient"
)

type publicSearchMetadata struct {
	Section     string `json:"section"`
	Image       string `json:"image"`
	DisplayDate string `json:"display_date"`
	Place       string `json:"place"`
	EventStatus string `json:"event_status"`
	RecordKind  string `json:"record_kind"`
	Fiction     bool   `json:"fiction"`
}
type publicSearchCard struct {
	searchHitView
	Section, Image, Excerpt, Date, Place, Kind, Status, Voice, SourceVoiceLabel string
	Fiction                                                                     bool
}
type publicSearchGroup struct {
	Key, Title, MoreURL string
	Cards               []publicSearchCard
}
type publicSearchOption struct{ Key, Label string }
type publicSearchFilter struct{ Label, RemoveURL string }
type publicSearchView struct {
	Lang, BasePath, Action, OtherURL, Q, Section, Voice, From, To, Error, Notice string
	L                                                                            map[string]string
	Options                                                                      []publicSearchOption
	Filters                                                                      []publicSearchFilter
	Groups                                                                       []publicSearchGroup
	Searched                                                                     bool
	Count                                                                        int
	Passage                                                                      *publicSearchCard
	Entity                                                                       *searchEntityView
	Versions                                                                     searchclient.Versions
}

func publicSearchPath(lang string) string {
	if lang == "en" {
		return "/en/search"
	}
	return "/de/suche"
}
func publicSearchLabels(lang string) map[string]string {
	l := searchLabels(lang)
	pairs := map[string][2]string{
		"Title": {"Suche", "Search"}, "Heading": {"Was möchtest du entdecken?", "What would you like to discover?"},
		"Intro":       {"Ein Lied, ein Ort, eine Erinnerung. Stell eine Frage und finde deinen Weg durch Jackies Welt.", "A song, a place, a memory. Ask a question and find your way through Jackie’s world."},
		"Placeholder": {"Zum Beispiel: Was verband Jackie mit Norwegen?", "For example: What connected Jackie with Norway?"},
		"Refine":      {"Suche eingrenzen", "Refine your search"}, "Area": {"Bereich", "Section"}, "Everywhere": {"Alle Bereiche", "All sections"},
		"FilterRemove": {"Filter entfernen", "Remove filter"}, "More": {"Mehr aus diesem Bereich", "More from this section"}, "Read": {"Weiterlesen", "Read more"},
		"Found": {"Fundstücke", "Discoveries"}, "Empty": {"Dazu haben wir noch nichts gefunden. Versuch es mit anderen Worten oder ohne Filter.", "We haven’t found anything for that yet. Try different words or remove a filter."},
		"DeepInfra": {"Diese Suche nutzt DeepInfra.", "This search uses DeepInfra."}, "PrivacyDetails": {"Was wird übermittelt?", "What is shared?"},
		"PublicPrivacy": {"Deine Frage und passende Textauszüge werden für die Suche an DeepInfra übermittelt. Gib keine vertraulichen Angaben ein. Die Frage steht außerdem in der Seitenadresse und kann im Browserverlauf bleiben.", "Your question and matching text excerpts are sent to DeepInfra to support the search. Please don’t enter confidential information. Your question also appears in the page address and may remain in your browser history."},
		"Fallback":      {"Die inhaltliche Suche ist gerade eingeschränkt. Wir zeigen dir die verfügbaren Treffer; ihre Auswahl oder Reihenfolge kann abweichen.", "The meaning-based search is currently limited. We’re showing the available results; their selection or order may differ."},
		"Fiction":       {"Literarische Fiktion", "Literary fiction"}, "FictionNote": {"Diese literarische Biografie ist eine erfundene Stimme. Sie ist keine autobiografische Quelle und kein Beleg für historische Tatsachen.", "This literary biography uses an invented voice. It is not an autobiographical source or evidence of historical facts."},
		"Provenance": {"Herkunft und Einzelheiten", "Sources and details"}, "Stored": {"Textstelle aus dem Archiv", "Passage from the archive"},
		"SourceNote":  {"Der folgende Text stammt aus dem gespeicherten Archivstand. Die Originalseite ist separat verlinkt.", "The text below comes from the stored archive version. The original page is linked separately."},
		"EntityTitle": {"Eintrag im Archiv", "Archive record"}, "Claims": {"Angaben und Belege", "Statements and sources"},
		"EntityNote": {"Das Archiv bewahrt die Angaben seiner Quellen einzeln. Abweichende Daten oder widersprüchliche Aussagen bleiben sichtbar.", "The archive preserves each source’s statements separately. Different dates and conflicting accounts remain visible."},
		"Evidence":   {"Belege anzeigen", "Show sources"}, "NoEvidence": {"Kein Belegverweis", "No source reference"}, "Recorded": {"Erfassung und Originaldaten", "Provenance and original data"},
		"About": {"Über diese Seite", "About this site"}, "ExamplesLabel": {"Vielleicht suchst du …", "You might ask …"},
		"Example1": {"Was verband Jackie mit Norwegen?", "What connected Jackie with Norway?"},
		"Example2": {"Welche Lieder handeln von Verlust?", "Which songs are about loss?"},
		"Example3": {"Was war Doll by Doll?", "What was Doll by Doll?"},
	}
	for k, p := range pairs {
		l[k] = searchMessage(lang, p[0], p[1])
	}
	return l
}
func publicSections(lang string) []publicSearchOption {
	return []publicSearchOption{
		{"music", searchMessage(lang, "Platten und Musik", "Records and music")},
		{"live", searchMessage(lang, "Konzerte und Orte", "Concerts and places")},
		{"timeline", searchMessage(lang, "Zeitreise", "Timeline")},
		{"writing", searchMessage(lang, "Jackies Texte", "Jackie’s writing")},
		{"press", searchMessage(lang, "Presse und Erinnerungen", "Press and memories")},
		{"biography", searchMessage(lang, "Literarische Biografie", "Literary biography")},
		{"site", searchMessage(lang, "Weitere Seiten", "Other pages")},
	}
}
func sectionLabel(section, lang string) string {
	for _, s := range publicSections(lang) {
		if s.Key == section {
			return s.Label
		}
	}
	return ""
}
func searchVoiceLabel(voice, lang string) string {
	switch voice {
	case "leven":
		return "Jackie Leven"
	case "editorial":
		return searchMessage(lang, "Redaktion", "Editorial")
	case "third_party":
		return searchMessage(lang, "Andere Stimmen", "Other voices")
	case "pastiche":
		return searchMessage(lang, "Erfundene Stimme", "Fictional voice")
	default:
		return voice
	}
}
func publicSearchHeaders(w http.ResponseWriter, lang string) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Robots-Tag", "noindex, nofollow")
	w.Header().Set("Referrer-Policy", "no-referrer")
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Content-Language", lang)
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'self'; img-src 'self' https://is1-ssl.mzstatic.com https://f4.bcbits.com https://www.mig-music.de; font-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
}
func (a *App) servePublicSearch(w http.ResponseWriter, r *http.Request) bool {
	lang, kind := "", "search"
	switch r.URL.EscapedPath() {
	case "/de/suche":
		lang = "de"
	case "/en/search":
		lang = "en"
	case "/de/suche/textstelle":
		lang = "de"
		kind = "passage"
	case "/en/search/passage":
		lang = "en"
		kind = "passage"
	case "/de/suche/objekt":
		lang = "de"
		kind = "entity"
	case "/en/search/entity":
		lang = "en"
		kind = "entity"
	default:
		return false
	}
	publicSearchHeaders(w, lang)
	other := "en"
	if lang == "en" {
		other = "de"
	}
	v := publicSearchView{Lang: lang, BasePath: a.basePath, Action: a.basePath + publicSearchPath(lang), OtherURL: a.basePath + publicSearchPath(other), L: publicSearchLabels(lang), Options: publicSections(lang)}
	status := 200
	values, err := url.ParseQuery(r.URL.RawQuery)
	invalid := err != nil || len(r.URL.RawQuery) > 8192
	for _, items := range values {
		if len(items) != 1 {
			invalid = true
		}
	}
	// Public callers cannot select provider modes or disable grouped retrieval.
	for _, key := range []string{"mode", "rerank", "grouped", "limit", "build_id"} {
		values.Del(key)
	}
	if !invalid {
		invalid = validateSearchValues(values, kind != "search") != nil
	}
	if section := values.Get("section"); section != "" && sectionLabel(section, lang) == "" {
		invalid = true
	}
	v.Q = values.Get("q")
	v.Section = values.Get("section")
	v.Voice = values.Get("voice")
	v.From = values.Get("from")
	v.To = values.Get("to")
	targetLang := lang
	if values.Get("lang") != "" {
		targetLang = values.Get("lang")
	}
	switch {
	case r.Method != "GET" && r.Method != "HEAD":
		w.Header().Set("Allow", "GET, HEAD")
		status = 405
		v.Error = searchMessage(lang, "Bitte verwende das Suchformular.", "Please use the search form.")
	case invalid:
		status = 400
		v.Error = searchMessage(lang, "Bitte prüfe deine Frage und die Filter. Die Frage darf höchstens 1024 UTF-8-Bytes enthalten; die Jahresangaben müssen aufsteigend sein.", "Please check your question and filters. The question may contain at most 1024 UTF-8 bytes, and the years must be in ascending order.")
	case a.search == nil:
		status = 503
		v.Error = searchMessage(lang, "Die Suche ist hier noch nicht verfügbar.", "Search is not available here yet.")
	case kind == "passage":
		response, e := a.search.Passage(r.Context(), values.Get("id"), targetLang)
		err = e
		if e == nil {
			card := a.publicSearchCard(response.Passage, lang, targetLang)
			v.Passage = &card
			v.Versions = response.Versions
		}
	case kind == "entity":
		response, e := a.search.Entity(r.Context(), values.Get("id"))
		err = e
		if e == nil {
			v.Entity = a.searchEntity(response.Entity, lang)
			v.Versions = response.Versions
		}
	case strings.TrimSpace(v.Q) != "":
		values.Set("lang", targetLang)
		values.Set("mode", "hybrid")
		values.Set("rerank", "1")
		values.Set("grouped", "1")
		response, e := a.search.Search(r.Context(), values)
		err = e
		if e == nil {
			v.Searched = true
			if response.Degraded {
				v.Notice = v.L["Fallback"]
			}
			v.Groups = a.publicSearchGroups(response.Hits, &v, values, targetLang)
			for _, group := range v.Groups {
				v.Count += len(group.Cards)
			}
		}
	}
	if err != nil && v.Error == "" {
		status, v.Error = searchError(lang, err)
		if status == 404 && kind == "entity" {
			v.Error = searchMessage(lang, "Dieser Eintrag ist in diesem Archivstand nicht vorhanden.", "This record does not exist in this archive version.")
		}
		if status == 409 {
			v.Error = searchMessage(lang, "Das Archiv wird gerade aktualisiert. Bitte versuche es gleich noch einmal.", "The archive is being updated. Please try again shortly.")
		}
	}
	v.Filters = publicSearchFilters(v, values)
	// Language switching preserves only readable search parameters or the record ID.
	alternate := publicSearchValues(values)
	alternate.Set("lang", other)
	if kind == "passage" {
		if other == "en" {
			v.OtherURL = a.basePath + "/en/search/passage"
		} else {
			v.OtherURL = a.basePath + "/de/suche/textstelle"
		}
		alternate = url.Values{"id": {values.Get("id")}, "lang": {other}}
	}
	if kind == "entity" {
		v.OtherURL = a.searchEntityURL(values.Get("id"), other)
		alternate = nil
	}
	if len(alternate) > 0 {
		v.OtherURL += "?" + alternate.Encode()
	}
	templateName := "search-public.gohtml"
	if kind != "search" {
		templateName = "search-reader.gohtml"
	}
	var body bytes.Buffer
	templates, e := a.templates.Clone()
	if e != nil {
		http.Error(w, "Rendering unavailable", 500)
		return true
	}
	if e = templates.ExecuteTemplate(&body, templateName, v); e != nil {
		http.Error(w, "Rendering unavailable", 500)
		return true
	}
	w.WriteHeader(status)
	if r.Method != "HEAD" {
		_, _ = w.Write(body.Bytes())
	}
	return true
}
func publicSearchValues(values url.Values) url.Values {
	result := url.Values{}
	for _, key := range []string{"q", "section", "voice", "from", "to", "lang"} {
		if value := values.Get(key); value != "" {
			result.Set(key, value)
		}
	}
	return result
}
func publicSearchFilters(v publicSearchView, values url.Values) []publicSearchFilter {
	var filters []publicSearchFilter
	for _, key := range []string{"section", "voice", "from", "to"} {
		value := values.Get(key)
		if value == "" {
			continue
		}
		label := value
		switch key {
		case "section":
			label = sectionLabel(value, v.Lang)
		case "voice":
			label = searchVoiceLabel(value, v.Lang)
		case "from":
			label = v.L["From"] + " " + value
		case "to":
			label = v.L["To"] + " " + value
		}
		q := publicSearchValues(values)
		q.Del(key)
		filters = append(filters, publicSearchFilter{label, v.Action + "?" + q.Encode()})
	}
	return filters
}
func (a *App) publicSearchGroups(hits []searchclient.Hit, v *publicSearchView, values url.Values, targetLang string) []publicSearchGroup {
	var groups []publicSearchGroup
	indices := map[string]int{}
	for _, hit := range hits {
		card := a.publicSearchCard(hit, v.Lang, targetLang)
		if card.Fiction && v.Section != "biography" && v.Voice != "pastiche" {
			continue
		}
		index, ok := indices[card.Section]
		if !ok {
			q := publicSearchValues(values)
			q.Set("section", card.Section)
			index = len(groups)
			indices[card.Section] = index
			groups = append(groups, publicSearchGroup{Key: card.Section, Title: sectionLabel(card.Section, v.Lang), MoreURL: v.Action + "?" + q.Encode()})
		}
		groups[index].Cards = append(groups[index].Cards, card)
	}
	return groups
}
func (a *App) publicSearchCard(hit searchclient.Hit, lang, targetLang string) publicSearchCard {
	var m publicSearchMetadata
	_ = json.Unmarshal(hit.Metadata, &m)
	if sectionLabel(m.Section, lang) == "" {
		m.Section = "site"
	}
	c := publicSearchCard{searchHitView: a.searchHit(hit, lang, targetLang), Section: m.Section, Image: safeSearchImage(a.basePath, m.Image), Excerpt: searchExcerpt(hit.Text, 320), Date: m.DisplayDate, Place: m.Place, Fiction: m.Fiction || m.Section == "biography" || hit.TextVoice == "pastiche", Voice: searchVoiceLabel(hit.TextVoice, lang), SourceVoiceLabel: searchVoiceLabel(hit.SourceVoice, lang)}
	switch hit.TextKind {
	case "summary":
		c.Kind = searchMessage(lang, "Redaktionelle Zusammenfassung", "Editorial summary")
	case "original", "quote", "quotation", "excerpt", "original_quote":
		c.Kind = searchMessage(lang, "Originalauszug", "Original excerpt")
	case "translation":
		c.Kind = searchMessage(lang, "Übersetzter Auszug", "Translated excerpt")
	default:
		if hit.TextVoice == "leven" {
			c.Kind = searchMessage(lang, "Jackies eigene Worte", "Jackie’s own words")
		}
	}
	if c.Fiction {
		c.Kind = searchMessage(lang, "Literarische Fiktion", "Literary fiction")
	}
	switch m.EventStatus {
	case "announced":
		c.Status = searchMessage(lang, "Angekündigt", "Announced")
	case "took_place":
		c.Status = searchMessage(lang, "Als stattgefunden belegt", "Documented as having taken place")
	case "cancelled":
		c.Status = searchMessage(lang, "Abgesagt", "Cancelled")
	case "mixed":
		c.Status = searchMessage(lang, "Unterschiedliche Quellenangaben", "Different accounts in the sources")
	case "unknown":
		c.Status = searchMessage(lang, "Durchführung ungeklärt", "Occurrence unconfirmed")
	}
	return c
}
func searchExcerpt(text string, limit int) string {
	text = strings.Join(strings.Fields(text), " ")
	runes := []rune(text)
	if len(runes) <= limit {
		return text
	}
	end := limit
	for end > limit-60 && !unicode.IsSpace(runes[end]) {
		end--
	}
	if end <= limit-60 {
		end = limit
	}
	return strings.TrimSpace(string(runes[:end])) + "…"
}
func safeSearchImage(basePath, raw string) string {
	if raw == "" || len(raw) > 4096 || !utf8.ValidString(raw) {
		return ""
	}
	u, err := url.Parse(raw)
	if err != nil || u.User != nil || u.Fragment != "" || strings.IndexFunc(raw, unicode.IsControl) >= 0 {
		return ""
	}
	if strings.HasPrefix(raw, "/assets/") {
		safe := searchOriginalURL(basePath, raw)
		ext := strings.ToLower(path.Ext(u.Path))
		switch ext {
		case ".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif":
			return safe
		}
		return ""
	}
	if u.Scheme != "https" || u.Port() != "" || u.RawQuery != "" {
		return ""
	}
	switch u.Host {
	case "is1-ssl.mzstatic.com", "f4.bcbits.com", "www.mig-music.de":
		return u.String()
	}
	return ""
}
