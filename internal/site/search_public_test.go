package site

import (
	"encoding/json"
	"net/http"
	"net/url"
	"strings"
	"sync/atomic"
	"testing"
	"unicode/utf8"

	"jackieleven/internal/searchclient"
)

func publicHit(section, title string) searchclient.Hit {
	hit := testSearchHit()
	hit.ID = section + "#p1"
	hit.DocumentID = section
	hit.Title = title
	hit.Metadata = json.RawMessage(`{"section":"` + section + `","display_date":"1997-04-13 | 1997-04-05","place":"Bodø","image":"/assets/bilder/startseite/cover-mystery-of-love.png","event_status":"announced"}`)
	return hit
}
func TestPublicSearchForcesDiscoveryAndHidesTechnicalControls(t *testing.T) {
	var calls atomic.Int64
	a := newSearchTestApp(t, "/jackieleven", func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		q := r.URL.Query()
		for k, want := range map[string]string{"q": "Norwegen?", "mode": "hybrid", "rerank": "1", "grouped": "1", "section": "music", "voice": "leven", "from": "1990", "limit": "20"} {
			if q.Get(k) != want {
				t.Errorf("%s=%q want%q", k, q.Get(k), want)
			}
		}
		if q.Has("build_id") {
			t.Error("untrusted build forwarded")
		}
		_ = json.NewEncoder(w).Encode(searchclient.SearchResponse{Versions: testVersions(), Mode: "lexical", Degraded: true, Reason: "provider_private_error", Hits: []searchclient.Hit{publicHit("music", "The Mystery of Love")}})
	})
	w := searchRequest(a, "GET", "/jackieleven/de/suche")
	if w.Code != 200 || calls.Load() != 0 {
		t.Fatal("initial public form")
	}
	w = searchRequest(a, "GET", "/jackieleven/de/suche?q=Norwegen%3F&section=music&voice=leven&from=1990&mode=lexical&rerank=0&grouped=0&build_id=other")
	body := w.Body.String()
	if w.Code != 200 {
		t.Fatalf("public status%d body%s", w.Code, body)
	}
	for _, want := range []string{`<details class="discovery-refine">`, `name="section"`, `name="voice"`, `Platten und Musik`, `inhaltliche Suche ist gerade eingeschränkt`, `/jackieleven/assets/css/search.css`, `src="/jackieleven/assets/bilder/startseite/cover-mystery-of-love.png"`, `referrerpolicy="no-referrer"`, `DeepInfra`, `href="/jackieleven/de/suche/textstelle?id=music%23p1&amp;lang=de"`} {
		if !strings.Contains(body, want) {
			t.Errorf("missing%q", want)
		}
	}
	for _, bad := range []string{`name="mode"`, `name="rerank"`, `name="grouped"`, `content-1`, `provider_private_error`, `<details class="discovery-refine" open`, `mode=lexical`, `build_id=other`} {
		if strings.Contains(body, bad) {
			t.Errorf("technical data exposed %q", bad)
		}
	}
	start := strings.Index(body, `<details class="discovery-refine">`)
	end := strings.Index(body[start:], "</details>") + start
	for _, name := range []string{`name="section"`, `name="voice"`, `name="from"`, `name="to"`} {
		at := strings.Index(body, name)
		if at < start || at > end {
			t.Errorf("filter outside disclosure: %s", name)
		}
	}
	if !strings.Contains(body, `aria-label="Filter entfernen: Platten und Musik"`) {
		t.Fatal("active section not removable")
	}
	if !strings.Contains(body, `section=music`) {
		t.Fatal("missing section drilldown")
	}
	for k, want := range map[string]string{"Referrer-Policy": "no-referrer", "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"} {
		if w.Header().Get(k) != want {
			t.Errorf("header%s", k)
		}
	}
}
func TestPublicSearchExcludesFictionUntilExplicitFilter(t *testing.T) {
	a := newSearchTestApp(t, "", func(w http.ResponseWriter, r *http.Request) {
		bio := publicHit("biography", "FICTION MARKER")
		bio.TextVoice = "pastiche"
		disguised := publicHit("site", "ALSO FICTION")
		disguised.Metadata = json.RawMessage(`{"section":"site","fiction":true}`)
		_ = json.NewEncoder(w).Encode(searchclient.SearchResponse{Versions: testVersions(), Mode: "hybrid", Hits: []searchclient.Hit{publicHit("writing", "Real writing"), bio, disguised}})
	})
	for _, query := range []string{"?q=Jackie", "?q=Jackie&section=writing"} {
		body := searchRequest(a, "GET", "/en/search"+query).Body.String()
		if strings.Contains(body, "FICTION MARKER") || strings.Contains(body, "ALSO FICTION") {
			t.Fatal("fiction leaked into default results")
		}
		if !strings.Contains(body, "Real writing") {
			t.Fatal("real writing missing")
		}
	}
	for _, query := range []string{"?q=Jackie&section=biography", "?q=Jackie&voice=pastiche"} {
		w := searchRequest(a, "GET", "/en/search"+query)
		if w.Code != 200 || !strings.Contains(w.Body.String(), "FICTION MARKER") || !strings.Contains(w.Body.String(), "not an autobiographical source") {
			t.Fatal("explicit fiction not clearly marked")
		}
	}
}
func TestPublicEmptyAndInvalidFilters(t *testing.T) {
	var calls atomic.Int64
	a := newSearchTestApp(t, "", func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		_ = json.NewEncoder(w).Encode(searchclient.SearchResponse{Versions: testVersions(), Mode: "hybrid", Hits: []searchclient.Hit{}})
	})
	for _, route := range []string{"/de/suche", "/en/search"} {
		w := searchRequest(a, "GET", route+"?q=nomatch")
		if w.Code != 200 || !strings.Contains(w.Body.String(), `class="discovery-empty"`) {
			t.Fatal("missing honest empty result")
		}
	}
	before := calls.Load()
	for _, query := range []string{"q=x&section=bogus", "q=x&voice=source", "q=x&from=2000&to=1990", "q=x&q=y", "q=x%0Asecret"} {
		if w := searchRequest(a, "GET", "/de/suche?"+query); w.Code != 400 {
			t.Errorf("invalid public request%d", w.Code)
		}
	}
	if calls.Load() != before {
		t.Fatal("invalid public request reached upstream")
	}
}
func TestPublicImageAllowlistAndExcerpt(t *testing.T) {
	for _, raw := range []string{"//evil.test/a.png", "https://evil.test/a.png", "http://is1-ssl.mzstatic.com/a.jpg", "https://is1-ssl.mzstatic.com.evil.test/a.jpg", "https://user@is1-ssl.mzstatic.com/a.jpg", "https://is1-ssl.mzstatic.com:443/a.jpg", "/assets/../private.png", "/assets/%252e%252e/private.jpg", "data:image/svg+xml,bad", "/assets/x.svg", "https://is1-ssl.mzstatic.com/a.jpg?q=private"} {
		if got := safeSearchImage("/jackieleven", raw); got != "" {
			t.Errorf("unsafe image%s ->%s", raw, got)
		}
	}
	for raw, want := range map[string]string{"/assets/cover.jpg": "/jackieleven/assets/cover.jpg", "https://is1-ssl.mzstatic.com/a.jpg": "https://is1-ssl.mzstatic.com/a.jpg", "https://f4.bcbits.com/a.jpg": "https://f4.bcbits.com/a.jpg", "https://www.mig-music.de/a.jpg": "https://www.mig-music.de/a.jpg"} {
		if got := safeSearchImage("/jackieleven", raw); got != want {
			t.Errorf("safe image%s ->%s", raw, got)
		}
	}
	excerpt := searchExcerpt(strings.Repeat("Über Norwegen und Bodø. ", 30), 320)
	if !utf8.ValidString(excerpt) || len([]rune(excerpt)) > 321 || len([]rune(excerpt)) < 250 || !strings.HasSuffix(excerpt, "…") {
		t.Fatalf("bad excerpt%q", excerpt)
	}
}
func TestPublicEntityPreservesConflictingAssertions(t *testing.T) {
	raw := json.RawMessage(`{"id":"event/one","type":"Event","label":"Concert in Bodø","time":[{"statement_id":"s1","edtf_value":"1997-04-13","references":[{"document":"document/report","locator":"Newspaper 15 April","quote":"A <b>memorable</b> evening","evidence_type":"third_party"}]},{"statement_id":"s2","edtf_value":"[1997-04-05,1997-04-06]","certainty":"uncertain","note":"Earlier announcement"}],"performance_status":[{"status_value":"announced"},{"status_value":"took_place"}],"recorded_by":{"agent":"archive-research"}}`)
	a := newSearchTestApp(t, "/jackieleven", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/entities" || r.URL.Query().Get("id") != "event/one" || r.Header.Get("X-Archive-Content-Version") != "content-1" {
			t.Error("wrong entity request")
		}
		_ = json.NewEncoder(w).Encode(searchclient.EntityResponse{Versions: testVersions(), Entity: raw})
	})
	w := searchRequest(a, "GET", "/jackieleven/de/suche/objekt?id=event%2Fone")
	body := w.Body.String()
	for _, want := range []string{"Concert in Bodø", "1997-04-13", "[1997-04-05,1997-04-06]", "Unsicher", "Angekündigt", "Als stattgefunden belegt", `href="/jackieleven/de/suche/objekt?id=document%2Freport"`, `A &lt;b&gt;memorable&lt;/b&gt; evening`, `<details class="discovery-provenance">`, `archive-research`} {
		if !strings.Contains(body, want) {
			t.Errorf("entity missing%q", want)
		}
	}
	if w.Code != 200 || strings.Contains(body, "<b>memorable</b>") {
		t.Fatal("unsafe entity view")
	}
	if strings.Index(body, "1997-04-13") > strings.Index(body, `<details class="discovery-provenance">`) {
		t.Fatal("claims only visible in JSON")
	}
}
func TestSearchNavigationOnlyWhenConfigured(t *testing.T) {
	a := newSearchTestApp(t, "/jackieleven", func(http.ResponseWriter, *http.Request) {})
	for _, route := range []string{"/jackieleven/de/", "/jackieleven/en/"} {
		w := searchRequest(a, "GET", route)
		if w.Code != 200 || !strings.Contains(w.Body.String(), `class="site-search-link"`) || !strings.Contains(w.Body.String(), `class="home-search"`) || !strings.Contains(w.Body.String(), `/jackieleven/assets/css/search.css`) {
			t.Errorf("configured homepage%s", route)
		}
	}
	plain := testApp(t)
	w := searchRequest(plain, "GET", "/de/")
	if strings.Contains(w.Body.String(), `class="site-search-link"`) || strings.Contains(w.Body.String(), `class="home-search"`) {
		t.Fatal("search shown without config")
	}
}
func TestPublicSectionLinksRetainReadableFilters(t *testing.T) {
	values := url.Values{"q": {"a & b"}, "voice": {"leven"}, "from": {"1990"}, "mode": {"hybrid"}, "rerank": {"1"}, "grouped": {"1"}}
	a := &App{basePath: "/jackieleven"}
	v := publicSearchView{Lang: "en", Action: "/jackieleven/en/search"}
	groups := a.publicSearchGroups([]searchclient.Hit{publicHit("live", "Concert")}, &v, values, "en")
	u, err := url.Parse(groups[0].MoreURL)
	if err != nil {
		t.Fatal(err)
	}
	q := u.Query()
	if q.Get("section") != "live" || q.Get("q") != "a & b" || q.Get("voice") != "leven" || q.Get("from") != "1990" || q.Has("mode") || q.Has("rerank") || q.Has("grouped") {
		t.Fatal("bad drilldown params", q)
	}
}
