package site

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"

	"jackieleven/internal/searchclient"
)

type searchHitView struct {
	searchclient.Hit
	PassageURL   string
	OriginalURL  string
	MetadataText string
}
type searchView struct {
	Lang, BasePath, Action, OtherURL     string
	Q, TargetLang, Mode, Voice, From, To string
	Rerank, Configured                   bool
	L                                    map[string]string
	Error                                string
	Manifest                             searchclient.Manifest
	Result                               *searchclient.SearchResponse
	Hits                                 []searchHitView
	Passage                              *searchHitView
	Versions                             searchclient.Versions
}

func searchLabels(lang string) map[string]string {
	labels := map[string]string{
		"Title": "Archivsuche|Archive search", "Home": "Zur Startseite|Home", "Intro": "Texte aus dem Jackie-Leven-Archiv durchsuchen. Die Textstimme bezeichnet den Autor des angezeigten Texts; die Quellenstimme den Autor des zugrunde liegenden Dokuments.|Search texts from the Jackie Leven archive. Text voice identifies the author of the displayed text; source voice identifies the author of the underlying document.",
		"Query": "Suchanfrage|Search query", "Submit": "Suchen|Search", "Language": "Sprache der Zielseiten|Destination language", "Mode": "Suchmodus|Search mode", "Voice": "Textstimme|Text voice", "All": "Alle|All", "Editorial": "Redaktion|Editorial", "ThirdParty": "Dritte|Third party", "Leven": "Jackie Leven|Jackie Leven", "Pastiche": "Pastiche (erfundene Stimme)|Pastiche (fictional voice)",
		"From": "Erscheinungsjahr von|Publication year from", "To": "bis|to", "YearHint": "Die Jahresfilter beziehen sich auf das Erscheinungsjahr des Dokuments, nicht auf das Datum eines erwähnten Konzerts.|Year filters refer to the document’s publication year, not the date of a concert mentioned in it.", "Rerank": "Reranking anfragen (optional)|Request reranking (optional)",
		"Privacy": "Semantische und hybride Suche senden den Suchtext an DeepInfra; Reranking zusätzlich die gefundenen Textauszüge. Rein lexikalische Suche ohne Reranking bleibt lokal. Suchanfragen stehen in der Seitenadresse und können im Browserverlauf gespeichert werden.|Semantic and hybrid search send your query to DeepInfra; reranking also sends retrieved excerpts. Lexical search without reranking stays local. Queries appear in the page address and may be saved in your browser history.", "Initial": "Eine Suchanfrage eingeben, um Textstellen zu finden.|Enter a query to find passages.", "Empty": "Keine Textstellen für diese Anfrage gefunden.|No passages found for this query.", "Count": "Angezeigte Treffer|Displayed hits", "ActualMode": "Verwendeter Modus|Mode used", "Degraded": "Rückfallbetrieb|Fallback", "Reason": "Grund|Reason", "Yes": "ja|yes", "No": "nein|no", "Reranked": "Reranking verwendet|Reranking used", "Duration": "Suchdauer|Search duration", "Snapshot": "Inhaltsstand|Content version", "Release": "Suchdienst-Version|Search release",
		"SourceVoice": "Quellenstimme|Source voice", "TextVoice": "Textstimme|Text voice", "TextKind": "Textart|Text kind", "TextLanguage": "Textsprache|Text language", "OpenPassage": "Gespeicherte Textstelle lesen|Read stored passage", "Original": "Originalseite öffnen|Open original page", "NoOriginal": "Keine sichere Originaladresse verfügbar.|No safe original address available.", "Passage": "Gespeicherte Textstelle|Stored passage", "PassageIntro": "Hier steht der vollständig gespeicherte Text dieser Textstelle im angezeigten Inhaltsstand. Der Link zur Originalseite führt zum Dokument.|This is the complete stored text of this passage in the content version shown. The original-page link opens the document.", "Back": "Zur Suche|Back to search", "Metadata": "Weitere Metadaten|Additional metadata", "Identifier": "Textstellenkennung|Passage ID", "Document": "Dokumentkennung|Document ID", "Excerpt": "Trefferauszug|Result excerpt", "Examples": "Beispiele|Examples",
	}
	for k, value := range labels {
		parts := strings.SplitN(value, "|", 2)
		labels[k] = parts[0]
		if lang == "en" {
			labels[k] = parts[1]
		}
	}
	return labels
}
func searchMessage(lang, de, en string) string {
	if lang == "en" {
		return en
	}
	return de
}

func (a *App) serveSearch(w http.ResponseWriter, r *http.Request) bool {
	lang, passage := "", false
	switch r.URL.EscapedPath() {
	case "/de/suche", "/de/suche-test":
		lang = "de"
	case "/en/search", "/en/search-test":
		lang = "en"
	case "/de/suche/textstelle":
		lang = "de"
		passage = true
	case "/en/search/passage":
		lang = "en"
		passage = true
	default:
		return false
	}
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Robots-Tag", "noindex, nofollow")
	w.Header().Set("Referrer-Policy", "no-referrer")
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Content-Language", lang)
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "default-src 'none'; style-src 'self' 'unsafe-inline'; img-src 'self'; font-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
	v := searchView{Lang: lang, BasePath: a.basePath, L: searchLabels(lang), TargetLang: lang, Mode: "hybrid", Configured: a.search != nil}
	if lang == "de" {
		v.Action = a.basePath + "/de/suche"
		v.OtherURL = a.basePath + "/en/search"
	} else {
		v.Action = a.basePath + "/en/search"
		v.OtherURL = a.basePath + "/de/suche"
	}
	if !passage {
		v.Action = a.basePath + r.URL.EscapedPath()
	}
	status := http.StatusOK
	if a.search != nil {
		v.Manifest = a.search.Manifest()
	}
	if r.Method != http.MethodGet && r.Method != http.MethodHead {
		w.Header().Set("Allow", "GET, HEAD")
		v.Error = searchMessage(lang, "Diese Seite unterstützt nur GET und HEAD.", "This page only supports GET and HEAD.")
		status = http.StatusMethodNotAllowed
	} else if len(r.URL.RawQuery) > 8192 {
		v.Error = searchMessage(lang, "Die Anfrage ist zu lang.", "The request is too long.")
		status = 400
	} else {
		values, err := url.ParseQuery(r.URL.RawQuery)
		if err == nil {
			for _, values := range values {
				if len(values) != 1 {
					err = errors.New("duplicate parameter")
					break
				}
			}
		}
		if err != nil {
			v.Error = searchMessage(lang, "Ungültige Anfrageparameter.", "Invalid request parameters.")
			status = 400
		} else {
			v.Q = values.Get("q")
			v.Voice = values.Get("voice")
			v.From = values.Get("from")
			v.To = values.Get("to")
			v.Rerank = values.Get("rerank") == "1"
			if values.Get("lang") != "" {
				v.TargetLang = values.Get("lang")
			}
			if values.Get("mode") != "" {
				v.Mode = values.Get("mode")
			}
			err = validateSearchValues(values, passage)
			if err != nil {
				v.Error = searchMessage(lang, "Ungültige Filter: höchstens 1024 UTF-8-Bytes ohne Steuerzeichen, Sprache de/en, ein gültiger Modus und Erscheinungsjahre von 1 bis 9999 in aufsteigender Reihenfolge.", "Invalid filters: use at most 1024 UTF-8 bytes without control characters, language de/en, a valid mode, and publication years from 1 to 9999 in ascending order.")
				status = 400
			} else if a.search == nil {
				v.Error = searchMessage(lang, "Die lokale Suche ist noch nicht eingerichtet.", "Local search has not been configured yet.")
				status = 503
			} else if passage {
				var result *searchclient.PassageResponse
				result, err = a.search.Passage(r.Context(), values.Get("id"), v.TargetLang)
				if err == nil {
					hit := a.searchHit(result.Passage, lang, v.TargetLang)
					v.Passage = &hit
					v.Versions = result.Versions
				}
			} else if strings.TrimSpace(v.Q) != "" {
				values.Set("lang", v.TargetLang)
				values.Set("mode", v.Mode)
				v.Result, err = a.search.Search(r.Context(), values)
				if err == nil {
					for _, hit := range v.Result.Hits {
						v.Hits = append(v.Hits, a.searchHit(hit, lang, v.TargetLang))
					}
				}
			}
			if err != nil && v.Error == "" {
				status, v.Error = searchError(lang, err)
			}
		}
	}
	name := "search.gohtml"
	if passage {
		name = "search-passage.gohtml"
	}
	var body bytes.Buffer
	view, err := a.templates.Clone()
	if err != nil {
		http.Error(w, "Rendering unavailable", 500)
		return true
	}
	if err := view.ExecuteTemplate(&body, name, v); err != nil {
		http.Error(w, "Rendering unavailable", 500)
		return true
	}
	w.WriteHeader(status)
	if r.Method != http.MethodHead {
		_, _ = w.Write(body.Bytes())
	}
	return true
}

func validateSearchValues(v url.Values, passage bool) error {
	invalid := errors.New("invalid query")
	for _, key := range []string{"q", "id", "lang", "voice", "mode", "from", "to", "rerank"} {
		value := v.Get(key)
		if !utf8.ValidString(value) || strings.IndexFunc(value, unicode.IsControl) >= 0 {
			return invalid
		}
	}
	if len(v.Get("q")) > searchclient.MaxQueryBytes {
		return invalid
	}
	if passage && (v.Get("id") == "" || len(v.Get("id")) > 1024) {
		return invalid
	}
	switch v.Get("lang") {
	case "", "de", "en":
	default:
		return invalid
	}
	switch v.Get("mode") {
	case "", "lexical", "semantic", "hybrid":
	default:
		return invalid
	}
	switch v.Get("voice") {
	case "", "editorial", "third_party", "leven", "pastiche":
	default:
		return invalid
	}
	switch v.Get("rerank") {
	case "", "0", "1":
	default:
		return invalid
	}
	var years [2]int
	for i, key := range []string{"from", "to"} {
		if v.Get(key) != "" {
			n, err := strconv.Atoi(v.Get(key))
			if err != nil || n < 1 || n > 9999 {
				return invalid
			}
			years[i] = n
		}
	}
	if years[0] > 0 && years[1] > 0 && years[0] > years[1] {
		return invalid
	}
	return nil
}
func searchError(lang string, err error) (int, string) {
	var api *searchclient.Error
	if !errors.As(err, &api) {
		return 503, searchMessage(lang, "Die Suche ist vorübergehend nicht erreichbar. Bitte erneut versuchen.", "Search is temporarily unavailable. Please try again.")
	}
	switch api.Status {
	case 400:
		return 400, searchMessage(lang, "Die Suche hat die Anfrage als ungültig zurückgewiesen.", "Search rejected the request as invalid.")
	case 404:
		return 404, searchMessage(lang, "Diese Textstelle ist in diesem Inhaltsstand nicht vorhanden.", "This passage does not exist in this content version.")
	case 409:
		return 409, searchMessage(lang, "Website und Suchdienst verwenden unterschiedliche Inhaltsstände. Beide müssen mit demselben Suchmanifest gestartet werden.", "The website and search service use different content versions. Both must start with the same search manifest.")
	case 429:
		return 429, searchMessage(lang, "Die Suche ist gerade ausgelastet. Bitte später erneut versuchen.", "Search is busy. Please try again later.")
	default:
		return 503, searchMessage(lang, "Die Suche konnte nicht abgeschlossen werden. Bitte erneut versuchen.", "Search could not be completed. Please try again.")
	}
}
func (a *App) searchHit(hit searchclient.Hit, lang, targetLang string) searchHitView {
	path := "/de/suche/textstelle"
	if lang == "en" {
		path = "/en/search/passage"
	}
	metadata := ""
	if len(hit.Metadata) > 0 && string(hit.Metadata) != "null" && string(hit.Metadata) != "{}" {
		var value any
		if json.Unmarshal(hit.Metadata, &value) == nil {
			var b bytes.Buffer
			enc := json.NewEncoder(&b)
			enc.SetEscapeHTML(false)
			enc.SetIndent("", "  ")
			if enc.Encode(value) == nil {
				metadata = b.String()
			}
		}
	}
	return searchHitView{Hit: hit, PassageURL: a.basePath + path + "?" + url.Values{"id": {hit.ID}, "lang": {targetLang}}.Encode(), OriginalURL: searchOriginalURL(a.basePath, hit.URL), MetadataText: metadata}
}

// URLs from the search service remain untrusted. Reject relative authorities,
// encoded traversal/separators and controls before adding the deployment mount.
func searchOriginalURL(basePath, raw string) string {
	if len(raw) > 4096 || !strings.HasPrefix(raw, "/") || strings.HasPrefix(raw, "//") {
		return ""
	}
	u, err := url.Parse(raw)
	if err != nil || u.IsAbs() || u.Host != "" || u.User != nil {
		return ""
	}
	if strings.Contains(u.Path, "\\") || strings.IndexFunc(raw, unicode.IsControl) >= 0 || strings.IndexFunc(u.Path, unicode.IsControl) >= 0 || strings.HasPrefix(u.Path, "//") {
		return ""
	}
	// Decode nested escapes too; every successful pass shortens the bounded path.
	path := u.Path
	for {
		for _, part := range strings.Split(path, "/") {
			if part == ".." || part == "." {
				return ""
			}
		}
		if strings.HasPrefix(path, "//") || strings.Contains(path, "\\") || strings.IndexFunc(path, unicode.IsControl) >= 0 {
			return ""
		}
		decoded, err := url.PathUnescape(path)
		if err != nil || decoded == path {
			break
		}
		path = decoded
	}
	target := basePath + u.EscapedPath()
	if u.RawQuery != "" {
		target += "?" + u.RawQuery
	}
	if u.Fragment != "" {
		target += "#" + u.EscapedFragment()
	}
	return target
}
