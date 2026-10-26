package searchapi

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"jackieleven/internal/search"
)

type repo struct{ fail error }

func (r repo) Ready(context.Context, search.Manifest) error { return r.fail }
func (r repo) Lexical(context.Context, search.Manifest, search.Query, int) ([]search.Hit, error) {
	return []search.Hit{}, r.fail
}
func (r repo) Semantic(context.Context, search.Manifest, search.Query, []float32, int) ([]search.Hit, error) {
	return nil, r.fail
}
func (r repo) Passage(context.Context, search.Manifest, string, string) (search.Hit, error) {
	return search.Hit{}, search.ErrNotFound
}
func (r repo) Entity(context.Context, search.Manifest, string) (json.RawMessage, error) {
	return nil, search.ErrNotFound
}
func handler(fail error) http.Handler {
	m := search.Manifest{APIVersion: "v1", BuildID: "b", ContentVersion: "content", DataVersion: "data", EmbeddingProfile: "none"}
	s, _ := search.New(m, repo{fail}, nil, search.DefaultOptions())
	return New(s)
}
func TestHTTPContract(t *testing.T) {
	for _, tc := range []struct {
		url, version string
		status       int
		body         string
	}{
		{"/healthz", "", 200, "ok"}, {"/readyz", "", 200, "ready"},
		{"/v1/search?q=Jackie", "", 409, "content_version_mismatch"},
		{"/v1/search?q=Jackie", "wrong", 409, "content_version_mismatch"},
		{"/v1/search?q=Jackie", "content", 200, `"hits":[]`},
		{"/v1/search?q=Jackie&section=music&grouped=1", "content", 200, `"hits":[]`},
		{"/v1/search?q=Jackie&section=unknown", "content", 400, "invalid_query"},
		{"/v1/search?q=Jackie&grouped=2", "content", 400, "invalid_query"},
		{"/v1/search?q=Jackie&limit=51", "content", 400, "invalid_query"},
		{"/v1/search?q=Jackie&mode=invalid", "content", 400, "invalid_query"},
		{"/v1/search?q=Jackie&q=Other", "content", 400, "invalid_query"},
		{"/v1/search?q=Jackie&from=2001&to=1990", "content", 400, "invalid_query"},
		{"/v1/passages?id=missing", "content", 404, "not_found"},
		{"/v1/entities?id=missing", "content", 404, "not_found"},
	} {
		r := httptest.NewRequest("GET", tc.url, nil)
		r.Header.Set(VersionHeader, tc.version)
		w := httptest.NewRecorder()
		handler(nil).ServeHTTP(w, r)
		if w.Code != tc.status || !strings.Contains(w.Body.String(), tc.body) {
			t.Errorf("%s: status=%d body=%s", tc.url, w.Code, w.Body.String())
		}
		if w.Header().Get("Cache-Control") != "no-store" {
			t.Fatal("cache")
		}
	}
}
func TestHTTPFailureNoPrivateDetails(t *testing.T) {
	r := httptest.NewRequest("GET", "/v1/search?q=privatequery", nil)
	r.Header.Set(VersionHeader, "content")
	w := httptest.NewRecorder()
	handler(search.ErrUnavailable).ServeHTTP(w, r)
	if w.Code != 503 || strings.Contains(w.Body.String(), "privatequery") {
		t.Fatal(w.Code, w.Body.String())
	}
}
