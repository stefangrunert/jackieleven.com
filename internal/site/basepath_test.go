package site

import (
	"html"
	"net/http/httptest"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

func mountedTestApp(t *testing.T) *App {
	t.Helper()
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	app, err := New(Config{Root: root, BasePath: "/jackieleven/", Contact: ContactConfig{StateDir: t.TempDir()}})
	if err != nil {
		t.Fatal(err)
	}
	return app
}

func TestBasePathValidation(t *testing.T) {
	for _, path := range []string{"/jackieleven", "/previews/jackie-v2", "/jackie_2/"} {
		if _, err := normalizeBasePath(path); err != nil {
			t.Error(err)
		}
	}
	for _, path := range []string{"jackie", "//host", "/a//b", "/a/../b", "/a/%2f", "/a?b", "/a#b", "/a\nb", "https://host/path"} {
		if _, err := normalizeBasePath(path); err == nil {
			t.Errorf("accepted invalid mount %q", path)
		}
	}
	for _, path := range []string{"", "/"} {
		if got, err := normalizeBasePath(path); err != nil || got != "" {
			t.Errorf("%q: %q %v", path, got, err)
		}
	}
}

func TestBasePathRoutingAndContact(t *testing.T) {
	a := mountedTestApp(t)
	for _, tc := range []struct {
		path     string
		status   int
		location string
	}{
		{"/jackieleven", 301, "/jackieleven/"}, {"/jackieleven?x=1", 301, "/jackieleven/?x=1"}, {"/jackieleven/", 302, "/jackieleven/de/"},
		{"/jackieleven/de", 301, "/jackieleven/de/"}, {"/jackieleven/station/1983-der-ueberfall", 301, "/jackieleven/de/zeitreise/1983-caledonian-road"},
		{"/jackieleven//de///ueber//", 301, "/jackieleven/de/ueber"}, {"/jackieleven/de//ueber", 200, ""},
		{"/de/", 404, ""}, {"/assets/css/site.css", 404, ""}, {"/jackieleven-other/de/", 404, ""}, {"/jackieleven/assets/../app/bootstrap.php", 404, ""},
		{"/jackieleven/internal/site/contact.go", 404, ""}, {"/jackieleven/assets/../data/stationen.json", 404, ""},
	} {
		r := httptest.NewRequest("GET", tc.path, nil)
		w := httptest.NewRecorder()
		a.ServeHTTP(w, r)
		if w.Code != tc.status || w.Header().Get("Location") != tc.location {
			t.Errorf("%s: got%d %q", tc.path, w.Code, w.Header().Get("Location"))
		}
	}
	w := httptest.NewRecorder()
	r := httptest.NewRequest("GET", "https://unpubli.sh/jackieleven/de/mitmachen", nil)
	a.ServeHTTP(w, r)
	cookies := w.Result().Cookies()
	if len(cookies) != 1 || cookies[0].Path != "/jackieleven/" {
		t.Fatalf("cookie scope: %v", cookies)
	}
	if !strings.Contains(w.Body.String(), `action="/jackieleven/de/mitmachen#nachricht"`) {
		t.Fatal("contact action escaped mount")
	}
	post := httptest.NewRequest("POST", "https://unpubli.sh/jackieleven/de/mitmachen", strings.NewReader("token=invalid"))
	post.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	post.AddCookie(cookies[0])
	w = httptest.NewRecorder()
	a.ServeHTTP(w, post)
	if w.Code != 400 {
		t.Errorf("mounted POST status=%d", w.Code)
	}
}

func TestMountedProductionIdentityAndFragments(t *testing.T) {
	a := mountedTestApp(t)
	for _, host := range []string{"unpubli.sh", "jackieleven.com"} {
		r := httptest.NewRequest("GET", "/jackieleven/de/zeitreise/1950-kirkcaldy", nil)
		r.Host = host
		w := httptest.NewRecorder()
		a.ServeHTTP(w, r)
		body := html.UnescapeString(w.Body.String())
		for _, want := range []string{`rel="canonical" href="https://jackieleven.com/de/zeitreise/1950-kirkcaldy"`, `hreflang="en" href="https://jackieleven.com/en/timeline/1950-kirkcaldy"`, `"de":"/jackieleven/de/zeitreise/1950-kirkcaldy"`, `data-canonical-alternativen=`, `"de":"/de/zeitreise/1950-kirkcaldy"`} {
			if !strings.Contains(body, want) {
				t.Errorf("%s missing %s", host, want)
			}
		}
		if strings.Contains(body, "https://jackieleven.com/jackieleven/") || strings.Contains(body, "cloudflareinsights.com") || w.Header().Get("X-Robots-Tag") != "noindex" {
			t.Errorf("preview identity leaked: %s", host)
		}
	}
	w := httptest.NewRecorder()
	a.ServeHTTP(w, httptest.NewRequest("GET", "/jackieleven/de/zeitreise/1950-kirkcaldy?fragment=1", nil))
	if w.Code != 200 || w.Header().Get("Link") != `<https://jackieleven.com/de/zeitreise/1950-kirkcaldy>; rel="canonical"` || !strings.Contains(w.Body.String(), `src="/jackieleven/assets/`) {
		t.Fatal("fragment routing or canonical changed")
	}
	for _, path := range []string{"/robots.txt", "/sitemap.xml"} {
		w = httptest.NewRecorder()
		a.ServeHTTP(w, httptest.NewRequest("GET", "/jackieleven"+path, nil))
		if w.Code != 200 || w.Header().Get("X-Robots-Tag") != "noindex" || strings.Contains(w.Body.String(), "https://jackieleven.com/jackieleven/") {
			t.Errorf("bad mounted discovery endpoint%s", path)
		}
		if path == "/robots.txt" && w.Body.String() != "User-agent: *\nDisallow: /\n" {
			t.Error("preview crawl policy changed")
		}
	}
}

// Exercise every public route and chapter: no internal link, local image,
// stylesheet, script or form may silently escape to the host's unrelated site.
func TestMountedAllContentURLsStayInsideMount(t *testing.T) {
	a := mountedTestApp(t)
	c := &request{app: a, lang: "de"}
	paths := []string{}
	loc := regexp.MustCompile(`<loc>https://jackieleven\.com([^<]+)</loc>`)
	for _, m := range loc.FindAllStringSubmatch(c.sitemap(), -1) {
		paths = append(paths, html.UnescapeString(m[1]))
	}
	for _, l := range []string{"de", "en"} {
		for _, chapter := range listValue(a.data.Values["pastiche"]) {
			paths = append(paths, c.routePath("kapitel", M{"slug": get(chapter, "slug")}, l))
		}
	}
	attributes := regexp.MustCompile(`(?:href|src|action|data-youtube-preview)="(/[^\"]*)"`)
	assets := map[string]bool{}
	for _, path := range paths {
		w := httptest.NewRecorder()
		a.ServeHTTP(w, httptest.NewRequest("GET", "https://unpubli.sh/jackieleven"+path, nil))
		if w.Code != 200 {
			t.Errorf("%s: status%d", path, w.Code)
			continue
		}
		body := w.Body.String()
		if strings.Contains(body, "ZgotmplZ") {
			t.Errorf("unsafe template placeholder on%s", path)
		}
		for _, m := range attributes.FindAllStringSubmatch(body, -1) {
			target := html.UnescapeString(m[1])
			if !strings.HasPrefix(target, "/jackieleven/") {
				t.Errorf("%s escapes mount:%s", path, target)
			}
			if strings.HasPrefix(target, "/jackieleven/assets/") {
				assets[target] = true
			}
		}
	}
	if len(paths) < 500 || len(assets) < 10 {
		t.Fatalf("incomplete crawl: routes%d assets%d", len(paths), len(assets))
	}
	for path := range assets {
		w := httptest.NewRecorder()
		a.ServeHTTP(w, httptest.NewRequest("HEAD", path, nil))
		if w.Code != 200 {
			t.Errorf("mounted asset%s: %d", path, w.Code)
		}
	}
}
