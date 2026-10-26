// Package searchapi exposes the versioned internal HTTP adapter. It logs no queries.
package searchapi

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/url"
	"strconv"

	"jackieleven/internal/search"
)

const VersionHeader = "X-Archive-Content-Version"

type API struct{ Service *search.Service }

func New(s *search.Service) http.Handler { return &API{s} }
func write(w http.ResponseWriter, status int, v any) {
	data, e := json.Marshal(v)
	if e != nil || len(data) > 4<<20 {
		status = 503
		data = []byte(`{"api_version":"v1","error":{"code":"unavailable","message":"Search unavailable"}}`)
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_, _ = w.Write(append(data, '\n'))
}
func failure(w http.ResponseWriter, status int, code, message string) {
	write(w, status, map[string]any{"api_version": "v1", "error": map[string]string{"code": code, "message": message}})
}
func fail(w http.ResponseWriter, e error) {
	switch {
	case errors.Is(e, search.ErrInvalid):
		failure(w, 400, "invalid_query", "Invalid request")
	case errors.Is(e, search.ErrCapacity):
		w.Header().Set("Retry-After", "1")
		failure(w, 429, "capacity", "Search capacity exhausted")
	case errors.Is(e, search.ErrNotFound):
		failure(w, 404, "not_found", "Not found")
	default:
		failure(w, 503, "unavailable", "Search unavailable")
	}
}
func (a *API) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Robots-Tag", "noindex, nofollow")
	w.Header().Set("Referrer-Policy", "no-referrer")
	w.Header().Set(VersionHeader, a.Service.Manifest.ContentVersion)
	if r.Method != "GET" {
		w.Header().Set("Allow", "GET")
		failure(w, 405, "method_not_allowed", "Use GET")
		return
	}
	switch r.URL.Path {
	case "/healthz":
		write(w, 200, map[string]string{"status": "ok"})
		return
	case "/readyz":
		if e := a.Service.Ready(r.Context()); e != nil {
			fail(w, e)
		} else {
			write(w, 200, map[string]string{"status": "ready"})
		}
		return
	case "/v1/search", "/v1/passages", "/v1/entities":
	default:
		failure(w, 404, "not_found", "Not found")
		return
	}
	if r.Header.Get(VersionHeader) != a.Service.Manifest.ContentVersion {
		failure(w, 409, "content_version_mismatch", "Archive content version mismatch")
		return
	}
	if len(r.URL.RawQuery) > 16384 {
		fail(w, search.ErrInvalid)
		return
	}
	params, e := url.ParseQuery(r.URL.RawQuery)
	if e != nil {
		fail(w, search.ErrInvalid)
		return
	}
	for _, values := range params {
		if len(values) != 1 {
			fail(w, search.ErrInvalid)
			return
		}
	}
	switch r.URL.Path {
	case "/v1/search":
		q, e := parseQuery(params)
		if e != nil {
			fail(w, e)
			return
		}
		out, e := a.Service.Search(r.Context(), q)
		if e != nil {
			fail(w, e)
			return
		}
		write(w, 200, out)
	case "/v1/passages":
		if !only(params, "id", "lang") {
			fail(w, search.ErrInvalid)
			return
		}
		lang := params.Get("lang")
		if lang == "" {
			lang = "de"
		}
		out, e := a.Service.Passage(r.Context(), params.Get("id"), lang)
		if e != nil {
			fail(w, e)
			return
		}
		write(w, 200, out)
	case "/v1/entities":
		if !only(params, "id") {
			fail(w, search.ErrInvalid)
			return
		}
		out, e := a.Service.Entity(r.Context(), params.Get("id"))
		if e != nil {
			fail(w, e)
			return
		}
		write(w, 200, out)
	}
}
func only(v url.Values, keys ...string) bool {
	for k := range v {
		found := false
		for _, key := range keys {
			if k == key {
				found = true
			}
		}
		if !found {
			return false
		}
	}
	return true
}
func parseQuery(v url.Values) (search.Query, error) {
	q := search.Query{Text: v.Get("q"), Language: v.Get("lang"), Mode: v.Get("mode"), Voice: v.Get("voice"), Limit: 20}
	if !only(v, "q", "lang", "mode", "voice", "limit", "from", "to", "rerank") {
		return q, search.ErrInvalid
	}
	if q.Language == "" {
		q.Language = "de"
	}
	if q.Mode == "" {
		q.Mode = "hybrid"
	}
	var e error
	if v.Has("limit") {
		q.Limit, e = strconv.Atoi(v.Get("limit"))
		if e != nil {
			return q, search.ErrInvalid
		}
	}
	for k, dst := range map[string]**int{"from": &q.From, "to": &q.To} {
		if v.Has(k) {
			n, err := strconv.Atoi(v.Get(k))
			if err != nil {
				return q, search.ErrInvalid
			}
			*dst = &n
		}
	}
	switch v.Get("rerank") {
	case "", "0":
	case "1":
		q.Rerank = true
	default:
		return q, search.ErrInvalid
	}
	return q, q.Validate()
}
