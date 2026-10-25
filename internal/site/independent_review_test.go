package site

import (
	"context"
	"io/fs"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// These checks were first run against an isolated reviewer copy. They exercise
// user-visible and privacy boundaries that are separate from implementation tests.
func TestIndependentPrivateResourcesStayPrivate(t *testing.T) {
	a := testApp(t)
	for _, path := range []string{
		"/.git/config", "/.dev/resend-api-key", "/.dev/ontologie.html",
		"/research/columns/2002-10_deep-pool_oktober-2002.md",
		"/autobiografie/01-prinlaws-boy.md", "/ops/go-release-files.json",
		"/assets/%2e%2e/data/quellen.json", "/assets/",
	} {
		t.Run(path, func(t *testing.T) {
			w := httptest.NewRecorder()
			a.ServeHTTP(w, httptest.NewRequest("GET", "http://local.test"+path, nil))
			if w.Code != 404 {
				t.Fatalf("private resource returned status %d", w.Code)
			}
		})
	}
}

func TestIndependentContactReflectsOnlyEscapedInput(t *testing.T) {
	a := testApp(t)
	post := url.Values{
		"token":     {"invalid-csrf-token"},
		"name":      {`"><script>alert(1)</script>`},
		"email":     {"test@example.test"},
		"nachricht": {`</textarea><script>alert(2)</script>`},
	}
	r := httptest.NewRequest("POST", "http://local.test/de/mitmachen", strings.NewReader(post.Encode()))
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	w := httptest.NewRecorder()
	a.ServeHTTP(w, r)
	if w.Code != 400 || w.Header().Get("Cache-Control") != "no-store" || w.Header().Get("X-Robots-Tag") != "noindex" {
		t.Fatalf("unsafe contact error response: status=%d headers=%v", w.Code, w.Header())
	}
	body := w.Body.String()
	for _, script := range []string{"<script>alert(1)</script>", "<script>alert(2)</script>"} {
		if strings.Contains(body, script) {
			t.Fatalf("contact input became executable markup: %q", script)
		}
	}
	// Confirm the fields were actually preserved, so the test cannot pass merely
	// because the form or submitted values disappeared from the response.
	for _, escaped := range []string{"&lt;script&gt;alert(1)&lt;/script&gt;", "&lt;/textarea&gt;&lt;script&gt;alert(2)&lt;/script&gt;"} {
		if !strings.Contains(body, escaped) {
			t.Fatalf("escaped submitted field missing: %q", escaped)
		}
	}
}

func TestIndependentContactStateDoesNotStoreVisitorContents(t *testing.T) {
	h := newContactHarness(t, func(context.Context, M, string, string) bool { return false })
	post := url.Values{
		"token": {h.token}, "name": {"PRIVATE VISITOR NAME"},
		"email": {"privacy-review@example.test"}, "nachricht": {"PRIVATE VISITOR MESSAGE"},
		"cf-turnstile-response": {"private-verification-token"},
	}
	v, _, _ := h.post(post)
	if v["status"] != 502 {
		t.Fatalf("expected mocked uncertain-send response, got %v", v["status"])
	}
	files := 0
	err := filepath.WalkDir(h.c.config.StateDir, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if entry.IsDir() {
			// The caller supplies the state root; systemd secures it in production.
			// Check directories created by the contact module itself.
			if path != h.c.config.StateDir && info.Mode().Perm()&0077 != 0 {
				t.Errorf("state directory has nonprivate permissions %o", info.Mode().Perm())
			}
			return nil
		}
		files++
		if info.Mode().Perm() != 0600 {
			t.Errorf("state file permissions %o, want0600", info.Mode().Perm())
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		for _, secret := range []string{
			post.Get("name"), post.Get("email"), post.Get("nachricht"), post.Get("cf-turnstile-response"),
			"203.0.113.4", h.c.config.Key, h.c.config.Secret,
		} {
			if secret != "" && strings.Contains(string(data), secret) {
				t.Errorf("visitor contents or credential leaked into persisted state")
			}
		}
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if files < 2 {
		t.Fatalf("expected session and limiter files, found%d", files)
	}
}
