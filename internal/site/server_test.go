package site

import (
	"net/http/httptest"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

func testApp(t *testing.T) *App {
	t.Helper()
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	a, err := New(Config{Root: root, Contact: ContactConfig{StateDir: t.TempDir()}})
	if err != nil {
		t.Fatal(err)
	}
	return a
}
func TestRequestLanguageIsIsolated(t *testing.T) {
	a := testApp(t)
	var wg sync.WaitGroup
	for i := 0; i < 48; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			lang, path := "de", "/de/zeitreise"
			if i%2 == 1 {
				lang, path = "en", "/en/timeline"
			}
			if i%3 == 0 {
				path = "/" + lang + "/"
			}
			r := httptest.NewRequest("GET", path, nil)
			r.Host = "jackieleven.com"
			w := httptest.NewRecorder()
			a.ServeHTTP(w, r)
			body := w.Body.String()
			if w.Code != 200 || w.Header().Get("Content-Language") != lang || !strings.Contains(body, `<html lang="`+lang+`">`) || strings.Contains(body, "ZgotmplZ") {
				t.Errorf("%s status=%d language=%s", path, w.Code, w.Header().Get("Content-Language"))
			}
			if !strings.Contains(body, `href="https://jackieleven.com/`+lang+`/`) {
				t.Errorf("missing canonical for %s", path)
			}
		}(i)
	}
	wg.Wait()
}
func TestHTTPBoundaryAndCanonicalization(t *testing.T) {
	a := testApp(t)
	for _, tc := range []struct {
		path     string
		status   int
		location string
	}{{"/", 302, "/de/"}, {"/de", 301, "/de/"}, {"/de//ueber", 200, ""}, {"//de///ueber//", 301, "/de/ueber"}, {"/app/config.local.php", 404, ""}, {"/data/stationen.json", 404, ""}, {"/templates/layout.gohtml", 404, ""}, {"/assets/../app/bootstrap.php", 404, ""}, {"/assets/.secret", 404, ""}, {"/de%2Fueber", 404, ""}} {
		r := httptest.NewRequest("GET", tc.path, nil)
		w := httptest.NewRecorder()
		a.ServeHTTP(w, r)
		if w.Code != tc.status || w.Header().Get("Location") != tc.location {
			t.Errorf("%s: %d %q", tc.path, w.Code, w.Header().Get("Location"))
		}
	}
	r := httptest.NewRequest("HEAD", "/de/", nil)
	w := httptest.NewRecorder()
	a.ServeHTTP(w, r)
	if w.Code != 200 || w.Body.Len() != 0 {
		t.Errorf("HEAD: %d body=%d", w.Code, w.Body.Len())
	}
}
func TestCanonicalOriginDoesNotTrustHost(t *testing.T) {
	a := testApp(t)
	r := httptest.NewRequest("GET", "/en/", nil)
	r.Host = "attacker.example"
	w := httptest.NewRecorder()
	a.ServeHTTP(w, r)
	if strings.Contains(w.Body.String(), "attacker.example") || w.Header().Get("X-Robots-Tag") != "noindex" {
		t.Fatal("untrusted origin used")
	}
	if !strings.Contains(w.Body.String(), `rel="canonical" href="https://jackieleven.com/en/"`) {
		t.Fatal("missing canonical")
	}
}
