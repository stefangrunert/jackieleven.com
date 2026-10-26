package searchclient

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

const testManifestJSON = `{"api_version":"v1","build_id":"build-a","content_version":"content-a","data_version":"data-a","embedding_profile":"none","passage_count":2,"document_count":1}`
const searchJSON = `{"api_version":"v1","content_version":"content-a","data_version":"data-a","search_release":"search-v1","mode":"lexical","degraded":true,"reason":"embedding_off","reranked":false,"duration_ms":1.25,"hits":[{"id":"document#p1","document_id":"document","title":"Title","text":"Exact stored excerpt","language":"en","source_voice":"third_party","text_voice":"editorial","text_kind":"summary","url":"/en/voices/document","score":0.8}]}`

func manifestFile(t *testing.T) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), "manifest.json")
	if err := os.WriteFile(p, []byte(testManifestJSON), 0600); err != nil {
		t.Fatal(err)
	}
	return p
}
func clientFor(t *testing.T, h http.HandlerFunc) *Client {
	t.Helper()
	s := httptest.NewServer(h)
	t.Cleanup(s.Close)
	c, err := New(s.URL, manifestFile(t))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(c.http.CloseIdleConnections)
	return c
}
func assertStatus(t *testing.T, err error, status int) {
	t.Helper()
	var api *Error
	if !errors.As(err, &api) || api.Status != status {
		t.Fatalf("error %v, want status %d", err, status)
	}
}

func TestSearchPinnedContract(t *testing.T) {
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/search" || r.Header.Get("X-Archive-Content-Version") != "content-a" {
			t.Errorf("wrong API path or version")
		}
		q := r.URL.Query()
		for key, want := range map[string]string{"q": "Doll by Doll", "lang": "en", "mode": "hybrid", "voice": "editorial", "from": "1990", "to": "2001", "rerank": "1", "limit": "20"} {
			if q.Get(key) != want {
				t.Errorf("%s = %s", key, q.Get(key))
			}
		}
		if q.Has("build_id") {
			t.Error("untrusted build forwarded")
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(searchJSON))
	})
	result, err := c.Search(context.Background(), url.Values{"q": {"Doll by Doll"}, "lang": {"en"}, "mode": {"hybrid"}, "voice": {"editorial"}, "from": {"1990"}, "to": {"2001"}, "rerank": {"1"}, "build_id": {"other"}, "limit": {"50"}})
	if err != nil {
		t.Fatal(err)
	}
	if result.Mode != "lexical" || !result.Degraded || result.Reason != "embedding_off" || result.DurationMS != 1.25 || result.Hits[0].TextVoice != "editorial" {
		t.Fatalf("lost contract fields: %+v", result)
	}
}
func TestPassageContract(t *testing.T) {
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/passages" || r.URL.Query().Get("id") != "document#p1" || r.URL.Query().Get("lang") != "de" {
			t.Error("wrong passage query")
		}
		_, _ = w.Write([]byte(`{"api_version":"v1","content_version":"content-a","data_version":"data-a","search_release":"search-v1","passage":{"id":"document#p1","document_id":"document","text":"Full text\n\nSecond paragraph","metadata":{"year":1999}}}`))
	})
	got, err := c.Passage(context.Background(), "document#p1", "de")
	if err != nil {
		t.Fatal(err)
	}
	if got.Passage.Text != "Full text\n\nSecond paragraph" {
		t.Fatal("passage changed")
	}
}
func TestFailuresAreBoundedAndDoNotExposeQueries(t *testing.T) {
	for _, tc := range []struct {
		name   string
		status int
		body   string
		want   int
	}{
		{"invalid", 400, `PRIVATE_QUERY`, 400}, {"missing", 404, `PRIVATE_QUERY`, 404}, {"mismatch", 409, `PRIVATE_QUERY`, 409}, {"busy", 429, `PRIVATE_QUERY`, 429}, {"database", 503, `PRIVATE_QUERY`, 503}, {"unexpected", 500, `PRIVATE_QUERY`, 503},
		{"invalid JSON", 200, "broken PRIVATE_QUERY", 503}, {"oversize", 200, strings.Repeat("x", maxResponseBytes+1), 503},
		{"wrong content", 200, strings.ReplaceAll(searchJSON, "content-a", "content-b"), 409}, {"wrong data", 200, strings.ReplaceAll(searchJSON, "data-a", "data-b"), 409},
		{"wrong API", 200, strings.ReplaceAll(searchJSON, `"v1"`, `"v2"`), 503}, {"null hits", 200, `{"api_version":"v1","content_version":"content-a","data_version":"data-a","search_release":"v1","mode":"lexical","hits":null}`, 503},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tc.status)
				_, _ = w.Write([]byte(tc.body))
			})
			_, err := c.Search(context.Background(), url.Values{"q": {"PRIVATE_QUERY"}})
			assertStatus(t, err, tc.want)
			if strings.Contains(err.Error(), "PRIVATE_QUERY") {
				t.Fatal("query exposed")
			}
		})
	}
}
func TestLoopbackOnlyAndNoRedirect(t *testing.T) {
	p := manifestFile(t)
	for _, endpoint := range []string{"https://127.0.0.1:8081", "http://example.com", "http://192.168.1.1", "http://127.0.0.1:8081/v1", "http://127.0.0.1:8081?key=secret", "http://user@127.0.0.1:8081", "http://127.0.0.1#fragment", "http://127.0.0.1:bad"} {
		if _, err := New(endpoint, p); err == nil {
			t.Errorf("accepted endpoint %s", endpoint)
		}
	}
	called := false
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { called = true }))
	defer target.Close()
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Location", target.URL)
		w.WriteHeader(302)
	})
	_, err := c.Search(context.Background(), url.Values{"q": {"example"}})
	assertStatus(t, err, 503)
	if called {
		t.Fatal("followed redirect")
	}
}
func TestCancellationAndOffline(t *testing.T) {
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) { <-r.Context().Done() })
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	start := time.Now()
	_, err := c.Search(ctx, url.Values{"q": {"example"}})
	assertStatus(t, err, 503)
	if time.Since(start) > time.Second {
		t.Fatal("cancellation was not honored")
	}
	offline := httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {}))
	offline.Close()
	c, err = New(offline.URL, manifestFile(t))
	if err != nil {
		t.Fatal(err)
	}
	_, err = c.Search(context.Background(), url.Values{"q": {"example"}})
	assertStatus(t, err, 503)
}
func TestManifestIsPinnedAndValidated(t *testing.T) {
	p := manifestFile(t)
	c, err := New("http://localhost:8081", p)
	if err != nil {
		t.Fatal(err)
	}
	changed := strings.ReplaceAll(testManifestJSON, "content-a", "content-b")
	if err := os.WriteFile(p, []byte(changed), 0600); err != nil {
		t.Fatal(err)
	}
	if c.Manifest().ContentVersion != "content-a" {
		t.Fatal("manifest changed after startup")
	}
	for _, body := range []string{"{}", strings.ReplaceAll(testManifestJSON, `"v1"`, `"v2"`), testManifestJSON + "{}", strings.Repeat("x", (64<<10)+1)} {
		if err := os.WriteFile(p, []byte(body), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err := New("http://127.0.0.1:8081", p); err == nil {
			t.Fatal("accepted invalid manifest")
		}
	}
}
func TestEmptyResultsAndUnknownFields(t *testing.T) {
	var body map[string]any
	if err := json.Unmarshal([]byte(searchJSON), &body); err != nil {
		t.Fatal(err)
	}
	body["hits"] = []any{}
	body["future_field"] = "fine"
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) { _ = json.NewEncoder(w).Encode(body) })
	got, err := c.Search(context.Background(), url.Values{"q": {"nomatch"}})
	if err != nil || len(got.Hits) != 0 {
		t.Fatalf("empty response: %v %v", got, err)
	}
}

func TestPassageCannotSubstituteAnotherID(t *testing.T) {
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"api_version":"v1","content_version":"content-a","data_version":"data-a","search_release":"v1","passage":{"id":"another#passage","document_id":"another","text":"wrong passage"}}`))
	})
	_, err := c.Passage(context.Background(), "document#p1", "en")
	assertStatus(t, err, 503)
}

func TestEntityPinnedAndIdentityChecked(t *testing.T) {
	wrong := false
	c := clientFor(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/entities" || r.URL.Query().Get("id") != "event/one" || r.Header.Get("X-Archive-Content-Version") != "content-a" {
			t.Error("wrong entity request")
		}
		id := "event/one"
		if wrong {
			id = "event/two"
		}
		_ = json.NewEncoder(w).Encode(EntityResponse{Versions: Versions{APIVersion: "v1", ContentVersion: "content-a", DataVersion: "data-a", SearchRelease: "v1"}, Entity: json.RawMessage(`{"id":"` + id + `","label":"Event"}`)})
	})
	if _, err := c.Entity(context.Background(), "event/one"); err != nil {
		t.Fatal(err)
	}
	wrong = true
	_, err := c.Entity(context.Background(), "event/one")
	assertStatus(t, err, 503)
}
