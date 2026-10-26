package site

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"

	"jackieleven/internal/searchclient"
)

func newSearchTestApp(t *testing.T, basePath string, h http.HandlerFunc) *App {
	t.Helper()
	s := httptest.NewServer(h)
	t.Cleanup(s.Close)
	p := filepath.Join(t.TempDir(), "manifest.json")
	if err := os.WriteFile(p, []byte(`{"api_version":"v1","build_id":"build-1","content_version":"content-1","data_version":"data-1","embedding_profile":"none","passage_count":1,"document_count":1}`), 0600); err != nil {
		t.Fatal(err)
	}
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	a, err := New(Config{Root: root, BasePath: basePath, SearchURL: s.URL, SearchManifest: p, Contact: ContactConfig{StateDir: t.TempDir()}})
	if err != nil {
		t.Fatal(err)
	}
	return a
}
func searchRequest(a *App, method, path string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	a.ServeHTTP(w, httptest.NewRequest(method, path, nil))
	return w
}
func testVersions() searchclient.Versions {
	return searchclient.Versions{APIVersion: "v1", ContentVersion: "content-1", DataVersion: "data-1", SearchRelease: "search-1"}
}
func testSearchHit() searchclient.Hit {
	return searchclient.Hit{ID: "document#passage-1", DocumentID: "document", Title: `A <script>alert(1)</script> title`, Text: "Exact <b>stored</b> text\n\nSecond paragraph.", Language: "en", SourceVoice: "third_party", TextVoice: "editorial", TextKind: "summary", URL: "/en/voices/document", Metadata: json.RawMessage(`{"year":1999,"note":"<script>bad</script>"}`)}
}
func TestSearchSSRAndMountedPassage(t *testing.T) {
	var calls atomic.Int64
	a := newSearchTestApp(t, "/preview", func(w http.ResponseWriter, r *http.Request) {
		calls.Add(1)
		if r.Header.Get("X-Archive-Content-Version") != "content-1" {
			t.Error("snapshot not pinned")
		}
		if r.URL.Path == "/v1/passages" {
			if r.URL.Query().Get("id") != "document#passage-1" {
				t.Error("wrong passage ID")
			}
			_ = json.NewEncoder(w).Encode(searchclient.PassageResponse{Versions: testVersions(), Passage: testSearchHit()})
			return
		}
		q := r.URL.Query()
		for key, want := range map[string]string{"q": "Norwegen", "lang": "en", "mode": "hybrid", "voice": "editorial", "from": "1990", "to": "2000", "rerank": "1", "limit": "20"} {
			if q.Get(key) != want {
				t.Errorf("%s=%q want %q", key, q.Get(key), want)
			}
		}
		_ = json.NewEncoder(w).Encode(searchclient.SearchResponse{Versions: testVersions(), Mode: "lexical", Degraded: true, Reason: "embedding_off", DurationMS: 2.4, Hits: []searchclient.Hit{testSearchHit()}})
	})
	w := searchRequest(a, "GET", "/preview/de/suche-test")
	if w.Code != 200 || calls.Load() != 0 || !strings.Contains(w.Body.String(), `action="/preview/de/suche-test"`) {
		t.Fatalf("initial form: %d %d", w.Code, calls.Load())
	}
	w = searchRequest(a, "GET", "/preview/de/suche-test?q=Norwegen&lang=en&mode=hybrid&voice=editorial&from=1990&to=2000&rerank=1")
	body := w.Body.String()
	for _, want := range []string{`method="get"`, `value="Norwegen"`, `value="editorial" selected`, `lexical`, `embedding_off`, `2.4 ms`, `content-1`, `third_party`, `editorial`, `summary`, `/preview/de/suche/textstelle?id=document%23passage-1&amp;lang=en`, `A &lt;script&gt;alert(1)&lt;/script&gt; title`, `Exact &lt;b&gt;stored&lt;/b&gt; text`} {
		if !strings.Contains(body, want) {
			t.Errorf("missing %q", want)
		}
	}
	if w.Code != 200 || strings.Contains(body, "<script>") || strings.Contains(body, `href="/en/voices/document"`) {
		t.Fatalf("unsafe or failed result: %d", w.Code)
	}
	for key, want := range map[string]string{"Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Robots-Tag": "noindex, nofollow"} {
		if w.Header().Get(key) != want {
			t.Errorf("header %s=%s", key, w.Header().Get(key))
		}
	}
	w = searchRequest(a, "GET", "/preview/de/suche/textstelle?id=document%23passage-1&lang=en")
	body = w.Body.String()
	for _, want := range []string{`Exact &lt;b&gt;stored&lt;/b&gt; text`, "Second paragraph.", `href="/preview/en/voices/document"`, `document#passage-1`, `Weitere Metadaten`, `&lt;script&gt;bad&lt;/script&gt;`} {
		if !strings.Contains(body, want) {
			t.Errorf("reader missing %q", want)
		}
	}
	if w.Code != 200 || strings.Contains(body, "<script>") || strings.Contains(body, "ZgotmplZ") {
		t.Fatalf("reader: %d", w.Code)
	}
	w = searchRequest(a, "GET", "/preview/en/search/passage?id=document%23passage-1")
	if w.Code != 200 || !strings.Contains(w.Body.String(), "Stored passage") || w.Header().Get("Content-Language") != "en" {
		t.Fatal("English passage failed")
	}
}
func TestSearchEmptyErrorsAndMethods(t *testing.T) {
	var status atomic.Int64
	status.Store(200)
	a := newSearchTestApp(t, "", func(w http.ResponseWriter, r *http.Request) {
		if status.Load() != 200 {
			w.WriteHeader(int(status.Load()))
			_, _ = w.Write([]byte("upstream error with PRIVATE_DATA"))
			return
		}
		_ = json.NewEncoder(w).Encode(searchclient.SearchResponse{Versions: testVersions(), Mode: "hybrid", Hits: []searchclient.Hit{}})
	})
	for _, path := range []string{"/de/suche", "/de/suche-test", "/en/search", "/en/search-test"} {
		w := searchRequest(a, "GET", path+"?q=nomatch")
		if w.Code != 200 || (!strings.Contains(w.Body.String(), "Keine Textstellen") && !strings.Contains(w.Body.String(), "No passages found")) {
			t.Fatalf("empty %s: %d", path, w.Code)
		}
	}
	for _, code := range []int{400, 404, 409, 429, 503} {
		status.Store(int64(code))
		w := searchRequest(a, "GET", "/en/search?q=example")
		if w.Code != code || strings.Contains(w.Body.String(), "No passages found") || strings.Contains(w.Body.String(), "PRIVATE_DATA") || !strings.Contains(w.Body.String(), `role="alert"`) {
			t.Errorf("error %d rendered incorrectly", code)
		}
	}
	status.Store(200)
	w := searchRequest(a, "HEAD", "/en/search?q=example")
	if w.Code != 200 || w.Body.Len() != 0 || w.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("HEAD failed")
	}
	w = searchRequest(a, "POST", "/de/suche")
	if w.Code != 405 || w.Header().Get("Allow") != "GET, HEAD" {
		t.Fatal("POST not rejected")
	}
}
func TestSearchValidatesBeforeCallingService(t *testing.T) {
	var calls atomic.Int64
	a := newSearchTestApp(t, "", func(http.ResponseWriter, *http.Request) { calls.Add(1) })
	for _, query := range []string{"q=x&q=y", "q=%xx", "q=hello%0Aworld", "q=" + strings.Repeat("a", 1025), "q=x&mode=other", "q=x&lang=no", "q=x&voice=source", "q=x&from=2000&to=1990", "q=x&from=0", "q=x&to=10000", "q=x&rerank=true", "q=x&from=notyear", "q=" + strings.Repeat("x", 8193)} {
		w := searchRequest(a, "GET", "/de/suche?"+query)
		if w.Code != 400 {
			t.Errorf("invalid query status %d", w.Code)
		}
	}
	for _, path := range []string{"/de/suche/textstelle", "/en/search/passage?id=", "/en/search/passage?id=" + url.QueryEscape(strings.Repeat("x", 1025))} {
		if w := searchRequest(a, "GET", path); w.Code != 400 {
			t.Errorf("invalid passage: %d", w.Code)
		}
	}
	if calls.Load() != 0 {
		t.Fatal("invalid query reached service")
	}
}
func TestUnconfiguredSearchLeavesWebsiteWorking(t *testing.T) {
	a := testApp(t)
	if w := searchRequest(a, "GET", "/de/suche-test"); w.Code != 503 || !strings.Contains(w.Body.String(), "noch nicht eingerichtet") {
		t.Fatal("missing unconfigured notice")
	}
	for _, path := range []string{"/de/", "/en/", "/de/mitmachen"} {
		if w := searchRequest(a, "GET", path); w.Code != 200 {
			t.Errorf("normal page %s=%d", path, w.Code)
		}
	}
}
func TestSearchOriginalURLs(t *testing.T) {
	for _, raw := range []string{"https://evil.example/x", "//evil.example/x", "/%2Fevil.example/x", "/\\evil.example", "/foo/%2e%2e/bar", "/foo/../bar", "/foo/%252e%252e/bar", "/foo/%0dbar", "/foo\nbar", "javascript:alert(1)", "relative/path"} {
		if got := searchOriginalURL("/preview", raw); got != "" {
			t.Errorf("unsafe URL %q became %q", raw, got)
		}
	}
	for raw, want := range map[string]string{"/de/stimmen/quelle": "/preview/de/stimmen/quelle", "/en/pool/a?foo=bar#existing": "/preview/en/pool/a?foo=bar#existing", "/en/space%20name": "/preview/en/space%20name"} {
		if got := searchOriginalURL("/preview", raw); got != want {
			t.Errorf("safe URL %q=%q", raw, got)
		}
	}
}

func TestUnavailableSearchDoesNotBreakNormalPages(t *testing.T) {
	a := newSearchTestApp(t, "", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(503) })
	if w := searchRequest(a, "GET", "/en/search?q=example"); w.Code != 503 {
		t.Fatalf("unavailable search: %d", w.Code)
	}
	for _, path := range []string{"/de/", "/en/", "/de/mitmachen"} {
		if w := searchRequest(a, "GET", path); w.Code != 200 {
			t.Errorf("normal page %s=%d", path, w.Code)
		}
	}
}
